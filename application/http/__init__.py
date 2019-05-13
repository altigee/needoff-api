from utils.http import returns_json, NoJsonPayloadException
from sanic import Blueprint
import logging
import traceback
from application.http.models import *

LOG = logging.getLogger("[httperrors]")

httperrors = Blueprint("httperrors", __name__)


@httperrors.exception(Exception)
@returns_json
def handle_generic_exception(exc):
    LOG.error(f"Unhandled exception : {exc}. Stacktrace: {traceback.format_stack()}")
    return HttpError('Internal Server Error'), 500


@httperrors.exception(NoJsonPayloadException)
@returns_json
def handle_no_payload(exc):
    LOG.error(f"No payload received: {exc}. Stacktrace: {traceback.format_stack()}")
    return HttpError('No payload data'), 400
