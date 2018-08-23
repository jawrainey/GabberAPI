# -*- coding: utf-8 -*-
"""
Handles uploading and access writes (ACL) for files in the Gabber bucket
"""
import base64
import boto3
import botocore.client
from flask import current_app as app
from uuid import uuid4

s3 = boto3.client(
    "s3",
    aws_access_key_id=app.config['S3_KEY'],
    aws_secret_access_key=app.config['S3_SECRET'],
    config=botocore.client.Config(signature_version='s3')
)


def __get_path(project_id, session_id, is_transcoded=False):
    """
    The path to specific Gabber session in the mode that the app is being run in.
    """
    return '{}/{}/{}/{}/{}'.format(
        app.config['S3_ROOT_FOLDER'],
        app.config['S3_PROJECT_MODE'],
        project_id,
        'transcoded' if is_transcoded else 'raw',
        session_id
    )


def transcode(project_id, session_id):
    """
    Use the project/session ID to retrieve the raw uploaded content, and transcode the audio
    recording to produce a smaller file (22k sample rate, 24 bit rate).

    :param project_id: which project does the recording belong to?
    :param session_id: which recording is it?
    """
    transcoder = boto3.client(
        'elastictranscoder',
        app.config['S3_REGION'],
        aws_access_key_id=app.config['S3_KEY'],
        aws_secret_access_key=app.config['S3_SECRET']
    )

    transcoder.create_job(
        PipelineId=app.config['S3_PIPELINE_ID'],
        Input={'Key': __get_path(project_id, session_id)},
        Outputs=[{
            'Key': __get_path(project_id, session_id, True),
            'PresetId': app.config['S3_PIPELINE_PRESET_ID']
        }]
    )


def signed_url(project_id, session_id):
    """
    Generates a signed URL for a given file (which includes its path) on S3.

    :param project_id: The ID of the project associated with the file to upload
    :param session_id: The ID of the session associated with the file to upload.
    :return: A temporary (2 hour) URL for a given file on S3.
    """
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': app.config['S3_BUCKET'], 'Key': __get_path(project_id, session_id, is_transcoded=True)},
        ExpiresIn=3600*2)


def upload(the_file, project_id, session_id):
    """
    Uploads a given file to S3

    :param the_file: The file (as binary) to upload
    :param project_id: The ID of the project associated with the file to upload
    :param session_id: The ID of the session associated with the file to upload.
    :return: True if the file uploaded successfully, otherwise False
    """
    s3.upload_fileobj(
        the_file,
        app.config['S3_BUCKET'],
        __get_path(project_id, session_id)
    )


def __static_path():
    return '{}/{}/static/'.format(app.config['S3_ROOT_FOLDER'], app.config['S3_PROJECT_MODE'])


def static_file_by_name(name):
    path = 'https://{}.s3.amazonaws.com/{}'.format(app.config['S3_BUCKET'], __static_path())
    return path + (name or 'default')


def upload_base64(data):
    filename = uuid4().hex
    s3.put_object(
        ACL='public-read',
        Bucket=app.config['S3_BUCKET'],
        Key=__static_path() + filename,
        Body=base64.b64decode(data),
        ContentType='image/jpeg',
        ContentEncoding='base64'
    )
    return filename
