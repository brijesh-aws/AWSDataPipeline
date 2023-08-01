import json
import boto3
import pandas as pd
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

      class ExcelToJsonException(Exception):
            pass
      class ExcelToJsonFilesNotFoundException(Exception):
            pass

      excelFile = ""
      totalFiles = 0
      datestamp = dt.datetime.now().strftime("%Y-%m-%d")
      timestamp = dt.datetime.now().strftime("%H%M%S")

      sourceBucket      = os.environ["sourceBucket"]
      sourcePath        = os.environ["sourcePath"]
      destinationBucket = sourceBucket #os.environ["destinationBucket"]
      destinationPath   = os.environ["destinationPath"]
      archivePath       = os.environ["archivePath"]
      fileFilter        = os.environ["fileFilter"]

      if 'analytics_job_details' in event:
            destinationBucket = event['analytics_job_details']['buckets']['raw_bucket']
            print('Destination Bucket (from event) : {}'.format(destinationBucket))

            if 'fileFilter' in event['analytics_job_details']:
                  fileFilter = event['analytics_job_details']['fileFilter']
                  print( 'File Filter (from event) : {}'.format( fileFilter ) )

      try:
            bucket = s3res.Bucket(sourceBucket)
            objects = bucket.objects.filter( Prefix='{}/'.format(sourcePath) )

            for obj in objects:
                  path, filename = os.path.split(obj.key)
                  if not filename.endswith( fileFilter ):
                        continue

                  excelFile = obj.key
                  print( "Downloading, {}/{}...".format( sourceBucket, excelFile ) )

                  # Reading S3 File
                  fileData = s3.get_object( Bucket=sourceBucket, Key=excelFile )["Body"].read()

                  # Convert to JSON
                  data_frame = pd.read_excel( io.BytesIO( fileData ), converters={'Date': str} )
                  data_frame.insert( len(data_frame.columns), 'record_created_on', datestamp )
                  data_frame.reset_index()
                  data_frame_result = data_frame.to_json(orient="records")
                  parsed = json.loads(data_frame_result)

                  # Added to reformate the data for Glue/Athena compatible
                  json_file_data = json.dumps(parsed,indent=None, separators=(',',':'))
                  json_file_data = str(json_file_data)[1:-1]
                  json_file_data = (json_file_data.replace("},","}\n"))

                  # Uploading JSON Data file
                  outputFile = excelFile.replace( sourcePath, destinationPath ).replace(' ', '_').lower()
                  outputFileKey = os.path.splitext( outputFile )[0]+"_{ds}_{ts}.json".format( ds=datestamp, ts=timestamp )

                  print( "JSON Data File Path : {}/{}.".format( destinationBucket, outputFileKey ) )
                  response = s3.put_object( Bucket=destinationBucket, Key=outputFileKey, Body=json_file_data )

                  print("S3 RESPONSE : ", response)

                  if response["ResponseMetadata"]["HTTPStatusCode"] == 200:

                        print( "Excel to JSON conversion has been completed successfully." )
                        # Archive the Excel Data file
                        print("Archiving File : {}/{}.".format(destinationBucket, excelFile))
                        s3.copy_object(   CopySource={'Bucket': sourceBucket, 'Key': excelFile},
                                          Bucket=destinationBucket,
                                          Key="{}/{}".format( archivePath, excelFile )
                                      )

                        # Delete the Source Excel Data file
                        s3.delete_object(Bucket=sourceBucket, Key=excelFile)

                        totalFiles = totalFiles + 1
                  else:
                        error = '{}~Excel To JSON Conversion failed for the file {}.'.format( event["analytics_job_details"]["name"], excelFile )
                        print( "Error : ", error )
                        raise ExcelToJsonException( error )

            print( "Total files processed : ", totalFiles )

            if( totalFiles == 0 ):
                  error = '{}~No Files Found for Excel To JSON Conversion'.format( event["analytics_job_details"]["name"] )
                  print( "Error : ", error )
                  raise ExcelToJsonFilesNotFoundException( error )

            return event

      except Exception as err:
                print('This is exception, Error is :', err)
                raise err


