import logging
from application.auth.models import User
from application.http.models import HttpError, HttpMessage
from utils.http import returns_json, json_convert
from sanic import Blueprint
from sanic_jwt import BaseEndpoint
from application.auth.v1_dto import *

LOG = logging.getLogger("[auth_v1]")

auth_v1 = Blueprint("auth_v1", __name__)
auth_v1.url_prefix = "/v1/auth"


class Register(BaseEndpoint):
    async def post(self, request, *args, **kwargs):
        username = request.json.get('username', None)
        email = request.json.get('email', None)

        if User.find_by_username(request.username):
            LOG.warning(f'Repeated registration for {request.username}')
            return HttpError(f'User {request.username} already exists'), 400

        access_token, output = await self.responses.get_access_token_output(
            request,
            user,
            self.config,
            self.instance)

        refresh_token = await self.instance.auth.get_refresh_token(request, user)
        output.update({
            self.config.refresh_token_name(): refresh_token
        })

        response = self.responses.get_token_reponse(
            request,
            access_token,
            output,
            refresh_token=refresh_token,
            config=self.config)

        return RegisterResponse(user.id, access_token, refresh_token)


@auth_v1.route('/register', methods=['POST'])
@returns_json
@json_convert(to=RegisterRequest)
async def register_v1(request: RegisterRequest):
    if User.find_by_username(request.username):
        LOG.warning(f'Repeated registration for {request.username}')
        return HttpError(f'User {request.username} already exists'), 400
    new_user = User(
        username=request.username,
        password=User.generate_hash(request.password),
        jti=decode_token(refresh_token)
    )
    await new_user.save_to_db()

    return RegisterResponse(new_user.id, access_token, refresh_token), 201


@auth_v1.route('/login', methods=['POST'])
@returns_json
@json_convert(to=LoginRequest)
async def login_v1(request: LoginRequest):
    current_user = await User.find_by_username(request.username)
    if not current_user:
        LOG.warning(f'Non-existing user {request.username} login')
        return HttpError(f"User {request.username} doesn't exist"), 400

    if User.verify_hash(request.password, current_user.password):
        access_token, refresh_token = new_tokens(current_user.username)
        current_user.jti = decode_token(refresh_token)['jti']
        await current_user.save_to_db()
        return LoginResponse(current_user.id, access_token, refresh_token), 200
    else:
        LOG.warning(f'Wrong credentials for user {request.username}')
        return HttpError('Wrong credentials'), 403


@auth_v1.route('/logout', methods=['POST'])
@returns_json
#@jwt_refresh_token_required
async def logout_v1(request):
    jti = get_raw_jwt()['jti']
    user = await User.find_by_username(get_jwt_identity())
    if user.jti != jti:
        LOG.warning(f'Wrong JTI ({jti}) for user {user.username} on logout')
        return HttpError('Invalid token'), 400
    user.jti = None
    await user.save_to_db()
    return HttpMessage('Refresh token has been revoked'), 200


@auth_v1.route('/token/refresh', methods=['POST'])
@returns_json
#@jwt_refresh_token_required
async def token_refresh_v1(request):
    jti = get_raw_jwt()['jti']
    user = await User.find_by_username(get_jwt_identity())
    if user.jti != jti:
        return HttpError('Invalid token'), 400
    access_token, refresh_token = new_tokens(user.username)
    user.jti = decode_token(refresh_token)['jti']
    await user.save_to_db()
    return RefreshResponse(
        access_token=access_token,
        refresh_token=refresh_token), 200


def new_tokens(identity):
    return create_access_token(identity=identity), \
           create_refresh_token(identity=identity)
