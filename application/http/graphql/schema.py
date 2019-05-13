from graphene_sqlalchemy import SQLAlchemyConnectionField

from application.http.graphql.mutations import *
from application.http.graphql.types import *
import application.http.graphql.resolvers as resolvers


class Query(graphene.ObjectType):
    node = relay.Node.Field()
    all_users = SQLAlchemyConnectionField(types.User)
    user_by_name = graphene.Field(User,
                                  username=graphene.String(required=True),
                                  resolver=resolvers.user_by_name)
    all_days_off = SQLAlchemyConnectionField(types.DayOff)


class Mutation(graphene.ObjectType):
    create_day_off = CreateDayOff.Field()


def create_schema(dump_to_file):
    # noinspection PyTypeChecker
    schema = graphene.Schema(
        query=Query,
        mutation=Mutation,
        types=[
            types.DayOff,
            types.User
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

