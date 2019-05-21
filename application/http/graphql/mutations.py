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
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required
from graphql import GraphQLError
import datetime
import logging
from application.workspace.models import *

LOG = logging.getLogger("[mutations]")


def to_date(date_time_str):
    return datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')


class RegisterUserResponse(graphene.ObjectType):
    id = graphene.Int()
    email = graphene.String()


class RegisterUser(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        password = graphene.String()

    ok = graphene.Boolean()
    response = graphene.Field(RegisterUserResponse)

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

        return RegisterUser(ok=True, response=RegisterUserResponse(id=new_user.id, email=new_user.email))


class CreateDayOff(graphene.Mutation):
    class Arguments:
        leave_type = graphene.String()
        start_date = graphene.String()
        end_date = graphene.String()
        workspace_id = graphene.Int()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    @gql_jwt_required
    def mutate(self, _, leave_type, start_date, end_date, workspace_id):
        user = _UserModel.find_by_email(get_jwt_identity())
        if not user:
            raise GraphQLError('User not found')
        if not is_valid_leave_type(leave_type):
            raise GraphQLError('Invalid leave type')
        day_off = DayOff(
            leave_type=leave_type,
            start_date=to_date(start_date),
            end_date=to_date(end_date),
            workspace_id=workspace_id,
            user_id=user.id)
        day_off.save_and_persist()
        return CreateDayOff(day_off=day_off, ok=True)
