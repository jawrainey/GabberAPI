# -*- coding: utf-8 -*-
"""
All annotations for a session
"""
from flask import request
from gabber import db
from flask_restful import Resource
from flask_jwt_extended import jwt_required, jwt_optional, get_jwt_identity
from gabber.utils.general import custom_response
from gabber.api.schemas.annotations import UserAnnotationSchema, UserAnnotationPostSchema
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

        project = Project.query.get(pid)

        if not project.is_public:
            helpers.abort_if_unauthorized(project)

        annotations = UserAnnotationModel.query.filter_by(session_id=sid).all()
        schema = UserAnnotationSchema(many=True)
        return custom_response(200, data=schema.dump(annotations))

    @jwt_required
    def post(self, pid, sid):
        """
        Create a new annotation on an existing session
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        # Only members of a PRIVATE project can add an annotation through the API
        helpers.abort_if_unauthorized(Project.query.get(pid))

        # Text and optionally, a list of tags (i.e. codes):
        json_data = request.get_json(force=True, silent=True)
        helpers.abort_if_invalid_json(json_data)

        schema = UserAnnotationPostSchema()
        helpers.abort_if_errors_in_validation(schema.validate(json_data))

        data = schema.load(json_data)

        user_annotation = UserAnnotationModel(
            content=data['content'],
            start_interval=data['start_interval'],
            end_interval=data['end_interval'],
            user_id=User.query.filter_by(email=get_jwt_identity()).first().id,
            interview_id=sid,
        )

        user_annotation.tags.extend([Tags.query.filter_by(id=cid).first() for cid in data['tags']])
        db.session.add(user_annotation)
        db.session.commit()

        return custom_response(200, data=UserAnnotationSchema().dump(user_annotation))


class UserAnnotation(Resource):
    """
    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/
    """
    @jwt_required
    def put(self, pid, sid, aid):
        """
        Update an existing annotation

        Notes:
            (1) tags are currently optional
            (2) only the user who created the annotation can edit.
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        helpers.abort_if_unauthorized(Project.query.get(pid))
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        annotation = UserAnnotationModel.query.get(aid)
        helpers.abort_if_unknown_annotation(annotation)
        helpers.abort_if_not_a_member_and_private(user, Project.query.get(pid))
        helpers.abort_if_not_user_made(user.id, annotation.user_id)

        json_data = request.get_json(force=True, silent=True)
        helpers.abort_if_invalid_json(json_data)

        schema = UserAnnotationSchema()
        helpers.abort_if_errors_in_validation(schema.validate(json_data))

        data = schema.load(json_data, instance=annotation)
        db.session.commit()

        return custom_response(200, data=schema.dump(data))

    @jwt_required
    def delete(self, pid, sid, aid):
        """
        Soft delete an existing annotation
        """
        helpers.abort_on_unknown_project_id(pid)
        helpers.abort_if_invalid_parameters(pid, sid)
        helpers.abort_if_unauthorized(Project.query.get(pid))

        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_a_member_and_private(user, Project.query.get(pid))

        annotation = UserAnnotationModel.query.get(aid)
        helpers.abort_if_unknown_annotation(annotation)
        helpers.abort_if_not_user_made(user.id, annotation.user_id)

        UserAnnotationModel.query.filter_by(id=aid).update({'is_active': 0})

        return custom_response(200)
