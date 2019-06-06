import graphene
from application.balances.models import DayOff, is_valid_leave_type
from application.http.graphql import types
from application.http.graphql.util import gql_jwt_required, current_user_or_error
from graphql import GraphQLError
import logging

LOG = logging.getLogger("[mutations]")


class CreateDayOff(graphene.Mutation):
    class Arguments:
        type = graphene.String()
        start_date = graphene.Date()
        end_date = graphene.Date()
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
            start_date=start_date,
            end_date=end_date,
            workspace_id=workspace_id,
            comment=comment,
            user_id=user.id)
        day_off.save_and_persist()
        return CreateDayOff(day_off=day_off, ok=True)
