import graphene

from application.workspace.models import (WorkspaceUserModel,
                                          WorkspaceUserRelationTypes,
                                          HolidayCalendar,
                                          Holiday)
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error
from graphql import GraphQLError
from application.shared.database import db, Persistent
import logging

LOG = logging.getLogger("[mutations]")


class CreateCalendar(graphene.Mutation):
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
            calendar = HolidayCalendar(name=name,ws_id=ws_id)
            calendar.save_and_persist()

            return CreateCalendar(ok=True, calendar=calendar)
        except Exception as e:
            LOG.error(f'Calendar creation failed. Error: {e}')
            Persistent.rollback()
            return GraphQLError('Could not create calendar.')


class RemoveCalendar(graphene.Mutation):
    class Arguments:
        id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, id):
        current_user = current_user_or_error()

        calendar = HolidayCalendar.find(id=id)

        if calendar is None:
            raise GraphQLError('Could not find a calendar.')

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=calendar.ws_id, relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            calendar.delete_and_persist()

            return RemoveCalendar(ok=True)
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

        calendar = HolidayCalendar.find(id=calendar_id)

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

        calendar = HolidayCalendar.find(id=holiday.calendar_id)

        if WorkspaceUserModel.find(user_id=current_user.id, ws_id=calendar.ws_id,
                                   relation_type=WorkspaceUserRelationTypes.OWNER) is None:
            raise GraphQLError('You you\'re not a workspace owner.')

        try:
            holiday.delete_and_persist()

            return RemoveHoliday(ok=True)
        except Exception as e:
            raise GraphQLError('Could not remove a holiday.')
