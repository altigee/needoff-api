import logging
from sanic import Blueprint
from dataclasses import dataclass
from utils.http import returns_json, json_convert
from application.auth.models import User as UserModel
from application.workspace.models import WorkspaceModel, WorkspaceUserModel
from application.http.models import HttpError
from application.shared.database import db

from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
)


LOG = logging.getLogger("[ws_v1]")

ws_v1 = Blueprint("workspace_v1", __name__)
ws_v1.url_prefix = "/v1/workspace"


@dataclass
class WorkspaceRegisterRequest:
    workspace_name: str
    username: str
    password: str


@dataclass
class WorkspaceRegisterResponse:
    workspace_name: str
    username: str
    password: str


@ws_v1.route("/register", methods=["POST"])
@returns_json
@json_convert(to=WorkspaceRegisterRequest)
def register_ws_v1(payload: WorkspaceRegisterRequest):
    if WorkspaceModel.find_by_name(payload.workspace_name):
        LOG.warning(f'Attempt to create duplicate workspace {payload.workspace_name}')
        return HttpError(f'Workspace {payload.workspace_name} already exists'), 400

    if UserModel.find_by_username(payload.username):
        LOG.warning(f'Repeated registration for {payload.username}')
        return HttpError(f'User {payload.username} already exists'), 400

    try:
        user = UserModel(
            username=payload.username,
            password=UserModel.generate_hash(payload.password))

        db.session.add(user)
        db.session.flush()

        ws = WorkspaceModel(
            name=payload.workspace_name,
            invitation_token=WorkspaceModel.generate_invitation_token_string()
        )
        db.session.add(ws)
        db.session.flush()

        ws_user = WorkspaceUserModel(
            user_id=user.id,
            ws_id=ws.id
        )
        db.session.add(ws_user)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        LOG.error(f"Workspace registration failed. Error: {e}")
        return HttpError('Could not register new workspace'), 500

    access_token = create_access_token(identity=payload.username)
    refresh_token = create_refresh_token(identity=payload.username)

    return WorkspaceRegisterResponse(user.id, access_token, refresh_token), 201
