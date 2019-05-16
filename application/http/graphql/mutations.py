import graphene
from application.balances.models import DayOff, is_valid_leave_type
from application.auth.models import User as _User
from flask_jwt_extended import get_jwt_identity
from application.http.graphql import types
from graphql import GraphQLError
import datetime


def to_date(date_time_str):
    return datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S.%f')


class CreateDayOff(graphene.Mutation):
    class Arguments:
        leave_type = graphene.String()
        start_date = graphene.String()
        end_date = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    def mutate(self, args, leave_type, start_date, end_date):
        user = _User.find_by_username(get_jwt_identity())
        if not user:
            raise GraphQLError('User not found')
        if not is_valid_leave_type(leave_type):
            raise GraphQLError('Invalid leave type')
        day_off = DayOff(
            leave_type=leave_type,
            start_date=to_date(start_date),
            end_date=to_date(end_date),
            user_id=user.id)
        day_off.save_and_persist()
        return CreateDayOff(day_off=day_off, ok=True)
