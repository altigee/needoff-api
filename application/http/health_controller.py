import logging
from application.shared.database import db
from sqlalchemy.sql import text
from sqlalchemy.exc import DatabaseError

from sanic import Blueprint
from utils.http import returns_json

LOG = logging.getLogger("[health_v1]")

health_v1 = Blueprint("health_v1", __name__)
health_v1.url_prefix = "/v1/health"


@health_v1.route('', methods=['GET'])
@returns_json
def health(request):
    return {'DB Status': db_available()}, 200


def db_available():

    try:
        db.session.query('1').from_statement(text('SELECT 1')).all()
        return "Ok"
    except DatabaseError as e:
        logging.error(e)
        return "Connection is broken"
