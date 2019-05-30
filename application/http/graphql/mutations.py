import graphene
from application.balances.models import DayOff, is_valid_leave_type
from application.auth.models import User as _UserModel
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt,
    decode_token
)
from application.workspace.models import (WorkspaceModel,
                                          WorkspaceUserModel,
                                          WorkspaceInvitation,
                                          WorkspaceInvitationStatus,
                                          WorkspaceUserRelationTypes,
                                          WorkspaceHolidayCalendar,
                                          Holiday)
from application.users.models import UserProfile
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error
from graphql import GraphQLError
from application.shared.database import db, Persistent
import datetime
import logging

LOG = logging.getLogger("[mutations]")


def to_date(date_time_str):
    return datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')


class LoginUser(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()
    access_token = graphene.String()
    refresh_token = graphene.String()

    def mutate(self, _, email, password):
        current_user = _UserModel.find_by_email(email)
        if not current_user:
            LOG.warning(f'Non-existing user {email} login')
            raise GraphQLError('Wrong cedentials')

        if _UserModel.verify_hash(password, current_user.password):
            access_token = create_access_token(current_user.email)
            refresh_token = create_refresh_token(current_user.email)
            current_user.jti = decode_token(refresh_token)['jti']
            current_user.save_and_persist()
            return LoginUser(ok=True,
                             access_token=access_token,
                             refresh_token=refresh_token)
        else:
            LOG.warning(f'Wrong credentials for user {email}')
            raise GraphQLError('Wrong credentials')


class RegisterUser(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()
    user_id = graphene.Int()
    access_token = graphene.String()
    refresh_token = graphene.String()

    def mutate(self, _, email, password):
        if _UserModel.find_by_email(email):
            LOG.warning(f'Repeated registration for {email}')
            raise GraphQLError(f'User {email} already exists')

        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        try:
            new_user = _UserModel(
                email=email.strip(),
                password=_UserModel.generate_hash(password),
                jti=decode_token(refresh_token)['jti'],
                created_time=datetime.datetime.now()
            )

            new_user.save()
            Persistent.flush()
            new_user_profile = UserProfile(
                user_id=new_user.id,
                email=email.strip()
            )
            new_user_profile.save_and_persist()
        except Exception as e:
            LOG.error(f"User registration failed. Error: {e}")
            Persistent.rollback()
            raise GraphQLError("User registration failed.")
        else:
            # check ws invitatitons
            try:
                pending_invitations = WorkspaceInvitation.find_all(email=email,
                                                                   status=WorkspaceInvitationStatus.PENDING)
                processed_ws_ids = set()
                for inv in pending_invitations:
                    if inv.ws_id not in processed_ws_ids:
                        processed_ws_ids.add(inv.ws_id)
                        db.session.add(WorkspaceUserModel(user_id=new_user.id,
                                                          ws_id=inv.ws_id,
                                                          start_date=datetime.datetime.now()))
                    inv.status = WorkspaceInvitationStatus.ACCEPTED
                    db.session.query(WorkspaceInvitation) \
                        .filter(WorkspaceInvitation.id == inv.id) \
                        .update({WorkspaceInvitation.status: inv.status})
                db.session.commit()
            except Exception as e:
                LOG.error(f"Workspace invitations check failed for user {new_user.email}. Error: {e}")
                db.session.rollback()

        return RegisterUser(ok=True,
                            user_id=new_user.id,
                            access_token=access_token,
                            refresh_token=refresh_token)


class CreateDayOff(graphene.Mutation):
    class Arguments:
        type = graphene.String()
        start_date = graphene.String()
        end_date = graphene.String()
        workspace_id = graphene.Int()
        comment = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    @gql_jwt_required
    def mutate(self, _, type, start_date, end_date, workspace_id, comment):
        user = current_user_or_error()
        if not is_valid_leave_type(type):
            raise GraphQLError('Invalid leave type')
        day_off = DayOff(
            leave_type=type,
            start_date=to_date(start_date),
            end_date=to_date(end_date),
            workspace_id=workspace_id,
            comment=comment,
            user_id=user.id)
        day_off.save_and_persist()
        return CreateDayOff(day_off=day_off, ok=True)


class CreateWorkspace(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        description = graphene.String()
        members = graphene.List(of_type=graphene.String)

    ok = graphene.Boolean()
    ws = graphene.Field(lambda: types.Workspace)

    @gql_jwt_required
    def mutate(self, _, name, description, members):
        user = current_user_or_error()
        try:
            new_ws = WorkspaceModel(name=name, description=description)
            new_ws.save()
            Persistent.flush()  # so we now have ID for new_ws
            new_relation = WorkspaceUserModel(ws_id=new_ws.id,
                                              user_id=user.id,
                                              relation_type=WorkspaceUserRelationTypes.OWNER)
            new_relation.save_and_persist()
            for email in members:
                if email.strip() == user.email:
                    continue
                wsi = WorkspaceInvitation(email=email, ws_id=new_ws.id)
                # check if user with this email already exist
                user_by_email = _UserModel.find_by_email(email=email)
                if user_by_email:
                    member_relation = WorkspaceUserModel(ws_id=new_ws.id,
                                                         user_id=user_by_email.id,
                                                         relation_type=WorkspaceUserRelationTypes.MEMBER)
                    member_relation.save()
                    wsi.status = WorkspaceInvitationStatus.ACCEPTED
                wsi.save_and_persist()
            return CreateWorkspace(ok=True, ws=new_ws)
        except Exception as e:
            LOG.error(f'Workspace creation failed. Error: {e}')
            Persistent.rollback()
            raise GraphQLError('Workspace creation failed.')


class AddWorkspaceMember(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        start_date = graphene.Date()
        ws_id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, email, ws_id, start_date=None):
        current_user = current_user_or_error()

        # TODO: Make it a shared function
        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=ws_id, relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        start_date = start_date if start_date else datetime.datetime.utcnow()

        try:
            user = _UserModel.find(email=email)
            if user is None:
                if WorkspaceInvitation.find(email=email, ws_id=ws_id) is None:
                    WorkspaceInvitation(email=email, ws_id=ws_id, start_date=start_date,
                                        status=WorkspaceInvitationStatus.PENDING).save_and_persist()
            elif WorkspaceUserModel.find(user_id=user.id, ws_id=ws_id) is None:
                WorkspaceUserModel(user_id=user.id, ws_id=ws_id, start_date=start_date).save_and_persist()
            return AddWorkspaceMember(ok=True)
        except Exception as e:
            LOG.error(f'Could not add member into workspace. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not add member into workspace.')


class RemoveWorkspaceMember(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        ws_id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, email, ws_id):
        current_user = current_user_or_error()

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=ws_id, relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            invitation = WorkspaceInvitation.find(ws_id=ws_id, email=email)
            if invitation:
                invitation.delete()

            ws_user = None

            user = _UserModel.find(email=email)
            if user:
                ws_user = WorkspaceUserModel.find(ws_id=ws_id, user_id=user.id)

            if ws_user:
                ws_user.delete()

            Persistent.commit()
            return RemoveWorkspaceMember(ok=True)
        except Exception as e:
            LOG.error(f'Could not remove member from workspace.. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not remove member from workspace.')


class CreateWorkspaceCalendar(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        ws_id = graphene.Int()

    ok = graphene.Boolean()
    calendar = graphene.Field(lambda: types.WorkspaceHolidayCalendar)

    @gql_jwt_required
    def mutate(self, _, name, ws_id):
        current_user = current_user_or_error()

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=ws_id, relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            calendar = WorkspaceHolidayCalendar(name=name,ws_id=ws_id)
            calendar.save_and_persist()

            return CreateWorkspaceCalendar(ok=True, calendar=calendar)
        except Exception as e:
            LOG.error(f'Calendar creation failed. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not create calendar.')


class RemoveWorkspaceCalendar(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, id):
        current_user = current_user_or_error()

        calendar = WorkspaceHolidayCalendar.find(id=id)

        if calendar is None:
            raise GraphQLError('Could not find a calendar.')

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=calendar.ws_id, relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            calendar.delete_and_persist()

            return CreateWorkspaceCalendar(ok=True)
        except Exception as e:
            LOG.error(f'Could not remove calendar. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not remove calendar.')


class AddHoliday(graphene.Mutation):
    class Arguments:
        calendar_id = graphene.Int()
        date = graphene.Date()
        name = graphene.String()

    ok = graphene.Boolean()
    holiday = graphene.Field(lambda: types.Holiday)

    @gql_jwt_required
    def mutate(self, _, calendar_id, date, name):
        current_user = current_user_or_error()

        calendar = WorkspaceHolidayCalendar.find(id=calendar_id)

        if calendar is None:
            raise GraphQLError('Could not find calendar.')

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=calendar.ws_id, relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            holiday = Holiday(name=name, calendar_id=calendar_id,date=date)
            holiday.save_and_persist()
            return AddHoliday(ok=True, holiday=holiday)
        except Exception as e:
            raise GraphQLError('Could not add a holiday.')


class RemoveHoliday(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, id):
        current_user = current_user_or_error()

        holiday = Holiday.find(id=id)

        if holiday is None:
            raise GraphQLError('Could not find holiday.')

        calendar = WorkspaceHolidayCalendar.find(id=holiday.calendar_id)

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=calendar.ws_id,
                                   relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            holiday.delete_and_persist()

            return RemoveHoliday(ok=True)
        except Exception as e:
            raise GraphQLError('Could not remove a holiday.')
