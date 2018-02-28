# -*- coding: utf-8 -*-
"""
Content for all projects that a JWT authenticated user has access to
"""
from gabber import db
from gabber.users.models import User
from gabber.projects.models import Membership, Project, Roles, InterviewSession
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity
from slugify import slugify


class ProjectSessions(Resource):
    @jwt_required
    def get(self, slug):
        """
        All the interview sessions for a given project

        :param slug: the project title slugified
        :return: A list of
        """
        if slug not in [p.slug for p in Project.query.all()]:
            abort(404, message='The provided project slug does not match to a project')

        user = User.query.filter_by(email=get_jwt_identity()).first()
        project = Project.query.filter_by(slug=slug).first()
        # If the project is private and the user is not a member
        if user.id not in [p.user_id for p in project.members] and not project.isProjectPublic:
            abort(404, message='You are not a member of this project')
        interview_sessions = InterviewSession.query.filter_by(project_id=project.id).all()
        return [i.serialize() for i in interview_sessions], 200


class JoinPublicProject(Resource):
    @jwt_required
    def post(self):
        """
        Joins a public project for a given user (determined through JWT token)

        Mapped to: /api/project/join/

        :return: 200 if all is well, otherwise error
        """
        parser = reqparse.RequestParser()
        parser.add_argument('slug', required=True, help="A slug of the project to join is required")
        args = parser.parse_args()
        slug = slugify(args['slug'])

        if not Project.query.filter_by(slug=slug):
            abort(404, message='A project for that slug was not found')

        current_user = get_jwt_identity()
        usr = User.query.filter_by(email=current_user).first()
        _project = Project.query.filter_by(slug=slug).first()

        if _project.isProjectPublic:
            user_role = Roles.query.filter_by(name='user').first().id
            membership = Membership(uid=usr.id, pid=_project.id, rid=user_role)
            _project.members.append(membership)
            db.session.add(_project)
            db.session.commit()
        return "", 200


class AllPublicProjects(Resource):
    """
    All public AND private projects for an authenticated user
    """
    def get(self):
        """
        All public projects; no JWT required

        Mapped to: /api/projects/public

        :return: A dictionary of public (i.e. available to all users) projects.
        """
        projects = Project.query.filter_by(isProjectPublic=1).order_by(Project.id.desc()).all()
        return [i.project_as_json() for i in projects]


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
        return User.query.filter_by(email=current_user).first().projects()
