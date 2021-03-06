import graphene, datetime, logging
from application.auth.models import User as _UserModel
from application.users.models import UserProfile, UserDevice
from graphql import GraphQLError
from application.shared.database import db, Persistent

from application.http.graphql.util import (
    gql_jwt_required,
    current_user_or_error
)
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    decode_token
)
from application.workspace.models import (
    WorkspaceUser,
    WorkspaceInvitation,
    WorkspaceInvitationStatus,
    WorkspaceUserRole,
    WorkspaceUserRoles,
)

LOG = logging.getLogger("[mutations]")


class SaveUserDevice(graphene.Mutation):
    class Arguments:
        token = graphene.String()

    user_id = graphene.Int()
    token = graphene.String()

    @gql_jwt_required
    def mutate(self, _, token):
        try:
            user = current_user_or_error()
            if user is not None and token is not None:
                UserDevice.query().filter_by(device_token=token).delete()
                ud = UserDevice(user_id=user.id, device_token=token)
                ud.save_and_persist()
                return SaveUserDevice(user_id=ud.user_id, token=ud.device_token)
        except Exception as e:
            print(e)
            raise GraphQLError('Failed to save device token')


class RemoveUserDevice(graphene.Mutation):
    class Arguments:
        token = graphene.String()

    user_id = graphene.Int()
    token = graphene.String()

    @gql_jwt_required
    def mutate(self, _, token):
        try:
            user = current_user_or_error()
            if user is not None and token is not None:
                UserDevice.find(device_token=token).delete_and_persist()
                return RemoveUserDevice(user_id=user.id, token=token)
        except Exception as e:
            raise GraphQLError('Failed to delete device token')


class Login(graphene.Mutation):
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
            raise GraphQLError('Wrong credentials')

        if not _UserModel.verify_hash(password, current_user.password):
            LOG.warning(f'Wrong credentials for user {email}')
            raise GraphQLError('Wrong credentials')

        access_token = create_access_token(current_user.email)
        refresh_token = create_refresh_token(current_user.email)
        current_user.jti = decode_token(refresh_token)['jti']
        current_user.save_and_persist()

        return Login(ok=True, access_token=access_token, refresh_token=refresh_token)


class UserData(graphene.InputObjectType):
    first_name = graphene.String()
    last_name = graphene.String()


class Register(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        password = graphene.String()
        user_data = UserData()

    ok = graphene.Boolean()
    user_id = graphene.Int()
    access_token = graphene.String()
    refresh_token = graphene.String()

    def mutate(self, _, email, password, user_data):
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
                email=email.strip(),
                first_name=user_data.first_name.strip(),
                last_name=user_data.last_name.strip()
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
                        WorkspaceUser(user_id=new_user.id,
                                      ws_id=inv.ws_id,
                                      start_date=inv.start_date
                                      ).save()

                        WorkspaceUserRole(ws_id=inv.ws_id,
                                          user_id=new_user.id,
                                          role=WorkspaceUserRoles.MEMBER
                                          ).save()

                    inv.status = WorkspaceInvitationStatus.ACCEPTED
                    WorkspaceInvitation.query() \
                        .filter(WorkspaceInvitation.id == inv.id) \
                        .update({WorkspaceInvitation.status: inv.status})

                Persistent.commit()
            except Exception as e:
                LOG.error(f"Workspace invitations check failed for user {new_user.email}. Error: {e}")
                db.session.rollback()

        return Register(ok=True,
                        user_id=new_user.id,
                        access_token=access_token,
                        refresh_token=refresh_token)
