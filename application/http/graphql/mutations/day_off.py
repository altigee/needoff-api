import graphene, logging
from application.users.models import UserDevice, UserProfile
from application.balances.models import DayOff, LeaveTypes, LeaveTypesLabels
from application.auth.models import User
from application.http.graphql import types
from graphql import GraphQLError
from application.workspace.models import WorkspaceUserRoles, WorkspaceUserRole
from application.rules.models import execute_day_off_validation_rule
from application.http.graphql.util import (
    gql_jwt_required,
    current_user_in_workspace_or_error,
    check_role_or_error,
    current_user_or_error
)
from application.shared.notifications import send_push

LOG = logging.getLogger("[mutations]")


class CreateDayOff(graphene.Mutation):
    class Arguments:
        type = graphene.String()
        start_date = graphene.Date()
        end_date = graphene.Date()
        workspace_id = graphene.Int()
        user_id = graphene.Int()
        comment = graphene.String()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)
    errors = graphene.List(of_type=graphene.String)
    warnings = graphene.List(of_type=graphene.String)
    notes = graphene.List(of_type=graphene.String)

    @gql_jwt_required
    def mutate(self, _, type, start_date, end_date, workspace_id, user_id, comment):

        user_id = user_id or current_user_in_workspace_or_error(ws_id=workspace_id).id
        user = User.find_by_id(user_id)

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

            try:
                ws_owner = WorkspaceUserRole.find(ws_id=workspace_id, role=WorkspaceUserRoles.OWNER)
                if ws_owner is not None and ws_owner.user_id != user.id:
                    profile = UserProfile.find(user_id=user.id)
                    uds = UserDevice.find_all(user_id=ws_owner.user_id)
                    for ud in uds:
                        if ud is not None and ud.device_token is not None:
                            push_body = 'Someone needs off ;)'
                            if profile is not None:
                                push_body = '{} {} requested {}'.format(profile.first_name, profile.last_name,
                                                                        LeaveTypesLabels[type])
                            send_push(to=ud.device_token, title='Leave request', body=push_body,
                                      custom_data={'type': 'new_leave_requested'})
            except Exception as e:
                LOG.error(f'Failed to send push notification about new leave. Error: {e}')
            response.day_off = day_off
        except Exception as e:
            LOG.error(f'Could not add a day off. Error: {e}')
            raise GraphQLError('Could not add a day off')

        return response


class ApproveDayOff(graphene.Mutation):
    class Arguments:
        day_off_id = graphene.Int()

    ok = graphene.Boolean()
    day_off = graphene.Field(lambda: types.DayOff)

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
            try:
                uds = UserDevice.find_all(user_id=day_off.user_id)
                profile = UserProfile.find(user_id=user.id)
                for ud in uds:
                    if ud.device_token is not None:
                        title = 'Leave request approved'
                        body = 'Your request has been approved'
                        if profile is not None:
                            body = '{} {} approved your request for {}'.format(profile.first_name, profile.last_name,
                                                                               LeaveTypesLabels[day_off.leave_type])
                        send_push(to=ud.device_token, title=title, body=body, custom_data={'type': 'request_approved'})
            except Exception as e:
                LOG.error(f'Failed to send push notifications about leave approval. Error: {e}')

            return ApproveDayOff(ok=True)
        except Exception as e:
            LOG.error(f'Could not approve day off. Error: {e}')
            raise GraphQLError('Could not approve day off')
