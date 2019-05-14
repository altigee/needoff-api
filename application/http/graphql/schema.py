import application.http.graphql.resolvers as resolvers
from application.http.graphql.mutations import *


class Query(graphene.ObjectType):
    user_by_name = graphene.Field(types.User,
                                  username=graphene.String(required=True),
                                  resolver=resolvers.user_by_name)
    my_balance = graphene.List(types.Balance, resolver=resolvers.my_balance)
    balance_by_user = graphene.List(types.Balance,
                                    username=graphene.String(required=True),
                                    resolver=resolvers.balance_by_user)


class Mutation(graphene.ObjectType):
    create_day_off = CreateDayOff.Field()


def create_schema(dump_to_file):
    # noinspection PyTypeChecker
    schema = graphene.Schema(
        query=Query,
        mutation=Mutation,
        types=[
            types.DayOff,
            types.User,
            types.Balance
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

