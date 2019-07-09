from ... import ma
from ...models.playlist import Playlist, PlaylistAnnotations


class PlaylistAnnotationsSchema(ma.ModelSchema):
    class Meta:
        model = PlaylistAnnotations
        include_fk = True


class PlaylistSchema(ma.ModelSchema):
    annotations = ma.Method("_annotations")

    class Meta:
        model = Playlist
        include_fk = True

    @staticmethod
    def _annotations(data):
        from ...models.projects import Connection as UserAnnotationModel
        from .annotations import UserAnnotationSchema
        # Note: this means we do not return the ID of the PlaylistAnnotation ...
        annotations = [UserAnnotationModel.query.get(i.annotation_id)
                       for i in data.annotations if len(data.annotations.all()) > 0]
        return UserAnnotationSchema(many=True).dump(annotations)
