# Place all the resolvers in this file
from application.auth.models import User as _User
from application.balances.models import Balance as _Balance, DayOff as _DayOff
from application.users.models import UserProfile as _UserProfile
from application.workspace.models import WorkspaceModel as _WorkspaceModel
from application.http.graphql.util import (
    gql_jwt_required,
    current_user_or_error,
    current_user_in_workspace_or_error
)


@gql_jwt_required
def user_by_name(_, info, email):
    return _User.find_by_email(email)


@gql_jwt_required
def my_leaves(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _DayOff.find_all(user_id=user.id, workspace_id=workspace_id)


@gql_jwt_required
def my_balance(_, info):
    user = current_user_or_error()
    return _Balance.find_by_user_id(user.id)


@gql_jwt_required
def balance_by_user(_, info, email):
    user = current_user_or_error()
    return _Balance.find_by_user_id(user.id)


@gql_jwt_required
def profile(_, info):
    user = current_user_or_error()
    return _UserProfile.find_by_user_id(user.id)


@gql_jwt_required
def my_workspaces(_, info):
    user = current_user_or_error()
    return _WorkspaceModel.find_by_user_id(user.id)


@gql_jwt_required
def team_calendar(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _DayOff.find_all(workspace_id=workspace_id)
