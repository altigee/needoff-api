import graphene
import application.http.graphql.types as types
import application.http.graphql.resolvers as resolvers
from application.http.graphql.mutations import user, day_off, holiday_calendar, workspace


class Query(graphene.ObjectType):
    user_by_name = graphene.Field(types.User,
                                  email=graphene.String(required=True),
                                  resolver=resolvers.user_by_name)

    my_leaves = graphene.List(types.DayOff,
                              workspace_id=graphene.Int(required=True),
                              resolver=resolvers.my_leaves)

    my_balance = graphene.List(types.Balance, resolver=resolvers.my_balance)

    balance_by_user = graphene.List(types.Balance,
                                    email=graphene.String(required=True),
                                    resolver=resolvers.balance_by_user)

    profile = graphene.Field(types.Profile,
                             resolver=resolvers.profile)

    my_workspaces = graphene.List(types.Workspace,
                                  resolver=resolvers.my_workspaces)

    workspace_by_id = graphene.Field(types.Workspace,
                                     workspace_id=graphene.Int(required=True),
                                     resolver=resolvers.workspace_by_id)
    workspace_owner = graphene.Field(types.Profile,
                                     workspace_id=graphene.Int(required=True),
                                     resolver=resolvers.workspace_owner)

    workspace_invitations = graphene.List(types.WorkspaceInvitation,
                                          workspace_id=graphene.Int(required=True),
                                          resolver=resolvers.workspace_invitations)

    workspace_calendars = graphene.List(types.WorkspaceHolidayCalendar,
                                        workspace_id=graphene.Int(required=True),
                                        resolver=resolvers.workspace_calendars)

    workspace_calendar_by_id = graphene.Field(types.WorkspaceHolidayCalendar,
                                              calendar_id=graphene.Int(required=True),
                                              resolver=resolvers.workspace_calendar_by_id)

    calendar_holidays = graphene.List(types.Holiday,
                                      calendar_id=graphene.Int(required=True),
                                      resolver=resolvers.calendar_holidays)

    team_calendar = graphene.List(types.DayOff, workspace_id=graphene.Int(required=True),
                                  resolver=resolvers.team_calendar)


class Mutation(graphene.ObjectType):
    login = user.Login.Field()
    register = user.Register.Field()
    create_day_off = day_off.CreateDayOff.Field()
    create_workspace = workspace.CreateWorkspace.Field()
    add_workspace_member = workspace.AddMember.Field()
    remove_workspace_member = workspace.RemoveMember.Field()
    create_workspace_calendar = holiday_calendar.CreateCalendar.Field()
    remove_workspace_calendar = holiday_calendar.RemoveCalendar.Field()
    add_holiday = holiday_calendar.AddHoliday.Field()
    remove_holiday = holiday_calendar.RemoveHoliday.Field()


def create_schema(dump_to_file):
    # noinspection PyTypeChecker
    schema = graphene.Schema(
        query=Query,
        mutation=Mutation,
        types=[
            types.DayOff,
            types.User,
            types.Balance,
            types.Profile,
            types.Workspace,
            types.WorkspaceInvitation
        ]
    )

    if dump_to_file:
        try:
            with open('./application/http/graphql/schema.graphql', 'w') as fp:
                fp.write(str(schema))
        except IOError:
            import logging
            logging.getLogger('[GraphQL Schema]').exception('Could not dump schema to a file')

    return schema
