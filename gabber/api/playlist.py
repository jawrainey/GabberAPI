# -*- coding: utf-8 -*-
"""
Actions on a users Playlists
"""
from .. import db
from ..models.user import User
from ..models.playlist import Playlist as PlaylistModel, PlaylistAnnotations
from ..utils.general import custom_response
from ..api.schemas.playlist import PlaylistSchema
from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from gabber.utils import helpers


class Playlist(Resource):
    """
    Mapped to: /api/playlists/<pid>/
    """
    @jwt_required
    def get(self, pid):
        """
        The public/private PLAYLISTS for an authenticated user.

        :param pid: The ID of the PLAYLIST to VIEW
        :return: A dictionary of public (i.e. available to all users) and private (user specific) PLAYLISTS.
        """
        playlist = self.user_created_playlist(pid, action='GET')
        return custom_response(200, data=PlaylistSchema().dump(playlist))

    @jwt_required
    def put(self, pid):
        """
        UPDATE a playlist
        """
        playlist = self.user_created_playlist(pid, action='UPDATE')
        json_data = helpers.jsonify_request_or_abort()

        schema = PlaylistSchema()
        helpers.abort_if_errors_in_validation(schema.validate(json_data))
        data = schema.load(json_data, instance=playlist)

        playlist.name = data.name
        playlist.description = data.description
        playlist.order = data.order

        self.crud_annotations(playlist, json_data['annotations'])

        db.session.commit()
        return custom_response(200, schema.dump(playlist))

    @jwt_required
    def delete(self, pid):
        """
        DELETE a playlist
        """
        playlist = self.user_created_playlist(pid, action='DELETE')
        playlist.is_active = False
        db.session.commit()
        return custom_response(200)

    @staticmethod
    def crud_annotations(playlist, updated):
        # We only care if they have been added/removed, e.g. not unchanged.
        prev_annotations = [i.annotation_id for i in playlist.annotations]
        new_annotations = [i['id'] for i in updated]
        # TODO: should this be two methods? AddNewAnnotation + DeleteExistingAnnotation
        deleted = [i for i in prev_annotations if i not in new_annotations]
        for annotation_id in deleted:
            playlist.annotations.filter_by(annotation_id=annotation_id).delete()

        added = [i for i in new_annotations if i not in prev_annotations]
        for annotation_id in added:
            db.session.add(PlaylistAnnotations(playlist_id=playlist.id, annotation_id=annotation_id))

    @staticmethod
    def user_created_playlist(pid, action):
        helpers.abort_on_unknown_playlist_id(pid)
        user = User.query.filter_by(email=get_jwt_identity()).first()
        helpers.abort_if_unknown_user(user)

        playlist = PlaylistModel.query.filter_by(id=pid).first()

        if playlist.user_id != user.id:
            raise custom_response(403, errors=['%s_UNAUTHORIZED' % action])
        return playlist
