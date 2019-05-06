import logging
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    jwt_refresh_token_required,
    get_jwt_identity,
    get_raw_jwt
)
from application.auth.models import UserModel, RevokedTokenModel
from application.http.models import HttpError, HttpMessage
from utils.http import returns_json, json_convert
from flask import Blueprint
from application.auth.v1_dto import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse

LOG = logging.getLogger("[auth_v1]")

auth_v1 = Blueprint("auth_v1", __name__)
auth_v1.url_prefix = "/v1/auth"


@auth_v1.route('/register', methods=['POST'])
@returns_json
@json_convert(to=RegisterRequest)
def register_v1(request: RegisterRequest):
    if UserModel.find_by_username(request.username):
        LOG.warning(f'Repeated registration for {request.username}')
        return HttpError(f'User {request.username} already exists'), 400

    new_user = UserModel(
        username=request.username,
        password=UserModel.generate_hash(request.password))
    new_user.save_to_db()
    access_token = create_access_token(identity=request.username)
    refresh_token = create_refresh_token(identity=request.username)
    return RegisterResponse(new_user.id, access_token, refresh_token), 201


@auth_v1.route('/login', methods=['POST'])
@returns_json
@json_convert(to=LoginRequest)
def login_v1(request: LoginRequest):
    current_user = UserModel.find_by_username(request.username)

    if not current_user:
        LOG.warning(f'Non-existing user {request.username} login')
        return HttpError(f"User {request.username} doesn't exist"), 400

    if UserModel.verify_hash(request.password, current_user.password):
        access_token = create_access_token(identity=request.username)
        refresh_token = create_refresh_token(identity=request.username)

        return LoginResponse(current_user.id, access_token, refresh_token), 200
    else:
        LOG.warning(f'Wrong credentials for user {request.username}')
        return HttpError('Wrong credentials'), 403


@auth_v1.route('/logout/access', methods=['POST'])
@returns_json
@jwt_required
def logout_access_v1():
    jti = get_raw_jwt()['jti']
    revoked_token = RevokedTokenModel(jti=jti)
    revoked_token.add()
    return HttpMessage('Access token has been revoked'), 200


@auth_v1.route('/logout/refresh', methods=['POST'])
@returns_json
@jwt_refresh_token_required
def logout_refresh_v1():
    jti = get_raw_jwt()['jti']
    revoked_token = RevokedTokenModel(jti=jti)
    revoked_token.add()
    return HttpMessage('Refresh token has been revoked'), 200


@auth_v1.route('/token/refresh', methods=['POST'])
@returns_json
@jwt_refresh_token_required
def token_refresh_v1():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return {'access_token': access_token}, 200
