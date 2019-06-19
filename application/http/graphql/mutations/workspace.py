import graphene, datetime, logging
from application.auth.models import User as _UserModel
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error, check_role_or_error
from graphql import GraphQLError
from application.shared.database import Persistent
from application.workspace.models import (
    WorkspaceModel,
    WorkspaceUser,
    WorkspaceInvitation,
    WorkspaceInvitationStatus,
    WorkspaceDate,
    WorkspaceUserRole,
    WorkspaceUserRoles,
    WorkspaceRule
)

LOG = logging.getLogger("[mutations]")


class CreateWorkspace(graphene.Mutation):
    class Arguments:
        name = graphene.String()
        description = graphene.String()
        members = graphene.List(of_type=graphene.String)

    ok = graphene.Boolean()
    ws = graphene.Field(lambda: types.Workspace)

    @gql_jwt_required
    def mutate(self, _, name, description, members):
        now = datetime.datetime.now()
        user = current_user_or_error()

        try:
            new_ws = WorkspaceModel(name=name, description=description)
            new_ws.save()
            Persistent.flush()  # so we now have ID for new_ws

            WorkspaceUser(ws_id=new_ws.id, user_id=user.id, start_date=now).save()

            for role in WorkspaceUserRoles.__members__:
                WorkspaceUserRole(ws_id=new_ws.id, user_id=user.id, role=role).save()

            for email in members:
                if email.strip() == user.email:
                    continue
                wsi = WorkspaceInvitation(email=email, ws_id=new_ws.id)
                # check if user with this email already exist
                user_by_email = _UserModel.find_by_email(email=email)

                if user_by_email:
                    WorkspaceUser(
                        ws_id=new_ws.id,
                        user_id=user_by_email.id,
                        start_date=now
                    ).save()

                    WorkspaceUserRole(
                        ws_id=new_ws.id,
                        user_id=user_by_email.id,
                        role=WorkspaceUserRoles.MEMBER
                    ).save()

                    wsi.status = WorkspaceInvitationStatus.ACCEPTED

                wsi.save()

            Persistent.commit()

            return CreateWorkspace(ok=True, ws=new_ws)
        except Exception as e:
            LOG.error(f'Workspace creation failed. Error: {e}')
            Persistent.rollback()
            raise GraphQLError('Workspace creation failed.')

class UpdateWorkspace(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        name = graphene.String()
        description = graphene.String()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, ws_id, name, description):
        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)
        ws = WorkspaceModel.find_by_id(ws_id)
        if ws is None:
            raise GraphQLError('Workspace not found.')
        try:
            if name is not None:
                ws.name = name
            if description is not None:
                ws.description = description
            ws.save_and_persist()
            return UpdateWorkspace(ok=True)
        except Exception as e:
            LOG.error(f'Workspace update failed. Error: {e}')
            Persistent.rollback()
            raise GraphQLError('Workspace update failed.')

class AddMember(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        start_date = graphene.Date()
        ws_id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, email, ws_id, start_date=None):
        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        start_date = start_date if start_date else datetime.datetime.utcnow()

        try:
            user = _UserModel.find(email=email)
            if user is None:
                if WorkspaceInvitation.find(email=email, ws_id=ws_id) is None:
                    WorkspaceInvitation(email=email, ws_id=ws_id, start_date=start_date,
                                        status=WorkspaceInvitationStatus.PENDING).save()
            elif WorkspaceUser.find(user_id=user.id, ws_id=ws_id) is None:
                WorkspaceInvitation(email=email, ws_id=ws_id, start_date=start_date,
                                    status=WorkspaceInvitationStatus.ACCEPTED).save()

                WorkspaceUser(user_id=user.id, ws_id=ws_id, start_date=start_date).save()

            Persistent.commit()

            return AddMember(ok=True)
        except Exception as e:
            LOG.error(f'Could not add member into workspace. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not add member into workspace.')


class UpdateMember(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        user_id = graphene.Int()
        start_date = graphene.Date()

    ok = graphene.Boolean()
    member = graphene.Field(lambda: types.WorkspaceUser)

    @gql_jwt_required
    def mutate(self, _, ws_id, user_id, start_date):

        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        ws_user = WorkspaceUser.find(ws_id=ws_id, user_id=user_id)

        if not ws_user:
            raise GraphQLError("Could not find user in the workspace")

        ws_user.start_date = start_date

        try:
            ws_user.save_and_persist()
            return UpdateMember(ok=True, member=ws_user)
        except Exception as e:
            LOG.error(f'Could not update the workspace member. Error: {e}')
            return GraphQLError('Could not update the workspace member.')


class RemoveMember(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        ws_id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, email, ws_id):
        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        try:
            invitation = WorkspaceInvitation.find(ws_id=ws_id, email=email)
            if invitation:
                invitation.delete()

            ws_user = None

            user = _UserModel.find(email=email)
            if user:
                ws_user = WorkspaceUser.find(ws_id=ws_id, user_id=user.id)

            if ws_user:
                ws_user.delete()

            Persistent.commit()
            return RemoveMember(ok=True)
        except Exception as e:
            LOG.error(f'Could not remove member from workspace.. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not remove member from workspace.')


class AddUserRole(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        user_id = graphene.Int()
        role = graphene.String()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, ws_id, user_id, role):
        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        if WorkspaceUserRole.find(ws_id=ws_id, user_id=user_id, role=role):
            return AddUserRole(ok=True)

        try:
            WorkspaceUserRole(ws_id=ws_id, user_id=user_id, role=role).save_and_persist()
            return AddUserRole(ok=True)
        except Exception as e:
            raise GraphQLError('Could not add a user role.')


class RemoveUserRole(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        user_id = graphene.Int()
        role = graphene.String()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, ws_id, user_id, role):
        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        user_role = WorkspaceUserRole.find(ws_id=ws_id, user_id=user_id, role=role)

        if not user_role:
            return RemoveUserRole(ok=True)

        try:
            user_role.delete_and_persist()
            return RemoveUserRole(ok=True)
        except Exception as e:
            raise GraphQLError('Could not remove a user role.')


class AddWorkspaceDate(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        date = graphene.Date()
        name = graphene.String()
        is_official_holiday = graphene.Boolean()

    ok = graphene.Boolean()
    workspace_date = graphene.Field(lambda: types.WorkspaceDate)

    @gql_jwt_required
    def mutate(self, _, ws_id, date, name, is_official_holiday):

        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        try:
            workspace_date = WorkspaceDate(name=name, ws_id=ws_id, date=date, is_official_holiday=is_official_holiday)
            workspace_date.save_and_persist()
            return AddWorkspaceDate(ok=True, workspace_date=workspace_date)
        except Exception as e:
            raise GraphQLError('Could not add a holiday.')


class RemoveWorkspaceDate(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, id):
        holiday = WorkspaceDate.find(id=id)

        if holiday is None:
            raise GraphQLError('Could not find holiday.')

        check_role_or_error(ws_id=holiday.ws_id, role=WorkspaceUserRoles.ADMIN)

        try:
            holiday.delete_and_persist()

            return RemoveWorkspaceDate(ok=True)
        except Exception as e:
            raise GraphQLError('Could not remove a holiday.')


class SetWorkspaceRule(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        type = graphene.String()
        rule = graphene.String()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, ws_id, type, rule):
        check_role_or_error(ws_id=ws_id, role=WorkspaceUserRoles.ADMIN)

        try:
            WorkspaceRule(ws_id=ws_id, type=type, rule=rule).merge_and_persist()
            return SetWorkspaceRule(ok=True)
        except Exception as e:
            raise GraphQLError('Could not create a rule.')
