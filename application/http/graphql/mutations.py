import graphene
from application.balances.models import DayOff, is_valid_leave_type
from application.auth.models import User as _User
from flask_jwt_extended import get_jwt_identity
from application.http.graphql import types
from graphql import GraphQLError


class CreateDayOff(graphene.Mutation):
    class Arguments:
        leave_type = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    def mutate(self, args, leave_type):
        user = _User.find_by_username(get_jwt_identity())
        if not user:
            raise GraphQLError('User not found')
        if not is_valid_leave_type(leave_type):
            raise GraphQLError('Invalid leave type')
        day_off = DayOff()
        day_off.day_off_type = leave_type
        day_off.user_id = user.id
        day_off.save_and_persist()
        return CreateDayOff(day_off=day_off, ok=True)
