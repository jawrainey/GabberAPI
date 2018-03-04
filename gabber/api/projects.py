# -*- coding: utf-8 -*-
"""
Content for all projects that a user has access to
"""
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import jwt_required, jwt_optional, get_jwt_identity
from gabber.api.helpers import abort_if_empty
from gabber.users.models import User
from gabber.projects.models import Membership, Project as ProjectModel, ProjectPrompt, Roles
import gabber.api.helpers as helpers
from slugify import slugify
from gabber import db


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

        if current_user:
            # TODO: check if user is known to the database
            user = User.query.filter_by(email=current_user).first()
            helpers.abort_if_unknown_user(user)
            projects = user.projects()
        else:
            projects = ProjectModel.all_public_projects()
        return projects

    @jwt_required
    def post(self):
        """
        CREATE a project where sessions can be created

            {
                "title": "The title of your neat project",
                "description": "Describe your project in at most 230 words",
                "privacy": "public",
                "topics": ["Topics must be less than 280 words", "Otherwise"]
            }

        Note:
            1) privacy options are: `public` and `private`"
            2) Anyone can create a project as long as they are logged in ...

        :return:
        """
        current_user = get_jwt_identity()
        usr = User.query.filter_by(email=current_user).first()
        helpers.abort_if_unknown_user(usr)

        parser = reqparse.RequestParser()
        parser.add_argument(
            'title',
            required=True,
            help='A title is required to create a project'
        )
        parser.add_argument(
            'description',
            required=True,
            help='A description is required to create a project'
        )
        parser.add_argument(
            'privacy',
            required=True,
            help='Privacy must be provided: either `public` or `private`'
        )
        parser.add_argument(
            'topics',
            required=True,
            help='A set of topics as a list must be provided',
            action='append'
        )

        args = parser.parse_args()

        # TODO: so much validation needs done here, including topics (for list of strings) and
        # if the project does not exist; this validation would be similar to UPDATE project
        # and hence sharing this between Scheme from mashmallow would simplify the logic

        title = abort_if_empty(args['title'])
        if ProjectModel.query.filter_by(slug=slugify(title)).first():
            abort(409, message='A project with that name already exists. Bad times.')

        privacy = abort_if_empty(args['privacy'])
        if privacy not in ['public', 'private']:
            abort(404, message='The privacy option you provided is invalid. Correct options are cd `public` or `private`')

        # TODO: validation the length of the description?
        description = abort_if_empty(args['description'])
        topics = abort_if_empty(args['topics'])

        project = ProjectModel(
            title=title,
            description=description,
            creator=usr.id,
            visibility=1 if privacy == 'public' else 0)

        admin_role = Roles.query.filter_by(name='admin').first().id
        membership = Membership(uid=usr.id, pid=project.id, rid=admin_role)
        project.members.append(membership)

        # TODO: validate the length of topic text?
        project.prompts.extend([ProjectPrompt(creator=usr.id, text_prompt=t) for t in topics])
        db.session.add(project)
        db.session.commit()

        return project.serialize(), 201
