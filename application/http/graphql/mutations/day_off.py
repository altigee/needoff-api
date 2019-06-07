import graphene, logging
from application.balances.models import DayOff, LeaveTypes, is_valid_leave_type
from application.workspace.models import WorkspaceUser, WorkspaceHoliday, WorkspaceUserRoles
from application.http.graphql import types
from graphql import GraphQLError
from application.http.graphql.util import (
    gql_jwt_required,
    current_user_in_workspace_or_error,
    check_role_or_error,
    current_user_or_error
)

LOG = logging.getLogger("[mutations]")


class CreateDayOff(graphene.Mutation):
    class Arguments:
        type = graphene.String()
        start_date = graphene.Date()
        end_date = graphene.Date()
        workspace_id = graphene.Int()
        comment = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

    @gql_jwt_required
    def mutate(self, _, type, start_date, end_date, workspace_id, comment):
        user = current_user_in_workspace_or_error(ws_id=workspace_id)
        ws_user = WorkspaceUser.find(user_id=user.id, ws_id=workspace_id)
        submitted_leaves = DayOff.query().\
            filter(DayOff.start_date <= end_date).\
            filter(DayOff.end_date >= start_date).\
            all()

        if not ws_user:
            raise GraphQLError('Invalid workspace')

        if not is_valid_leave_type(type):
            raise GraphQLError('Invalid leave type')

        # TODO: We should probably allow submitting it but mark it as "violating policies",
        #       so the approvers can decide whether to submit it. Change it while adding approvers functionality.
        if start_date > end_date:
            raise GraphQLError("Start date cannot be after the end date")

        if ws_user.start_date > start_date:
            raise GraphQLError("Day off dates should be after your Workspace start date")

        if ws_user.get_worked_months() < 3 and type == LeaveTypes.VACATION_PAID.name:
            raise GraphQLError("Paid vacations are only allowed after 3 months probation period")

        if WorkspaceHoliday.get_work_days_count(workspace_id, start_date, end_date) > 10:
            raise GraphQLError("Date range cannot exceed 10 business days")

        if len(submitted_leaves) > 0:
            raise GraphQLError("You've already submitted day offs within the given date range")

        try:
            day_off = DayOff(
                leave_type=type,
                start_date=start_date,
                end_date=end_date,
                workspace_id=workspace_id,
                comment=comment,
                user_id=user.id)
            day_off.save_and_persist()
        except Exception as e:
            LOG.error(f'Could not add a day off. Error: {e}')
            raise GraphQLError('Could not add a day off')

        return CreateDayOff(day_off=day_off, ok=True)


class ApproveDayOff(graphene.Mutation):
    class Arguments:
        day_off_id = graphene.Int()

    ok = graphene.Boolean()

    @gql_jwt_required
    def mutate(self, _, day_off_id):
        day_off = DayOff.find(id=day_off_id)
        user = current_user_or_error()

        if not day_off:
            raise GraphQLError("Could not find a day off")

        check_role_or_error(ws_id=day_off.workspace_id, role=WorkspaceUserRoles.APPROVER)

        try:
            day_off.approved_by_id = user.id
            day_off.save_and_persist()
            return ApproveDayOff(ok=True)
        except Exception as e:
            LOG.error(f'Could not approve day off. Error: {e}')
            raise GraphQLError('Could not approve day off')
