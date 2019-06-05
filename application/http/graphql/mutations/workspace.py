import graphene, datetime, logging
from application.auth.models import User as _UserModel
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error, current_user_in_workspace_or_error
from graphql import GraphQLError
from application.shared.database import Persistent
from application.workspace.models import (
    WorkspaceModel,
    WorkspaceUser,
    WorkspaceInvitation,
    WorkspaceInvitationStatus,
    WorkspaceUserRelationTypes,
    WorkspacePolicy,
    WorkspaceHoliday
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
        user = current_user_or_error()
        try:
            new_ws = WorkspaceModel(name=name, description=description)
            new_ws.save()
            Persistent.flush()  # so we now have ID for new_ws
            new_relation = WorkspaceUser(ws_id=new_ws.id,
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
                    member_relation = WorkspaceUser(ws_id=new_ws.id,
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


class SetPolicy(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        max_paid_vacations_per_year = graphene.Int()
        max_unpaid_vacations_per_year = graphene.Int()
        max_sick_leaves_per_year = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, ws_id, max_paid_vacations_per_year, max_unpaid_vacations_per_year, max_sick_leaves_per_year):
        current_user_in_workspace_or_error(ws_id=ws_id, relation=WorkspaceUserRelationTypes.OWNER)

        try:
            policy = WorkspacePolicy(ws_id=ws_id,
                                     max_paid_vacations_per_year=max_paid_vacations_per_year,
                                     max_unpaid_vacations_per_year=max_unpaid_vacations_per_year,
                                     max_sick_leaves_per_year=max_sick_leaves_per_year
                                     )
            policy.save_and_persist()

            return SetPolicy(ok=True)

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
        current_user_in_workspace_or_error(ws_id=ws_id, relation=WorkspaceUserRelationTypes.OWNER)

        start_date = start_date if start_date else datetime.datetime.utcnow()

        try:
            user = _UserModel.find(email=email)
            if user is None:
                if WorkspaceInvitation.find(email=email, ws_id=ws_id) is None:
                    WorkspaceInvitation(email=email, ws_id=ws_id, start_date=start_date,
                                        status=WorkspaceInvitationStatus.PENDING).save_and_persist()
            elif WorkspaceUser.find(user_id=user.id, ws_id=ws_id) is None:
                WorkspaceInvitation(email=email, ws_id=ws_id, start_date=start_date,
                                    status=WorkspaceInvitationStatus.ACCEPTED).save()
                WorkspaceUser(user_id=user.id, ws_id=ws_id, start_date=start_date).save_and_persist()
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

        current_user_in_workspace_or_error(ws_id=ws_id, relation=WorkspaceUserRelationTypes.OWNER)

        ws_user = WorkspaceUser.find(ws_id=ws_id, user_id=user_id)

        if not ws_user:
            raise GraphQLError("Could not find user in the workspace")

        ws_user.start_date = start_date

        try:
            ws_user.save_and_persist()
            return UpdateMember(ok=True, member=ws_user)
        except Exception as e:
            LOG.error(f'Could not update the workspace member. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not update the workspace member.')


class RemoveMember(graphene.Mutation):
    class Arguments:
        email = graphene.String()
        ws_id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, email, ws_id):
        current_user_in_workspace_or_error(ws_id=ws_id, elation=WorkspaceUserRelationTypes.OWNER)

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


class AddHoliday(graphene.Mutation):
    class Arguments:
        ws_id = graphene.Int()
        date = graphene.Date()
        name = graphene.String()

    ok = graphene.Boolean()
    holiday = graphene.Field(lambda: types.Holiday)

    @gql_jwt_required
    def mutate(self, _, ws_id, date, name):

        current_user_in_workspace_or_error(ws_id=ws_id, relation=WorkspaceUserRelationTypes.OWNER)

        try:
            holiday = WorkspaceHoliday(name=name, ws_id=ws_id,date=date)
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
        holiday = WorkspaceHoliday.find(id=id)

        if holiday is None:
            raise GraphQLError('Could not find holiday.')

        current_user_in_workspace_or_error(ws_id=holiday.ws_id, relatione=WorkspaceUserRelationTypes.OWNER)

        try:
            holiday.delete_and_persist()

            return RemoveHoliday(ok=True)
        except Exception as e:
            raise GraphQLError('Could not remove a holiday.')

