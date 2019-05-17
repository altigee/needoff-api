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
        if _UserModel.find_by_username(email):
            LOG.warning(f'Repeated registration for {email}')
            raise GraphQLError(f'User {email} already exists')

        access_token = create_access_token(identity=email)
        refresh_token = create_refresh_token(identity=email)
        new_user = _UserModel(
            username=email,
            password=_UserModel.generate_hash(password),
            jti=decode_token(refresh_token)['jti'],
            created_time=datetime.datetime.now()
        )
        new_user.save_and_persist()
        return RegisterUser(ok=True, response=RegisterUserResponse(id=new_user.id, email=new_user.username))


class CreateDayOff(graphene.Mutation):
    class Arguments:
        leave_type = graphene.String()
        start_date = graphene.String()
        end_date = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    @gql_jwt_required
    def mutate(self, _, leave_type, start_date, end_date):
        user = _UserModel.find_by_username(get_jwt_identity())
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
