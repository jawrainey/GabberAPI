# -*- coding: utf-8 -*-
"""
Contains a set of APIs required to access project, region, and playlist data.
This is in contrast to /api/views.py which can be considered the 'old' API.

TODO: clean user-input and authentication
"""
from gabber import db
from flask_restful import abort, Resource, reqparse
from gabber.users.models import User
from gabber.projects.models import Connection, Project, ProjectPrompt, PlaylistRegions, Interview
from gabber.projects.models import Playlists as PlaylistModel


def abort_if_user_or_playlist_doesnt_exist(user_id, playlist_id):
    """
    Validate the user id or playlist id here as this can be shared across endpoints

    :param user_id: The ID of a given User
    :param playlist_id: The ID of a given PlayList
    :return: An error (404) if either the User or PlayList does not exist
    """
    if (user_id not in [p.id for p in User.query.all()]) or \
            (playlist_id not in [p.id for p in PlaylistModel.query.all()]):
        abort(404, message="The provided user {} or playlist {} does not exist".format(user_id, playlist_id))

    if PlaylistModel.query.get(playlist_id).serialize()['uid'] != user_id:
        abort(404, message="This playlist ({}) is not associated with this user ({})".format(playlist_id, user_id))


class Projects(Resource):
    """
    Meta-data associated with a project obtained via its ID.
    """
    def get(self, pid):
        """
        The meta-data associated with a project, such as title, creation-date, codebook, and prompts.

        Mapped to: /api/project/<int:pid>

        :param pid: The ID of a project of interest
        :return: a dictionary of meta-data associated with a given project
        """
        # TODO: READ meta-data for a project [title, creation date, codes, topics, members]
        if pid not in [p.id for p in Project.query.all()]:
            return {'message': "The project with ID {} does not exist.".format(pid)}, 404
        return Project.query.get(pid).project_as_json(), 200


class RegionsListByProject(Resource):
    """
    A list of annotated regions from across all interviews for a particular project.
    """
    def get(self, project_id):
        """
        Regions associated with a particular Project (based on its ID).

        Mapped to: /api/project/<int:project_id>/regions/

        :param project_id: the ID of a specific project
        :return: A list of regions for a given project
        """
        connections = Connection.query.join(Interview, ProjectPrompt, Project).filter(Project.id == project_id).all()
        return [c.serialize() for c in connections], 200


class UserPlaylists(Resource):
    """
    The playlists created by a particular user;
    A specific playlist can be returned (via GET) or a list of user PlayLists (also via GET).
    """
    def post(self, user_id=None):
        """
        Create a new playlist for a given user by their ID

        Mapped to: '/api/users/<int:uid>/playlists (for POST)

        :param user_id: The unique identifier of a user
        :return: 201 if a playlist was successfully created, otherwise an error.
        """
        if not user_id:
            return {'message': 'no user ID provided'}, 404
        if user_id not in [user.id for user in User.query.all()]:
            return {'message': 'The provided does not exist'}, 404

        # i.e. we want to only use this method when no parameters are provided
        parser = reqparse.RequestParser()
        parser.add_argument('title', required=True, help="A title for your playlist is required")
        args = parser.parse_args()
        # TODO: validate clean user input
        playlist = PlaylistModel(name=args['title'], user_id=user_id)
        db.session.add(playlist)
        db.session.commit()
        return playlist.serialize(), 201

    def get(self, user_id=None, playlist_id=None):
        """
        The playlists a user is associated with as either a list or by a specific ID.

        Mapped to: '/api/users/<int:uid>/playlists/'
                   '/api/users/<int:uid>/playlists/<int:pid>'

        :param user_id: who are we searching for?
        :param playlist_id: are we interested in a specific project?
        :return: A list of serialized Playlist objects or an individual Playlist
        """
        known_user_playlist = [p.user_id for p in PlaylistModel.query.all()]
        if user_id in known_user_playlist and not playlist_id:
            return [pl.serialize() for pl in PlaylistModel.query.filter_by(user_id=user_id).all()]
        elif not playlist_id and user_id not in known_user_playlist:
            # i.e. this user does not have any playlists ... and is trying to get them all
            return [], 200
        abort_if_user_or_playlist_doesnt_exist(user_id, playlist_id)
        return PlaylistModel.query.filter_by(id=playlist_id, user_id=user_id).first().serialize(), 200


class RegionsListForPlaylist(Resource):
    """
    A list of regions that are associated with a user playlist and the feature to add more

    Note: this differs to `Projects.get` above as additional meta-data is added, such as notes
    """
    def post(self, uid, pid):
        """
        Created a region for a specific user playlist

        Mapped to: '/api/users/<int:uid>/playlists/<int:pid>/regions'

        :param uid: the unique identifier for a user: who are we searching for?
        :param pid: the unique identifier for a playlist: what playlist are we interested in?
        :return: Add a region to a specific user playlist
        """
        abort_if_user_or_playlist_doesnt_exist(uid, pid)

        parser = reqparse.RequestParser()
        parser.add_argument('regionID', type=int, required=True, help="A region ID is required to add to a playlist.")
        args = parser.parse_args()
        rid = args['regionID']

        # For now there, only let users add a playlist where the region is the same.
        if rid in [p.region_id for p in PlaylistRegions.query.filter_by(playlist_id=pid).all()]:
            return {'message': "A region with id {} already exists in this playlist".format(rid)}, 302
        # Otherwise add the region for the user to the specific playlist
        region = PlaylistRegions(uid=uid, pid=pid, rid=rid)
        db.session.add(region)
        db.session.commit()
        # The consumer may want to perform actions on the created region
        return region.serialize(), 201

    def get(self, uid, pid):
        """
        The regions for a specific user playlist

        Mapped to: '/api/users/<int:uid>/playlists/<int:pid>/regions'

        :param uid: the unique identifier for a user: who are we searching for?
        :param pid: the unique identifier for a playlist: what playlist are we interested in?
        :return: A list of regions associated with this specific user playlist
        """
        abort_if_user_or_playlist_doesnt_exist(uid, pid)
        return PlaylistModel.query.filter_by(id=pid, user_id=uid).first().serialize()['regions'], 200

    def delete(self, uid, pid):
        """
        The region that we would like to remove from the users playlist regions

        :param uid: the unique identifier for a user: who are we searching for?
        :param pid: the unique identifier for a playlist: what playlist are we interested in?
        :return: a 204 code and no entity is returned to indicate
        """
        abort_if_user_or_playlist_doesnt_exist(uid, pid)

        parser = reqparse.RequestParser()
        parser.add_argument('regionID', type=int, required=True,
                            help="An ID of the region inside the playlist is required to remove it.")
        args = parser.parse_args()
        rid = args['regionID']

        if rid not in [r.region_id for r in PlaylistRegions.query.all()]:
            return {'message': "You are trying to remove a region from a playlist that does not exist"}, 302

        PlaylistRegions.query.filter_by(region_id=rid, playlist_id=pid, user_id=uid).delete()
        db.session.commit()
        return '', 204


class RegionNote(Resource):
    """
    A note for a specific region that is within a user playlist
    """
    def post(self, uid=None, pid=None, rid=None):
        """
        Create a note for a specific region; for now this is a 1 to 1 between a user and a note.

        Mapped: /api/users/<int:uid>/playlists/<int:pid>/region/<int:rid>/note

        :param uid: The ID of the user whose playlist we want to view
        :param pid: The specific playlist to view
        :param rid: The specific region to add a note to
        :return: The ID of a region to create a note for
        """
        if not uid:
            return {'message': 'no user ID provided'}, 404
        if uid not in [user.id for user in User.query.all()]:
            return {'message': 'The provided does not exist'}, 404

        # i.e. we want to only use this method when no parameters are provided
        if uid and pid and rid:
            parser = reqparse.RequestParser()
            parser.add_argument('note', required=True, help="Content for the note is required")
            args = parser.parse_args()
            region = PlaylistRegions.query.filter_by(user_id=uid, playlist_id=pid, region_id=rid).first()
            region.note = args['note']
            db.session.commit()
            return {'region': region.serialize()}, 201
