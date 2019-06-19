import graphene, logging
from application.balances.models import DayOff, LeaveTypes
from application.http.graphql import types
from graphql import GraphQLError
from application.workspace.models import WorkspaceUserRoles
from application.rules.models import execute_day_off_validation_rule
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
    errors = graphene.List(of_type=graphene.String)
    warnings = graphene.List(of_type=graphene.String)
    notes = graphene.List(of_type=graphene.String)

    @gql_jwt_required
    def mutate(self, _, type, start_date, end_date, workspace_id, comment):

        user = current_user_in_workspace_or_error(ws_id=workspace_id)

        day_off = DayOff(
            leave_type=LeaveTypes[type],
            start_date=start_date,
            end_date=end_date,
            workspace_id=workspace_id,
            comment=comment,
            user_id=user.id)

        rule_result = execute_day_off_validation_rule(day_off=day_off)

        response = CreateDayOff(
            errors=rule_result.errors,
            warnings=rule_result.warnings,
            notes=rule_result.notes
        )

        if rule_result.is_rejected:
            return response

        try:
            day_off.save_and_persist()
            response.day_off = day_off
        except Exception as e:
            LOG.error(f'Could not add a day off. Error: {e}')
            raise GraphQLError('Could not add a day off')

        return response


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
