import logging, datetime
from flask import Blueprint
from dataclasses import dataclass
from utils.http import returns_json, json_convert
from application.auth.models import User
from application.workspace.models import *
from application.http.models import HttpError
from application.shared.database import db
from typing import List

from flask_jwt_extended import (
    jwt_required,
    current_user
)


LOG = logging.getLogger("[ws_v1]")

ws_v1 = Blueprint("workspace_v1", __name__)
ws_v1.url_prefix = "/v1/workspaces"


@dataclass
class WorkspaceCreateRequest:
    name: str
    enable_invitation_link: bool = False


@dataclass
class WorkspaceCreateResponse:
    id: int
    name: str
    invitation_link_token: str = ""


@dataclass
class WorkspaceInvitationRequestItem:
    email: str
    start_date: datetime.date = None # TODO: Figure out how to serialize JSON date string to date


@ws_v1.route("", methods=["POST"])
@jwt_required
@returns_json
@json_convert(to=WorkspaceCreateRequest)
def create_ws_v1(payload: WorkspaceCreateRequest):
    if WorkspaceModel.find(name=payload.name):
        LOG.warning(f'Attempt to create duplicate workspace {payload.name}')
        return HttpError(f'Workspace {payload.name} already exists'), 400

    try:
        ws = WorkspaceModel(name=payload.name)

        if payload.enable_invitation_link:
            ws.invitation_link_token = WorkspaceModel.generate_invitation_link_token()

        db.session.add(ws)
        db.session.flush()

        ws_user = WorkspaceUserModel(
            user_id=current_user.id,
            ws_id=ws.id,
            start_date=datetime.datetime.now()
        )
        db.session.add(ws_user)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        LOG.error(f"Workspace registration failed. Error: {e}")
        return HttpError('Could not register new workspace'), 500

    return WorkspaceCreateResponse(id=ws.id, name=ws.name, invitation_link_token=ws.invitation_link_token), 201


@ws_v1.route("/<ws_id>/invitations", methods=["POST"])
@jwt_required
@json_convert(to=WorkspaceInvitationRequestItem)
def invite_v1(payload: WorkspaceInvitationRequestItem, ws_id):

    if WorkspaceUserModel.find(user_id=current_user.id, ws_id=ws_id) is None:
        return HttpError('Could not find associated workspace'), 404

    user = User.find(email=payload.email)
    if user is None:
        if WorkspaceInvitation.find(email=payload.email, ws_id=ws_id) is None:
            WorkspaceInvitation(email=payload.email, ws_id=ws_id, start_date=datetime.datetime.now(), status=WorkspaceInvitationStatus.PENDING).save()
    elif WorkspaceUserModel.find(user_id=user.id, ws_id=ws_id) is None:
        # start_date = payload.start_date if payload.start_date else datetime.date.now()
        start_date = datetime.datetime.now()
        WorkspaceUserModel(user_id=user.id, ws_id=ws_id, start_date=start_date).save_and_persist()

    return "", 201


@ws_v1.route("/accepted_link_tokens/<token>", methods=["POST"])
@jwt_required
def join_workspace_by_invitation_link_token(token):

    ws = WorkspaceModel.find(invitation_link_token=token)
    if ws is None:
        return HttpError('Invalid token'), 404

    if WorkspaceUserModel.find(ws_id=ws.id, user_id=current_user.id) is not None:
        return "", 201

    WorkspaceUserModel(ws_id=ws.id, user_id=current_user.id, start_date=datetime.datetime.now()).save_and_persist()

    return "", 201
