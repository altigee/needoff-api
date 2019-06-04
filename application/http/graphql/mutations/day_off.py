import graphene
from application.balances.models import DayOff, is_valid_leave_type
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error
from graphql import GraphQLError
import datetime
import logging

LOG = logging.getLogger("[mutations]")


def to_date(date_time_str):
    return datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')


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
