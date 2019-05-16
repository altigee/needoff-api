# Place all the resolvers in this file
from application.auth.models import User as _User
from application.balances.models import Balance as _Balance, DayOff as _DayOff
from application.users.models import UserProfile as _UserProfile
from graphql import GraphQLError
import application.http.graphql.util as util

from flask import request

def user_by_name(_, info, username):
    return _User.find_by_username(username)


def my_leaves(_, info):
    user = util.current_user_or_error()
    return _DayOff.find_by_user_id(user.id)

def my_balance(_, info):
    user = util.current_user_or_error()
    return _Balance.find_by_user(user.id)


def balance_by_user(_, info, username):
    user = util.current_user_or_error()
    return _Balance.find_by_user(user.id)

def profile(_, info):
    user = util.current_user_or_error()
    return _UserProfile.find_by_user_id(user.id)
