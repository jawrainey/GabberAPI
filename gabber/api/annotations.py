# -*- coding: utf-8 -*-
"""
All annotations for a session
"""
from flask import request
from gabber import db
from flask_restful import Resource
from flask_jwt_extended import jwt_required, jwt_optional, get_jwt_identity
from gabber.utils.general import custom_response
from gabber.api.schemas.annotations import UserAnnotationSchema
from gabber.projects.models import Connection as UserAnnotationModel, Code as Tags, Project
from gabber.users.models import User
import gabber.api.helpers as helpers


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
        helpers.abort_if_unauthorized(Project.query.get(pid))
        annotations = UserAnnotationModel.query.filter_by(session_id=sid).all()
        return custom_response(200, data=UserAnnotationSchema(many=True).dump(annotations))

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

        user_annotation = UserAnnotationModel(
            content=json_data['content'],
            start_interval=json_data['start_interval'],
            end_interval=json_data['end_interval'],
            user_id=User.query.filter_by(email=get_jwt_identity()).first().id,
            session_id=sid
        )

        # TODO: tags are currently optional as they may not exist on the UI, yet.
        if json_data.get('tags'):
            user_annotation.tags.extend([Tags.query.filter_by(id=cid).first() for cid in json_data['tags']])
        db.session.add(user_annotation)
        db.session.commit()

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

        return custom_response(200)
