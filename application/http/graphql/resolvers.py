# Place all the resolvers in this file
from application.auth.models import User as _User
from application.balances.models import Balance as _Balance, DayOff as _DayOff
from application.users.models import UserProfile as _UserProfile
from application.shared.database import db
from graphql import GraphQLError
from application.http.graphql.types import Balance
from application.rules.models import execute_balance_calculation_rule

from application.workspace.models import (
    WorkspaceModel as _WorkspaceModel,
    WorkspaceUser,
    WorkspaceInvitation,
    WorkspaceDate,
    WorkspaceUserRole,
    WorkspaceUserRoles
)
from application.http.graphql.util import (
    gql_jwt_required,
    current_user_or_error,
    current_user_in_workspace_or_error,
    check_role_or_error
)


@gql_jwt_required
def user_by_name(_, info, email):
    return _User.find_by_email(email)


@gql_jwt_required
def my_leaves(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _DayOff.find_all(user_id=user.id, workspace_id=workspace_id)


@gql_jwt_required
def user_leaves(_, info, workspace_id, user_id):
    return _DayOff.find_all(workspace_id=workspace_id, user_id=user_id)


@gql_jwt_required
def my_balance(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    rule_result = execute_balance_calculation_rule(ws_id=workspace_id, user_id=user.id)

    return Balance(
        left_paid_leaves=rule_result.left_paid_leaves,
        left_unpaid_leaves=rule_result.left_unpaid_leaves,
        left_sick_leaves=rule_result.left_sick_leaves,
        total_paid_leaves=rule_result.total_paid_leaves,
        total_unpaid_leaves=rule_result.total_unpaid_leaves,
        total_sick_leaves=rule_result.total_sick_leaves
    )


@gql_jwt_required
def balance_by_user(_, info, workspace_id, user_id):
    rule_result = execute_balance_calculation_rule(ws_id=workspace_id, user_id=user_id)

    return Balance(
        left_paid_leaves=rule_result.left_paid_leaves,
        left_unpaid_leaves=rule_result.left_unpaid_leaves,
        left_sick_leaves=rule_result.left_sick_leaves,
        total_paid_leaves=rule_result.total_paid_leaves,
        total_unpaid_leaves=rule_result.total_unpaid_leaves,
        total_sick_leaves=rule_result.total_sick_leaves
    )


@gql_jwt_required
def profile(_, info):
    user = current_user_or_error()
    return _UserProfile.find_by_user_id(user.id)


@gql_jwt_required
def my_workspaces(_, info):
    user = current_user_or_error()
    return _WorkspaceModel.find_by_user_id(user.id)


@gql_jwt_required
def workspace_by_id(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _WorkspaceModel.find(id=workspace_id)


@gql_jwt_required
def workspace_owner(_, info, workspace_id):
    owner_role = WorkspaceUserRole.find(ws_id=workspace_id, role=WorkspaceUserRoles.OWNER)
    if owner_role is None:
        raise GraphQLError("Failed to load workspace owner")
    try:
        return _UserProfile.find_by_user_id(user_id=owner_role.user_id)
    except Exception:
        return None


@gql_jwt_required
def workspace_invitations(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    return db.session.query(WorkspaceInvitation).filter_by(ws_id=workspace_id).order_by(
        WorkspaceInvitation.status.desc()).all()


@gql_jwt_required
def workspace_members(_, info, workspace_id):
    return WorkspaceUser.find_all(ws_id=workspace_id)


@gql_jwt_required
def workspace_member(_, info, workspace_id, user_id):
    return WorkspaceUser.find(ws_id=workspace_id, user_id=user_id)


@gql_jwt_required
def workspace_dates(_, info, workspace_id):
    current_user_in_workspace_or_error(ws_id=workspace_id)

    return WorkspaceDate.find_all(ws_id=workspace_id)


@gql_jwt_required
def team_calendar(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _DayOff.query(). \
        filter(_DayOff.workspace_id == workspace_id). \
        filter(_DayOff.approved_by_id != None). \
        all()


@gql_jwt_required
def day_offs(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _DayOff.query(). \
        filter(_DayOff.workspace_id == workspace_id). \
        all()


@gql_jwt_required
def day_offs_for_approval(_, info, workspace_id):
    check_role_or_error(ws_id=workspace_id, role=WorkspaceUserRoles.APPROVER)

    return _DayOff.query(). \
        filter(_DayOff.workspace_id == workspace_id). \
        filter(_DayOff.approved_by_id == None). \
        all()
