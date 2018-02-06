# -*- coding: utf-8 -*-
"""
Content for all projects that a JWT authenticated user has access to
"""
from gabber.users.models import User
from gabber.projects.models import Project
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity


class AllProjects(Resource):
    """
    All public AND private projects for an authenticated user
    """
    @jwt_required
    def get(self):
        """
        The public/private projects for a JWT authenticated user.

        Mapped to: /api/projects/

        :return: A dictionary of public (i.e. available to all users) and private (user specific) projects.
        """
        current_user = get_jwt_identity()
        user_projects = User.query.filter_by(email=current_user).first().projects()
        public_projects = Project.query.filter_by(isProjectPublic=1).all()
        return {
            'private': [p.project_as_json() for p in user_projects],
            # Do not show the same projects in the public section if you are a member of that project
            'public': [p.project_as_json() for p in list(set(public_projects) - set(user_projects))]
        }
