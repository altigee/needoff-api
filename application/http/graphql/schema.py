import graphene
import application.http.graphql.types as types
import application.http.graphql.resolvers as resolvers
from application.http.graphql.mutations import user, day_off, workspace


class Query(graphene.ObjectType):
    user_by_name = graphene.Field(types.User,
                                  email=graphene.String(required=True),
                                  resolver=resolvers.user_by_name)

    my_leaves = graphene.List(types.DayOff,
                              workspace_id=graphene.Int(required=True),
                              resolver=resolvers.my_leaves)

    user_leaves = graphene.List(types.DayOff,
                                workspace_id=graphene.Int(required=True),
                                user_id=graphene.Int(required=True),
                                resolver=resolvers.user_leaves)

    my_balance = graphene.Field(types.Balance,
                                workspace_id=graphene.Int(required=True),
                                resolver=resolvers.my_balance)

    balance_by_user = graphene.Field(types.Balance,
                                     user_id=graphene.Int(required=True),
                                     workspace_id=graphene.Int(required=True),
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

    workspace_members = graphene.List(types.WorkspaceUser,
                                      workspace_id=graphene.Int(required=True),
                                      resolver=resolvers.workspace_members)

    workspace_member = graphene.Field(types.WorkspaceUser,
                                     workspace_id=graphene.Int(required=True),
                                     user_id=graphene.Int(required=True),
                                     resolver=resolvers.workspace_member)

    workspace_dates = graphene.List(types.WorkspaceDate,
                                    workspace_id=graphene.Int(required=True),
                                    resolver=resolvers.workspace_dates)

    team_calendar = graphene.List(types.DayOff, workspace_id=graphene.Int(required=True),
                                  resolver=resolvers.team_calendar)

    day_offs_for_approval = graphene.List(types.DayOff,
                                          workspace_id=graphene.Int(required=True),
                                          resolver=resolvers.day_offs_for_approval)

    day_offs = graphene.List(types.DayOff,
                             workspace_id=graphene.Int(required=True),
                             resolver=resolvers.day_offs)


class Mutation(graphene.ObjectType):
    login = user.Login.Field()
    register = user.Register.Field()
    create_day_off = day_off.CreateDayOff.Field()
    approve_day_off = day_off.ApproveDayOff.Field()
    create_workspace = workspace.CreateWorkspace.Field()
    update_workspace = workspace.UpdateWorkspace.Field()
    add_workspace_member = workspace.AddMember.Field()
    update_workspace_member = workspace.UpdateMember.Field()
    remove_workspace_member = workspace.RemoveMember.Field()
    add_user_role = workspace.AddUserRole.Field()
    remove_user_role = workspace.RemoveUserRole.Field()
    add_workspace_date = workspace.AddWorkspaceDate.Field()
    remove_workspace_date = workspace.RemoveWorkspaceDate.Field()
    set_workspace_rule = workspace.SetWorkspaceRule.Field()


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
