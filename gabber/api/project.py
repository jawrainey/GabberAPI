# -*- coding: utf-8 -*-
"""
Content for all projects that a user has access to
"""
from .. import db
from ..models.user import User
from ..models.projects import Project as ProjectModel, ProjectPrompt
from ..utils.general import custom_response
from ..api.schemas.project import ProjectModelSchema
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from flask import request
from gabber.utils import helpers


class Project(Resource):
    """
    Mapped to: /api/projects/<pid>/
    """
    @jwt_optional
    def get(self, pid):
        """
        The public/private projects for an authenticated user.

        :param pid: The ID of the project to VIEW
        :return: A dictionary of public (i.e. available to all users) and private (user specific) projects.
        """
        helpers.abort_on_unknown_project_id(pid)
        project = ProjectModel.query.filter_by(id=pid).first()
        helpers.abort_if_unknown_project(project)

        if project.is_public:
            return custom_response(200, ProjectModelSchema().dump(project))

        current_user = get_jwt_identity()
        if current_user:
            user = User.query.filter_by(email=current_user).first()
            helpers.abort_if_unknown_user(user)
            helpers.abort_if_not_a_member_and_private(user, project)
            return custom_response(200, ProjectModelSchema(user_id=user.id).dump(project))
        # If the user is not authenticated and the project is private
        return custom_response(200, errors=['PROJECT_DOES_NOT_EXIST'])

    @jwt_required
    def put(self, pid):
        """
        The project to UPDATE: expecting a whole Project object to be sent.
        """
        helpers.abort_on_unknown_project_id(pid)
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, pid)
        json_data = helpers.jsonify_request_or_abort()
        # TODO: have to have prompts to validate; must remove later
        json_data['prompts'] = json_data['topics']
        json_data['id'] = pid
        json_data['creator'] = user.id

        schema = ProjectModelSchema()
        errors = schema.validate(json_data)
        helpers.abort_if_errors_in_validation(errors)
        # TODO: When schema.load updates the model it does not invalidate the previous rows, and
        # (1) sets the FK to NULL and (2) does not update the is_active property.
        # I cannot figure out how to do that from within the schema and instead retrieve the
        # topics that exist for the current project, store them before updating the model,
        # then manually invalidate them. This issue may also relate to how I have setup the models.
        project = ProjectModel.query.get(pid)
        topics = project.prompts.all()
        # Deserialize data to internal ORM representation thereby overriding the data and then save it
        data = schema.load(json_data, instance=project)
        # Store the updates and therefore invalidating the previous topics and remove their project_id
        db.session.commit()
        # Only Delete is affected by this bug, so we re-populate the project_ids
        for topic in topics:
            if not topic.project_id:
                ProjectPrompt.query.filter_by(id=topic.id).update({'is_active': 0, 'project_id': pid})
        # TODO: this is temporary as it's hard-coded in the frontend and not validated in the schema above.
        project.organisation = int(json_data.get('organisation', {id: 0})['id'])
        db.session.commit()
        return custom_response(200, schema.dump(data))

    @jwt_required
    def delete(self, pid):
        helpers.abort_on_unknown_project_id(pid)
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, pid, action="projects.DELETE")
        ProjectModel.query.filter_by(id=pid).update({'is_active': False})
        db.session.commit()
        return custom_response(200)
