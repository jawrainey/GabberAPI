# -*- coding: utf-8 -*-
"""
Handles uploading and access writes (ACL) for files in the Gabber bucket
"""

import boto3, botocore.client
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


def signed_url(path):
    """
    Generates a signed URL for a given file (which includes its path) on S3.

    :param path the complete path on S3, i.e. folderName/fileID as a string
    :return: A temporary (2 hour) URL for a given file on S3.
    """
    return s3.generate_presigned_url(
        ClientMethod='get_object',
        Params={'Bucket': S3_BUCKET, 'Key': path},
        ExpiresIn=3600*2)


def upload(the_file, path):
    """
    Uploads a given file to S3

    :param the_file: The file (as binary) to upload
    :param path: The name to store the file on S3, which can include the path.
    :return: True if the file uploaded successfully, otherwise  False
    """
    s3.upload_fileobj(
        the_file,
        S3_BUCKET,
        path
    )
