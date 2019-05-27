import application.http.graphql.resolvers as resolvers
from application.http.graphql.mutations import *
from flask_jwt_extended import jwt_required


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
    team_calendar = graphene.List(types.DayOff, workspace_id=graphene.Int(required=True), resolver=resolvers.team_calendar)


class Mutation(graphene.ObjectType):
    login = LoginUser.Field()
    register = RegisterUser.Field()
    create_day_off = CreateDayOff.Field()
    create_workspace = CreateWorkspace.Field()


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
            types.Workspace
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
