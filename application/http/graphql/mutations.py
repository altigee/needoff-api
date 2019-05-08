import graphene
from application.balances.models import DayOffType, DayOff
from application.auth.models import User
from flask_jwt_extended import get_jwt_identity
from application.http.graphql import types
from graphql import GraphQLError


class CreateDayOff(graphene.Mutation):
    class Arguments:
        day_off_type = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    def mutate(self, args, day_off_type):
        user = User.find_by_username(get_jwt_identity())
        if not user:
            raise GraphQLError('User not found')
        day_off = DayOff()
        day_off.day_off_type = DayOffType[day_off_type]
        day_off.user_id = user.id
        day_off.save_to_db()
        return CreateDayOff(day_off=day_off, ok=True)
