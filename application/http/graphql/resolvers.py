# Place all the resolvers in this file
from application.auth.models import User as _User


def user_by_name(_, info, username):
    return _User.find_by_username(username)
