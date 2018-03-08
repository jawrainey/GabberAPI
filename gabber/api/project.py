# -*- coding: utf-8 -*-
"""
Content for all projects that a user has access to
"""
from gabber import db
from gabber.users.models import User
from gabber.projects.models import Project as ProjectModel, ProjectPrompt
from gabber.utils.general import custom_response
from gabber.api.schemas.project import ProjectModelSchema
from flask_restful import Resource, abort
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from flask import request
import gabber.api.helpers as helpers


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
        schema = ProjectModelSchema()

        if project.isProjectPublic:
            return custom_response(200, schema.dump(project))

        current_user = get_jwt_identity()
        if current_user:
            user = User.query.filter_by(email=current_user).first()
            helpers.abort_if_unknown_user(user)
            helpers.abort_if_not_a_member_and_private(user, project)
            return custom_response(200, schema.dump(project))
        # If the user is not authenticated and the project is private
        return custom_response(200, errors=['PROJECT_DOES_NOT_EXIST'])

    @jwt_required
    def put(self, pid):
        """
        The project to UPDATE: expecting a whole Project object to be sent.
        """
        helpers.abort_on_unknown_project_id(pid)
        current_user = get_jwt_identity()
        user = User.query.filter_by(email=current_user).first()
        helpers.abort_if_unknown_user(user)

        json_data = request.get_json(force=True, silent=True)
        helpers.abort_if_invalid_json(json_data)

        schema = ProjectModelSchema()
        errors = schema.validate(json_data)
        helpers.abort_if_errors_in_validation(errors)
        # Otherwise the update will fail
        helpers.abort_if_data_pid_not_route_pid(json_data['id'], pid)
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
        db.session.commit()
        return custom_response(200, schema.dump(data))

    @jwt_required
    def delete(self, pid):
        helpers.abort_on_unknown_project_id(pid)
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, pid, action="DELETE")
        ProjectModel.query.filter_by(id=pid).update({'is_active': 0})
        return custom_response(200)
