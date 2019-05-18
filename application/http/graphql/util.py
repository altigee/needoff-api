from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps
from application.auth.models import User as _User
from graphql import GraphQLError


def current_user_or_error(message="User not found"):
    user = _User.find_by_username(get_jwt_identity())
    if not user:
        raise GraphQLError(message)
    return user


def gql_jwt_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token_valid = True
        try:
            verify_jwt_in_request()
        except Exception as e:
            print(e)
            token_valid = False
        if not token_valid:
            raise GraphQLError(message="Invalid token.")
        return fn(*args, **kwargs)

    return wrapper
