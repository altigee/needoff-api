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
from application.workspace.models import WorkspaceModel, WorkspaceUserModel
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error
from graphql import GraphQLError
import datetime
import logging
from application.workspace.models import *

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
        new_user = _UserModel(
            email=email,
            password=_UserModel.generate_hash(password),
            jti=decode_token(refresh_token)['jti'],
            created_time=datetime.datetime.now()
        )
        try:
            new_user.save_and_persist()
        except Exception as e:
            LOG.error(f"User registration failed. Error: {e}")
            new_user.rollback()
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
                wsi = WorkspaceInvitation(email=email, ws_id=new_ws.id)
                wsi.save_and_persist()
            return CreateWorkspace(ok=True, ws=new_ws)
        except Exception as e:
            LOG.error(f'Workspace creation failed. Error: {e}')
            Persistent.rollback()
            raise GraphQLError('Workspace creation failed.')
