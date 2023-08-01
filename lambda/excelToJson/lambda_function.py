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

def lambda_handler(event, context):
	
      datestamp = dt.datetime.now().strftime("%m-%d-%Y")
      print('The event triggered date is : ' , datestamp)
      timestamp = dt.datetime.now().strftime("%H%M%S")
      print('The event triggered time is : ' , timestamp)
      bucket_name = ""
      key_name = ""
      Date="Date"
      destinationBucket = os.environ["destinationBucket"]

      if 'analytics_job_details' in event:
            destinationBucket = event['analytics_job_details']['buckets']['raw_bucket']
            print('Destination Bucket (from event) : {}'.format(destinationBucket))

      print("event info", event)
      try:
            for s3_records in event['Records']:
                  bucket_name = s3_records["s3"]["bucket"]["name"]
                  print ("bucket name", bucket_name)
                  key_name = s3_records["s3"]["object"]["key"]
                  key_name = urllib.parse.unquote_plus( key_name)
                  print("key_name", key_name)
                  s3_object = s3.get_object(Bucket=bucket_name, Key=key_name)
                  file_content = s3_object["Body"].read()
                  copy_source_object = {'Bucket': bucket_name, 'Key': key_name}
                  
                  print('The file fetched from S3 is : ' , key_name)

                  #output_file = (key_name.replace('xlsx', 'json').replace(' ', '_'))
                  output_file = (key_name.replace('xlsx', 'raw').replace(' ', '_'))
                  output_file = output_file.lower()
                  keyname_s3 = os.path.splitext(output_file)[0]+"_{ds}_{ts}.json".format(ds=datestamp, ts=timestamp)
                  read_excel_data = io.BytesIO(file_content)

                  data_frame = pd.read_excel(read_excel_data)
                  total_column = len(data_frame.columns)
                  
                  data_frame.insert(total_column, Date, datestamp)
                  data_frame.reset_index()
                  data_frame_result = data_frame.to_json(orient="records")
                  parsed = json.loads(data_frame_result)
                  json_file_data = json.dumps(parsed,indent=None, separators=(',',':'))
                  json_file_data = str(json_file_data)[1:-1] 
                  json_file_data = (json_file_data.replace("},","}\n"))
                  
                  response = s3.put_object( Bucket=destinationBucket, Key=keyname_s3, Body=json_file_data )

                  print('The target S3 location is :', destinationBucket + '/' + keyname_s3)
                  print('status code is :', response['ResponseMetadata']['HTTPStatusCode'])
                  print('The response metadata is :', response)
                  
                  s3.copy_object( CopySource=copy_source_object, Bucket=os.environ["archiveBucket"], Key=key_name )
                  s3.delete_object( Bucket=bucket_name, Key=key_name )

            print("Return: ", event)
            return event
            
      except Exception as err:
                print('This is exception, Error is :', err)