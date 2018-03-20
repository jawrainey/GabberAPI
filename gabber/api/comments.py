# -*- coding: utf-8 -*-
"""
READ a list of the comments for an annotation or CREATE a new comment.
"""
from flask_restful import Resource
from flask_jwt_extended import jwt_required, jwt_optional
from gabber.projects.models import ConnectionComments as CommentsModel, Project
from gabber.api.schemas.annotations import UserAnnotationCommentSchema
from gabber.utils.general import custom_response
from gabber import db
import gabber.api.helpers as helpers


def create_comment(project_id, session_id, annotation_id, comment_id=None):
    """
    CREATE a comment within a session to an annotation, however, if comment_id
    is provided, then the comment is a comment on a comment, rather than on an annotation.
    """
    helpers.abort_if_invalid_parameters(project_id, session_id)
    user = helpers.abort_if_unauthorized(Project.query.get(project_id))
    if comment_id:
        helpers.abort_if_unknown_comment(comment_id, annotation_id)

    data = helpers.jsonify_request_or_abort()

    schema = UserAnnotationCommentSchema()
    helpers.abort_if_errors_in_validation(schema.validate(data))
    # Note: comment_id can be null, which represents that it is a parent
    comment = CommentsModel(data['content'], comment_id, user.id, annotation_id)
    db.session.add(comment)
    db.session.commit()
    return custom_response(201, data=schema.dump(comment))


class Comments(Resource):
    """
    All comments for an annotation

    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/
    """
    @jwt_required
    def post(self, pid, sid, aid):
        """
        CREATE a comment on a session annotation
        """
        return create_comment(pid, sid, aid)


class CommentsReplies(Resource):
    """
    Read all the children (i.e. replies) of a parent comment.

    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>/replies/
    """
    @staticmethod
    @jwt_optional
    def get(pid, sid, aid, cid):
        """
        READ a comment an session annotation
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        children = CommentsModel.query.filter_by(parent_id=cid).all()
        return custom_response(200, data=UserAnnotationCommentSchema(many=True).dump(children))


class Comment(Resource):
    """
    Read/Update/Delete a comment on an annotation, or CREATE a new comment of a comment.

    Mapped to: /api/projects/<int:pid>/sessions/<string:sid>/annotations/<int:aid>/comments/<int:cid>
    """
    @jwt_required
    def post(self, pid, sid, aid, cid):
        """
        CREATE a comment on a comment of an session annotation
        """
        return create_comment(pid, sid, aid, cid)

    @jwt_required
    def delete(self, pid, sid, aid, cid):
        """
        DELETE a comment an session annotation
        """
        helpers.abort_if_invalid_parameters(pid, sid)
        user = helpers.abort_if_unauthorized(Project.query.get(pid))
        helpers.abort_if_unknown_comment(cid, aid)
        comment = CommentsModel.query.filter_by(id=cid)
        helpers.abort_if_not_user_made_comment(user.id, comment.first().user_id)
        comment.update({'is_active': False})
        return custom_response(200)
