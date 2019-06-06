# -*- coding: utf-8 -*-
"""
Content for all projects that a user has access to
"""
from .. import db
from ..models.user import User
from ..models.projects import Project as ProjectModel, TopicLanguage, Code, Codebook
from ..utils.general import custom_response
from ..api.schemas.project import ProjectModelSchema, ProjectLanguageSchema, \
    TopicLanguageSchema, CodebookSchema, TagsSchema
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity, jwt_optional
from gabber.utils import helpers
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

        json_data['id'] = pid
        json_data['creator'] = user.id

        schema = ProjectModelSchema()
        errors = schema.validate(json_data)
        helpers.abort_if_errors_in_validation(errors)

        # When the project is updated, only the image data (base-64) is sent if it has changed.
        if json_data.get('image', None):
            from ..utils import amazon
            json_data['image'] = amazon.upload_base64(json_data['image'])

        project = ProjectModel.query.get(pid)
        # TODO: it's unclear why schema.load does not load image correctly, hence needing to manually set it.
        project.image = json_data['image'] if json_data.get('image', None) else project.image
        project.is_public = json_data['privacy'] == 'public'

        # Loads project data: relations are not loaded in their own schemas
        data = schema.load(json_data, instance=project)

        self.add_codebook(project.id, json_data['codebook'])

        # Note: it may be better to move this to schema's pre-load
        for language, content in json_data['content'].items():
            # As the title may have changed, we must create a new slug
            content['slug'] = slugify(content['title'])
            # Overrides the title/description for the specific language that has changed
            plang = ProjectLanguageSchema().load(content, instance=data.content.filter_by(id=content['id']).first())
            for topic in content['topics']:
                # Updates the topic if it changes, otherwise adds a new topic
                if 'id' in topic:
                    TopicLanguageSchema().load(topic, instance=data.content.filter_by(id=topic['id']).first())
                else:
                    new_topic = TopicLanguage(project_id=project.id, lang_id=plang.lang_id, text=topic['text'])
                    db.session.add(new_topic)
        # Changes are stored in memory; if error occurs, wont be left with half-changed state.
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

    @staticmethod
    def add_codebook(project_id, json_codebook):
        codebook = CodebookSchema().dump(json_codebook)

        if 'id' not in codebook or not codebook.get('id', None):
            new_codebook = Codebook(project_id=project_id)
            db.session.add(new_codebook)
            db.session.commit()
            # To access below if it exists
            codebook['id'] = new_codebook.id

        for tag in codebook['tags']:
            if tag.get('id', None):
                TagsSchema().load(tag)
            else:
                new_tag = Code(text=tag['text'], codebook_id=codebook['id'])
                db.session.add(new_tag)
        db.session.commit()
