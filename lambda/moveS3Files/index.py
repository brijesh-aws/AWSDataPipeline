import json
import csv
import boto3
import os
import uuid
import datetime as dt
import urllib.parse
from time import sleep

s3_resource = boto3.resource('s3')

s3 = boto3.client( service_name='s3', region_name=os.environ['AWS_REGION'] )



def lambda_handler(event, context):

    class MoveFilesToS3FailedException( Exception ):
        pass

    print('Event : ' , event)
    event['guid'] = str( uuid.uuid4() )

    datestamp = dt.datetime.now().strftime("%m-%d-%Y")
    print('The event triggered date is : ', datestamp)

    timestamp = dt.datetime.now().strftime("%H%M%S")
    print('The event triggered time is : ', timestamp)

    srcBucket = os.environ["moveFilesSrcBucket"]
    destBucket = os.environ["moveFilesDestBucket"]
    path = os.environ["moveFilesPath"]

    bucket = s3_resource.Bucket(name=srcBucket)

    if 'ArchiveFiles' in event:
        if 'SrcBucket' in event['ArchiveFiles']:
            srcBucket = event['ArchiveFiles']['SrcBucket']
        if 'DestBucket' in event['ArchiveFiles']:
            destBucket = event['ArchiveFiles']['DestBucket']
        if 'Path' in event['ArchiveFiles']:
            path = event['ArchiveFiles']['Path']

    try:

        for object in bucket.objects.filter(Prefix=path):

            print('{0}:{1}'.format(bucket.name, object.key))
            key_name = object.key

            if object.key[-1] != "/":
                keyname_s3 = (key_name.replace(' ', '_'))
                keyname_s3 = keyname_s3.lower()
                keyname_s3 = os.path.splitext(keyname_s3)[0] + "_{ds}_{ts}".format(ds=datestamp, ts=timestamp) + \
                             os.path.splitext(keyname_s3)[1]
                copy_source = {
                    'Bucket': srcBucket,
                    'Key': key_name
                }
                s3_resource.meta.client.copy(copy_source, destBucket, keyname_s3)
                s3_object = s3.delete_object(Bucket=srcBucket, Key=key_name)
        return event

    except Exception as err:
        print('This is exception, Error is :', err)
        raise MoveFilesToS3FailedException("Got an exception while archiving files.")

