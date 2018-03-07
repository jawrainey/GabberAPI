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
        project = ProjectModel.query.get(pid)
        schema = ProjectModelSchema()

        if project.isProjectPublic:
            return custom_response(200, schema.dump(project))

        current_user = get_jwt_identity()
        if current_user:
            user = User.query.filter_by(email=current_user).first()
            helpers.abort_if_unknown_user(user)
            helpers.abort_if_not_a_member_and_private(user, project)
            return custom_response(200, schema.dump(project))

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
        # Deserialize data to internal ORM representation
        data = schema.load(json_data, instance=ProjectModel.query.get(pid))
        # thereby overriding the data and then save it
        db.session.commit()
        return custom_response(200, schema.dump(data))

    @jwt_required
    def delete(self, pid):
        helpers.abort_on_unknown_project_id(pid)
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, pid, action="DELETE")
        # TODO: the model needs updated, then /projects/ and /project/<id>
        # should only return views if the project is active. Likewise, all
        # actions on a project should not
        # ProjectModel.query.filter_by(id=pid).update({'is_active': 0})
        return "", 204

    @staticmethod
    def update_topic_by_attribute(topic_id, known_topic_ids, data, action="UPDATE"):
        """
        Helper method to UPDATE or DELETE a project's Topic

        :param topic_id: the ID of the topic to update
        :param known_topic_ids: pre-calculated list of known topics
        :param data: a dictionary of the topic attribute and value to update
        :param action: the action being performed as a string to
        :return: an error (400 code) is the topic is not known
        """
        if topic_id not in known_topic_ids:
            ProjectPrompt.query.filter_by(id=topic_id).update(data)
        else:
            abort(404, message='The topic you tried to %s does not exist.' % action)
