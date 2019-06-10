from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from functools import wraps
from application.auth.models import User as _User
from application.workspace.models import WorkspaceUser, WorkspaceUserRole
from graphql import GraphQLError


def current_user_or_error(message="User not found"):
    user = _User.find_by_email(get_jwt_identity())
    if not user:
        raise GraphQLError(message)
    return user


def current_user_in_workspace_or_error(ws_id, message="Wrong association"):
    user = current_user_or_error()
    find_kwargs = {
        "user_id": user.id,
        "ws_id": ws_id
    }


    assoc = WorkspaceUser.find(**find_kwargs)
    if not assoc:
        raise GraphQLError(message)


    return user


def check_role_or_error(ws_id, role, error="Not permitted"):
    user = current_user_or_error()

    if not WorkspaceUserRole.find(ws_id=ws_id, user_id=user.id, role=role):
        raise GraphQLError(error)


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
