# -*- coding: utf-8 -*-
"""
Uses an external API (unsplash) to search for images to use to represent a project
"""
from ..utils.general import custom_response
from flask import request
from flask_restful import Resource
from pyunsplash import PyUnsplash


class SearchImages(Resource):
    """
    Mapped to: /api/misc/photos/

    Note: the user must add a query parameter, e.g. /?query=cats
    """
    def get(self):
        """
        Retrieves a list of thumbnails
        """
        from flask import current_app as app
        query = request.args.get('query', None)

        if query:
            pu = PyUnsplash(api_key=app.config['PHOTOS_API_KEY'])
            search = pu.search(type_='photos', query=query)
            thumbnails = [photo.body['urls']['thumb'] for photo in list(search.entries)]
            return custom_response(200, data={'thumbnails': thumbnails})
        return custom_response(500, errors=['general.NO_PHOTOS'])


