import logging
import datetime
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt,
    decode_token
)
from application.auth.models import User
from application.http.models import HttpError, HttpMessage
from application.workspace.models import *
from utils.http import returns_json, json_convert
from flask import Blueprint
from application.auth.v1_dto import *

LOG = logging.getLogger("[auth_v1]")

auth_v1 = Blueprint("auth_v1", __name__)
auth_v1.url_prefix = "/v1/auth"


@auth_v1.route('/login', methods=['POST'])
@returns_json
@json_convert(to=LoginRequest)
def login_v1(request: LoginRequest):
    current_user = User.find_by_email(request.email)
    if not current_user:
        LOG.warning(f'Non-existing user {request.email} login')
        return HttpError(f"User {request.email} doesn't exist"), 400

    if User.verify_hash(request.password, current_user.password):
        access_token, refresh_token = new_tokens(current_user.email)
        current_user.jti = decode_token(refresh_token)['jti']
        current_user.save_and_persist()
        return LoginResponse(current_user.id, access_token, refresh_token), 200
    else:
        LOG.warning(f'Wrong credentials for user {request.email}')
        return HttpError('Wrong credentials'), 403


@auth_v1.route('/logout', methods=['POST'])
@returns_json
@jwt_refresh_token_required
def logout_v1():
    jti = get_raw_jwt()['jti']
    user = User.find_by_email(get_jwt_identity())
    if user.jti != jti:
        LOG.warning(f'Wrong JTI ({jti}) for user {user.email} on logout')
        return HttpError('Invalid token'), 400
    user.jti = None
    user.save_and_persist()
    return HttpMessage('Refresh token has been revoked'), 200


@auth_v1.route('/token/refresh', methods=['POST'])
@returns_json
@jwt_refresh_token_required
def token_refresh_v1():
    jti = get_raw_jwt()['jti']
    user = User.find_by_email(get_jwt_identity())
    if not user:
        return HttpError('User not found'), 404
    if user.jti != jti:
        return HttpError('Invalid token'), 400
    access_token, refresh_token = new_tokens(user.email)
    user.jti = decode_token(refresh_token)['jti']
    user.save_and_persist()
    return RefreshResponse(
        access_token=access_token,
        refresh_token=refresh_token), 200


def new_tokens(identity):
    return create_access_token(identity=identity), \
           create_refresh_token(identity=identity)
