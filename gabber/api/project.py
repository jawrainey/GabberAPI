# -*- coding: utf-8 -*-
"""
Content for all projects that a user has access to
"""
from gabber import db
from gabber.users.models import User
from gabber.projects.models import Project as ProjectModel, ProjectPrompt
from flask_restful import Resource, abort, reqparse
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
import gabber.api.helpers as helpers
from slugify import slugify


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

        if project.isProjectPublic:
            return project.serialize()

        current_user = get_jwt_identity()
        if current_user:
            user = User.query.filter_by(email=current_user).first()
            helpers.abort_if_unknown_user(user)
            helpers.abort_if_not_a_member_and_private(user, project)
            return project.serialize()

    @jwt_required
    def put(self, pid):
        """
        The project to UPDATE

        :param pid: The ID of the project to UPDATE
        :return: The UPDATED Project as a serialized object
        """
        helpers.abort_on_unknown_project_id(pid)
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)
        helpers.abort_if_not_admin_or_staff(user, pid, action="UPDATE")

        parser = reqparse.RequestParser()
        parser.add_argument(
            'title',
            required=False,
            help='A title is required to create a project'
        )
        parser.add_argument(
            'description',
            required=False,
            help='A description is required to create a project'
        )
        parser.add_argument(
            'privacy',
            required=False,
            help='Privacy must be provided: either `public` or `private`'
        )
        parser.add_argument(
            'topicsCreated',
            required=False,
            action='append',
            help='Expected a JSON object that contains a list of strings containing the topics and related text'
        )
        parser.add_argument(
            'topicsEdited',
            required=False,
            action='append',
            help='Expected a JSON object that contains a list of objects of existing topics that have been edited'
        )
        parser.add_argument(
            'topicsRemoved',
            required=False,
            help="Expecting a JSON object that contains a list of IDs of existing topics to remove"
        )

        args = parser.parse_args()
        # TODO: will be clean when marshalling
        title = helpers.abort_if_empty(args['title'])
        description = helpers.abort_if_empty(args['description'])
        privacy = helpers.abort_if_empty(args['privacy'])

        project = ProjectModel.query.get(pid)

        if title:
            project.title = title
            project.slug = slugify(title)
        if description:
            project.description = description
        if privacy:
            project.visibility = 1 if privacy == 'public' else 0

        topics_to_create = args['topicsCreated']
        topics_to_update = args['topicsEdited']
        topics_to_delete = args['topicsRemoved']

        known_topics = [p.id for p in project.prompts.all()]

        # TODO: need to use marshalling to simplify validation below; for now does not exist
        if topics_to_create:
            project.prompts.extend([ProjectPrompt(creator=user.id, text_prompt=text) for text in topics_to_create])

        if topics_to_update:
            for topic in topics_to_update:
                self.update_topic_by_attribute(topic['id'], known_topics, {'text_prompt': topic['text']})

        if topics_to_delete:
            for topic_id in topics_to_delete:
                self.update_topic_by_attribute(topic_id, known_topics, {'is_active': 0}, action="DELETE")

        db.session.add(project)
        db.session.commit()
        return project.serialize()

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
        topic_id = int(topic_id)
        if topic_id not in known_topic_ids:
            ProjectPrompt.query.filter_by(id=topic_id).update(data)
        else:
            abort(404, message='The topic you tried to %s does not exist.' % action)
