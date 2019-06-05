from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps
from application.auth.models import User as _User
from application.workspace.models import WorkspaceUser
from graphql import GraphQLError


def current_user_or_error(message="User not found"):
    user = _User.find_by_email(get_jwt_identity())
    if not user:
        raise GraphQLError(message)
    return user


def current_user_in_workspace_or_error(ws_id, message="Wrong association", relation=None):
    user = current_user_or_error()
    find_kwargs = {
        "user_id": user.id,
        "ws_id": ws_id
    }

    if relation is not None:
        find_kwargs["relation_type"] = relation

    assoc = WorkspaceUser.find(**find_kwargs)
    if not assoc:
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
