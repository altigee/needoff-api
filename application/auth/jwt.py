from sanic_jwt import exceptions
from .models import User
from sanic_jwt import Initialize


async def authenticate(request, *args, **kwargs):
    username = request.json.get("username", None)
    password = request.json.get("password", None)

    if not username or not password:
        raise exceptions.AuthenticationFailed("Missing username or password.")

    user = await User.find_by_username(username)
    if user is None:
        raise exceptions.AuthenticationFailed("User not found.")

    if User.verify_hash(password, user.password):
        raise exceptions.AuthenticationFailed("Password is incorrect.")

    return user


async def store_refresh_token(user_id, refresh_token, *args, **kwargs):
    user = await User.find_by_id(user_id)
    user.refresh_token = refresh_token
    await user.save_to_db()


async def retrieve_refresh_token(request, user_id, *args, **kwargs):
    user = await User.find_by_id(user_id)
    return user.refresh_token


def init_jwt(sanic_app):
    Initialize(sanic_app,
               authenticate=authenticate,
               path_to_authenticate='/v1/auth/login',
               # path_to_retrieve_user='/my_retrieve_user',
               path_to_verify='/v1/auth/verify',
               path_to_refresh='/v1/auth/refresh',
               refresh_token_enabled=True,
               store_refresh_token=store_refresh_token,
               retrieve_refresh_token=retrieve_refresh_token
               )
