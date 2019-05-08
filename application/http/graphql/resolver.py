from flask import Blueprint
from flask_graphql import GraphQLView
from .schema import schema
from flask_jwt_extended import jwt_required
import logging

LOG = logging.getLogger('[graphql]')

graphql_resolver = Blueprint('graphql', __name__)


def init_graphql(jwt_enabled):
    graphql_view = GraphQLView.as_view(name='graphql', schema=schema)
    if jwt_enabled:
        graphql_resolver.add_url_rule('/graphql', view_func=jwt_required(graphql_view))
    else:
        graphql_resolver.add_url_rule('/graphql', view_func=graphql_view)
