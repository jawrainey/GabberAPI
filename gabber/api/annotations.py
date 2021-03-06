# -*- coding: utf-8 -*-
"""
All annotations for a session
"""
from .. import db
from ..utils.general import custom_response
from ..utils.fcm import fcm
from ..api.schemas.annotations import UserAnnotationSchema
from ..models.projects import Connection as UserAnnotationModel, Code as Tags, Project, InterviewSession
from ..models.user import User
from flask import request
from flask_restful import Resource
from flask_jwt_extended import jwt_required, jwt_optional, get_jwt_identity
import gabber.utils.helpers as helpers


class UserAnnotations(Resource):
    """
    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/annotations/
    """
    @jwt_optional
    def get(self, pid, sid):
        """
        Returns a list of all annotations for an existing session
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        project = Project.query.get(pid)
        annotations = UserAnnotationModel.query.filter_by(session_id=sid).all()
        annotations = UserAnnotationSchema(many=True).dump(annotations)
        if project.is_public:
            return custom_response(200, data=annotations)
        helpers.abort_if_unauthorized(project)
        return custom_response(200, data=annotations)

    @jwt_required
    def post(self, pid, sid):
        """
        Create a new annotation on an existing session
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        helpers.abort_if_unauthorized(Project.query.get(pid))

        # Text and optionally, a list of tags (i.e. codes):
        json_data = request.get_json(force=True, silent=True)
        helpers.abort_if_invalid_json(json_data)

        schema = UserAnnotationSchema()
        helpers.abort_if_errors_in_validation(errors=schema.validate(json_data))

        user = User.query.filter_by(email=get_jwt_identity()).first()
        user_annotation = UserAnnotationModel(
            content=json_data['content'],
            start_interval=json_data['start_interval'],
            end_interval=json_data['end_interval'],
            user_id=user.id,
            session_id=sid
        )

        if json_data.get('tags', None):
            user_annotation.tags.extend([Tags.query.filter_by(id=cid).first() for cid in json_data['tags']])
        db.session.add(user_annotation)
        db.session.commit()

        InterviewSession.email_participants(user, sid)
        fcm.notify_participants_user_commented(pid, sid)

        return custom_response(200, data=schema.dump(user_annotation))


class UserAnnotation(Resource):
    """
    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/
    """
    @jwt_required
    def delete(self, pid, sid, aid):
        """
        Soft delete an existing annotation
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        user = helpers.abort_if_unauthorized(Project.query.get(pid))

        annotation = UserAnnotationModel.query.get(aid)
        helpers.abort_if_unknown_annotation(annotation)
        helpers.abort_if_not_user_made(user.id, annotation.user_id)

        UserAnnotationModel.query.filter_by(id=aid).update({'is_active': 0})
        db.session.commit()

        return custom_response(200)
