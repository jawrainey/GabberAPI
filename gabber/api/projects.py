# -*- coding: utf-8 -*-
"""
Content for all projects that a user has access to
"""
from .. import db
from ..models.user import User
from ..models.projects import Membership, Project as ProjectModel, ProjectPrompt, Roles
from ..api.schemas.project import ProjectPostSchema, ProjectModelSchema
from flask_restful import Resource
from flask_jwt_extended import jwt_required, jwt_optional, get_jwt_identity
from gabber.utils.general import custom_response
from sqlalchemy import or_
import gabber.utils.helpers as helpers


class Projects(Resource):
    """
    All public AND private projects for an authenticated user

    Mapped to: /api/projects/
    """
    @staticmethod
    @jwt_optional
    def get():
        """
        The projects for an authenticated user; if unauthenticated, then only public projects are shown

        :return: A dictionary of public (i.e. available to all users) and private (user specific) projects.
        """
        current_user = get_jwt_identity()
        projects = ProjectModel.query.filter_by(is_public=True).order_by(ProjectModel.id.desc()).all()

        if current_user:
            user = User.query.filter_by(email=current_user).first()
            helpers.abort_if_unknown_user(user)
            projects = ProjectModel.query.filter(or_(
                ProjectModel.members.any(Membership.user_id == user.id),
                ProjectModel.is_public)).all()
        return custom_response(200, data=ProjectModelSchema(many=True).dump(projects))

    @jwt_required
    def post(self):
        """
        CREATE a project where sessions can be created
        """
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        helpers.abort_if_unknown_user(user)
        # Force request to JSON, and fail silently if that fails the data is None.
        json_data = helpers.jsonify_request_or_abort()

        schema = ProjectPostSchema()
        helpers.abort_if_errors_in_validation(schema.validate(json_data))
        data = schema.dump(json_data)

        project = ProjectModel(
            title=data['title'],
            description=data['description'],
            creator=user.id,
            # TODO: this should be privacy, which is passed Public/Private
            is_public=1 if data['privacy'] == 'public' else 0)

        admin_role = Roles.query.filter_by(name='admin').first().id
        membership = Membership(uid=user.id, pid=project.id, rid=admin_role, confirmed=True)
        project.members.append(membership)

        project.prompts.extend([ProjectPrompt(creator=user.id, text_prompt=topic) for topic in data['topics']])
        db.session.add(project)
        db.session.commit()

        return custom_response(201, data=ProjectModelSchema().dump(project))
