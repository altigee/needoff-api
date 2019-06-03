# Place all the resolvers in this file
from application.auth.models import User as _User
from application.balances.models import Balance as _Balance, DayOff as _DayOff
from application.users.models import UserProfile as _UserProfile
from application.workspace.models import (WorkspaceModel as _WorkspaceModel,
                                          WorkspaceInvitation,
                                          WorkspaceUserModel,
                                          WorkspaceUserRelationTypes,
                                          WorkspaceHolidayCalendar,
                                          Holiday)
from application.http.graphql.util import (
    gql_jwt_required,
    current_user_or_error,
    current_user_in_workspace_or_error
)
from application.shared.database import db


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
def workspace_by_id(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _WorkspaceModel.find(id=workspace_id)


@gql_jwt_required
def workspace_owner(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    ws_user = WorkspaceUserModel.find(ws_id=workspace_id, relation_type=WorkspaceUserRelationTypes.OWNER)
    try:
        return _UserProfile.find_by_user_id(ws_user.user_id)
    except Exception:
        return None


@gql_jwt_required
def workspace_invitations(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    return db.session.query(WorkspaceInvitation).filter_by(ws_id=workspace_id).order_by(
        WorkspaceInvitation.status.desc()).all()


@gql_jwt_required
def workspace_calendars(_, info, workspace_id):
    _ = current_user_in_workspace_or_error(ws_id=workspace_id)
    return WorkspaceHolidayCalendar.find_all(ws_id=workspace_id)


@gql_jwt_required
def calendar_holidays(_, info, calendar_id):
    calendar = WorkspaceHolidayCalendar.find(id=calendar_id)

    if calendar is None:
        return []

    _ = current_user_in_workspace_or_error(ws_id=calendar.ws_id)

    return Holiday.find_all(calendar_id=calendar.id)


@gql_jwt_required
def team_calendar(_, info, workspace_id):
    user = current_user_in_workspace_or_error(ws_id=workspace_id)
    return _DayOff.find_all(workspace_id=workspace_id)
