# Place all the resolvers in this file
from application.auth.models import User as _User
from application.balances.models import Balance as _Balance, DayOff as _DayOff, LeaveTypes
from application.users.models import UserProfile as _UserProfile
from application.shared.database import db
from application.http.graphql.types import Balance
from graphql import GraphQLError

from application.workspace.models import (
    WorkspaceModel as _WorkspaceModel,
    WorkspaceInvitation,
    WorkspacePolicy,
    WorkspaceUser,
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


# TODO: Consider using business rules engine to make this logic customizable per workspace.
@gql_jwt_required
def my_balance(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)

    policy = WorkspacePolicy.find(ws_id=workspace_id)

    if policy is None:
        raise GraphQLError('No policies defined for workspace.')

    leaves = _DayOff.query(). \
        filter(_DayOff.user_id == user.id). \
        filter(_DayOff.workspace_id == workspace_id). \
        filter(_DayOff.approved_by_id != None). \
        all()
    ws_user = WorkspaceUser.find(user_id=user.id, ws_id=workspace_id)
    worked_months = ws_user.get_worked_months()

    allowed_count_map = {
        LeaveTypes.SICK_LEAVE.name: policy.max_sick_leaves_per_year * worked_months // 12,
        LeaveTypes.VACATION_PAID.name: policy.max_paid_vacations_per_year * worked_months // 12,
        LeaveTypes.VACATION_UNPAID.name: policy.max_unpaid_vacations_per_year * worked_months // 12,
    }

    used_leaves_count_map = {t: 0 for t in LeaveTypes.__members__}

    for leave in leaves:
        leave_type = leave.leave_type.name
        if not (leave_type in used_leaves_count_map):
            continue  # Huh?

        work_days_count = WorkspaceDate.get_work_days_count(workspace_id, leave.start_date, leave.end_date)
        used_leaves_count_map[leave_type] += work_days_count

    result = {}

    for leave_type in LeaveTypes.__members__:
        if leave_type in allowed_count_map:
            result[leave_type] = allowed_count_map[leave_type]

        if leave_type in used_leaves_count_map and leave_type in allowed_count_map:
            result[leave_type] = allowed_count_map[leave_type] - used_leaves_count_map[leave_type]

    return Balance(
        left_paid_leaves=result[LeaveTypes.VACATION_PAID.name],
        left_unpaid_leaves=result[LeaveTypes.VACATION_UNPAID.name],
        left_sick_leaves=result[LeaveTypes.SICK_LEAVE.name],
        total_paid_leaves=allowed_count_map[LeaveTypes.VACATION_PAID.name],
        total_unpaid_leaves=allowed_count_map[LeaveTypes.VACATION_UNPAID.name],
        total_sick_leaves=allowed_count_map[LeaveTypes.SICK_LEAVE.name]
    )


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
def workspace_by_id(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _WorkspaceModel.find(id=workspace_id)


@gql_jwt_required
def workspace_owner(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
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
def day_offs_for_approval(_, info, workspace_id):
    check_role_or_error(ws_id=workspace_id, role=WorkspaceUserRoles.APPROVER)

    return _DayOff.query(). \
        filter(_DayOff.workspace_id == workspace_id). \
        filter(_DayOff.approved_by_id == None). \
        all()
