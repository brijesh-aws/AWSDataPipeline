import json
import csv
import boto3
import os
import uuid
import datetime as dt
import urllib.parse
from time import sleep

s3 = boto3.client('s3')


def lambda_handler(event, context):
    class CsvToJsonFailedException(Exception):
        pass

    print('Event : ', event)

    event['guid'] = str(uuid.uuid4())

    datestamp = dt.datetime.now().strftime("%m-%d-%Y")
    print('The event triggered date is : ', datestamp)

    timestamp = dt.datetime.now().strftime("%H%M%S")
    print('The event triggered time is : ', timestamp)

    bucket_name = ""
    key_name = ""
    Date = 'Date'

    try:

        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        key_name = record['s3']['object']['key']
        key_name = urllib.parse.unquote_plus(key_name)

        copy_source_object = {'Bucket': bucket_name, 'Key': key_name}

        print('The file fetched from S3 is : ', key_name)

        output_file = (key_name.replace('csv', 'json').replace(' ', '_'))
        output_file = output_file.lower()
        keyname_s3 = os.path.splitext(output_file)[0] + "_{ds}_{ts}.json".format(ds=datestamp, ts=timestamp)

        destinationBucket = os.environ["destinationBucket"]

        json_data = []

        s3_object = s3.get_object(Bucket=bucket_name, Key=key_name)

        data = s3_object['Body'].read().decode('utf-8-sig').splitlines()

        for csv_row in csv.DictReader(data):
            csv_row[Date] = datestamp
            json_data.append(csv_row)

        json_file_data = json.dumps(json_data, indent=None, separators=(',', ':'))

        json_file_data = str(json_file_data)[1:-1]

        json_file_data = (json_file_data.replace("},", "}\n"))

        response = s3.put_object(Bucket=destinationBucket, Key=keyname_s3, Body=json_file_data)

        print('The target S3 location is :', destinationBucket + '/' + keyname_s3)
        print('status code is :', response['ResponseMetadata']['HTTPStatusCode'])
        print('The response metadata is :', response)

        s3.copy_object(CopySource=copy_source_object, Bucket=os.environ["archiveBucket"], Key=key_name)
        s3.delete_object(Bucket=bucket_name, Key=key_name)

        return event

    except Exception as err:
        print('This is exception, Error is :', err)

        if "analytics_job_details" in event:
            jobName = event['analytics_job_details']['name']
            print("Job Name is {}".format(jobName))

            raise CsvToJsonFailedException("{}~CSV to JSON conversion failed".format(jobName))