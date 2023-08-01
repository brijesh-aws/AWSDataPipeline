import json
import boto3
import io
import os
import csv
import uuid
import datetime as dt
import urllib.parse
from time import sleep

s3 = boto3.client("s3")
s3res = boto3.resource('s3')

def lambda_handler(event, context):

      print( "-------------------------------------------------------------------" )
      print( "Batch Run Time : ", dt.datetime.today() )
      print("-------------------------------------------------------------------")

      sourceBucket      = os.environ["sourceBucket"]
      folders           = os.environ["folders"]
      archivePath       = os.environ["archivePath"]

      if 'analytics_job_details' in event:
            sourceBucket = event['analytics_job_details']['buckets']['raw_bucket']

      try:
            folders = folders.split(",")

            for folder in folders:
                  folder = folder.strip()
                  bucket = s3res.Bucket(sourceBucket)
                  objects = bucket.objects.filter( Prefix='{}/'.format(folder) )

                  for obj in objects:
                        path, filename = os.path.split(obj.key)
                        fileS3Obj = s3.get_object(Bucket=sourceBucket, Key=obj.key)
                        fileDateStr       = fileS3Obj["LastModified"].strftime("%Y-%m-%d")
                        todaysDateStr     = dt.datetime.today().strftime("%Y-%m-%d")

                        if fileDateStr == todaysDateStr:
                              print( "***** File Uploaded Today *****" )
                              print( "File Name {}/{}...".format(sourceBucket, obj.key) )
                              print( "File Metadata  : ", fileS3Obj )

                              print( "Archiving today's file..." )
                              s3.copy_object(CopySource={'Bucket': sourceBucket, 'Key': obj.key},
                                             Bucket=sourceBucket,
                                             Key="{}/{}".format(archivePath, obj.key)
                                             )

                              print( "Deleting today's file..." )
                              s3.delete_object( Bucket=sourceBucket, Key=obj.key )
            return event

      except Exception as err:
                print('This is exception, Error is :', err)
                raise err


