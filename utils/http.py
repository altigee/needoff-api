from flask import make_response, jsonify
from functools import wraps


def returns_json(func):
    @wraps(func)
    def jsonify_response(*args, **kwargs):
        result, status = func(*args, **kwargs)
        if type(result) is not dict:
            result = result.__dict__
        return make_response(jsonify(result)), status
    return jsonify_response


class NoJsonPayloadException(Exception):
    """ No JSON data was passed when it was required"""
    pass


def json_convert(to):
    if to is None:
        raise Exception('\'to\' argument not specified for @json_convert')

    def wrapper(func):
        @wraps(func)
        def map_to_object():
            from flask import request
            if not request.json:
                raise NoJsonPayloadException('No payload given')
            return func(to(**request.json))
        return map_to_object
    return wrapper
