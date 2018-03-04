# -*- coding: utf-8 -*-
"""
A user can join or leave a project
"""
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from gabber.users.models import User
from gabber.projects.models import Project
from gabber.projects.models import Membership, Roles
import gabber.api.helpers as helpers
from gabber import db


class ProjectMembership(Resource):
    """
    Mapped to: /api/project/<int:id>/membership/
    """
    @jwt_required
    def post(self, pid=None):
        """
        Joins a public project for a given user (determined through JWT token)
        """
        _project = Project.query.get(pid)
        helpers.abort_if_unknown_project(_project)
        usr = User.query.filter_by(email=get_jwt_identity()).first()

        if _project.isProjectPublic and not usr.is_project_member(pid):
            user_role = Roles.query.filter_by(name='user').first().id
            membership = Membership(uid=usr.id, pid=_project.id, rid=user_role)
            _project.members.append(membership)
            db.session.add(_project)
            db.session.commit()
        return '', 204

    @jwt_required
    def delete(self, pid=None):
        """
        Leaves a project for a given user (determined through JWT token)
        """
        return '', 204
