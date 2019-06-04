import graphene
from application.auth.models import User as _UserModel

from application.workspace.models import (WorkspaceModel,
                                          WorkspaceUserModel,
                                          WorkspaceInvitation,
                                          WorkspaceInvitationStatus,
                                          WorkspaceUserRelationTypes
                                          )
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error
from graphql import GraphQLError
from application.shared.database import Persistent
import datetime
import logging

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


class AddMember(graphene.Mutation):
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
            return AddMember(ok=True)
        except Exception as e:
            LOG.error(f'Could not add member into workspace. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not add member into workspace.')


class RemoveMember(graphene.Mutation):
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
            return RemoveMember(ok=True)
        except Exception as e:
            LOG.error(f'Could not remove member from workspace.. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not remove member from workspace.')
