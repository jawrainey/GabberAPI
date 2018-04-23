# -*- coding: utf-8 -*-
"""
Handles uploading and access writes (ACL) for files in the Gabber bucket
"""
import boto3
import botocore.client
import os

S3_BUCKET = os.getenv('S3_BUCKET', '')
S3_KEY = os.getenv('S3_KEY', '')
S3_SECRET = os.getenv('S3_SECRET', '')
S3_LOCATION = 'https://{}.s3.amazonaws.com/'.format(S3_BUCKET)

s3 = boto3.client(
    "s3",
    aws_access_key_id=S3_KEY,
    aws_secret_access_key=S3_SECRET,
    config=botocore.client.Config(signature_version='s3')
)


def __get_path(project_id, session_id):
    """
    The path to specific Gabber session in the mode that the app is being run in.
    """
    return '{}/{}/{}/{}'.format(
        os.getenv('APP_NAME', 'main'),
        os.environ.get('APP_MODE', 'dev'),
        project_id,
        session_id
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
        Params={'Bucket': S3_BUCKET, 'Key': __get_path(project_id, session_id)},
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
        S3_BUCKET,
        __get_path(project_id, session_id)
    )
