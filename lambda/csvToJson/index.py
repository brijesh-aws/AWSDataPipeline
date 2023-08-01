import time
import boto3
import os
import sys
import json
import csv
import uuid
import datetime as dt
import urllib.parse
from time import sleep

s3 = boto3.client("s3")
s3res = boto3.resource('s3')

def lambda_handler(event, context):
    class CsvToJsonFailedException(Exception):
        pass
    class CSVToJsonFilesNotFoundException(Exception):
            pass

    try:

        print('Event : ', event)

        event['guid'] = str(uuid.uuid4())

        datestamp = dt.datetime.now().strftime("%m-%d-%Y")
        print('The event triggered date is : ', datestamp)

        timestamp = dt.datetime.now().strftime("%H%M%S")
        print('The event triggered time is : ', timestamp)

        sourceBucket        = os.environ["sourceBucket"]
        sourcePath          = os.environ["sourcePath"]
        destinationBucket   = os.environ["destinationBucket"]
        destinationPath     = os.environ["destinationPath"]
        archivePath         = os.environ["archivePath"]
        fileFilter          = os.environ["fileFilter"]

        excelFile = ""
        totalFiles = 0

        print( "Bucket : ", sourceBucket )

        #if 'analytics_job_details' in event:
        #    destinationBucket = event['analytics_job_details']['buckets']['raw_bucket']
        #    print('Destination Bucket (from event) : {}'.format(destinationBucket))

        #    if 'fileFilter' in event['analytics_job_details']:
        #          fileFilter = event['analytics_job_details']['fileFilter']
        #          print( 'File Filter (from event) : {}'.format( fileFilter ) )

        bucket = s3res.Bucket(sourceBucket)
        objects = bucket.objects.filter(Prefix='{}/'.format(sourcePath))

        for obj in objects:
            path, filename = os.path.split(obj.key)
            print( "PATH : ", path )
            print( "Filename : ", filename )
            print( "Obj.key : ", obj.key )

            if not filename.endswith( ".csv" ):
                continue

            s3_object = s3.get_object(Bucket=sourceBucket, Key=obj.key)
            data = s3_object['Body'].read().decode('utf-8-sig').splitlines()

            jsonData = []

            for csv_row in csv.DictReader(data):
                csv_row['record_created_on'] = datestamp
                jsonData.append(csv_row)

            jsonData = json.dumps(jsonData, indent=None, separators=(',', ':'))
            jsonData = str(jsonData)[1:-1]
            jsonData = jsonData.replace("},", "}\n")

            jsonFile = (obj.key).replace('csv', 'json').lower()
            jsonKey = os.path.splitext(jsonFile)[0] + "_{ds}_{ts}.json".format(ds=datestamp, ts=timestamp)

            response = s3.put_object(Bucket=destinationBucket, Key=jsonKey, Body=jsonData)

            print("S3 RESPONSE : ", response)

            if response["ResponseMetadata"]["HTTPStatusCode"] == 200:

                print( "CSV to JSON conversion has been completed successfully." )
                # Archive the Excel Data file
                print("Archiving File : {}/{}.".format(destinationBucket, "{}/{}".format( archivePath, obj.key ) ) )

                s3.copy_object(   CopySource={ 'Bucket': sourceBucket, 'Key': obj.key },
                                    Bucket=destinationBucket,
                                    Key="{}/{}".format( archivePath, obj.key )
                                )

                # Delete the Source Excel Data file
                s3.delete_object(Bucket=sourceBucket, Key=obj.key)

                totalFiles = totalFiles + 1
            else:
                error = '{}~CSV To JSON Conversion failed for the file {}.'.format( event["analytics_job_details"]["name"], obj.key )
                print( "Error : ", error )
                raise CSVToJsonFilesNotFoundException( error )

        print( "Total files processed : ", totalFiles )

        if( totalFiles == 0 ):
                error = '{}~No Files Found for CSV To JSON Conversion'.format( event["analytics_job_details"]["name"] )
                print( "Error : ", error )
                raise CSVToJsonFilesNotFoundException( error )

        return event

    except CSVToJsonFilesNotFoundException as notFound:
        raise CSVToJsonFilesNotFoundException( notFound )

    except Exception as err:
        print('This is exception, Error is :', err)

        if "analytics_job_details" in event:
            jobName = event['analytics_job_details']['name']
            print("Job Name is {}".format(jobName))

            raise CsvToJsonFailedException("{}~CSV to JSON conversion failed".format(jobName))

