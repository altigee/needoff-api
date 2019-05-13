from flask_jwt_extended import get_jwt_identity
from application.auth.models import User as _User
from graphql import GraphQLError


def current_user_or_error(message="User not found"):
    user = _User.find_by_username(get_jwt_identity())
    if not user:
        raise GraphQLError(message)
    return user
