import json
import csv
import boto3
import os
import uuid
import datetime as dt
import urllib.parse
from time import sleep

import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.errors as errors
import azure.cosmos.documents as documents
import azure.cosmos.http_constants as http_constants
from azure.cosmos import exceptions, CosmosClient, PartitionKey


kinesis = boto3.client( service_name='kinesis', region_name=os.environ['AWS_REGION'] )

s3 = boto3.client( service_name='s3', region_name=os.environ['AWS_REGION'] )

URL = os.environ["dbUrl"]
KEY = os.environ["dbKey"]
DATABASE_ID = os.environ["dbName"]
destinationBucket = os.environ["destinationBucket"]

CONTAINER_NAME = 'workItems'
keyname_s3 = 'json/test/workItems-{}.json'

client = cosmos_client.CosmosClient( URL, {'masterKey': KEY} )
print( 'Client :', client )

database  = client.get_database_client( DATABASE_ID )
print( 'Database :', database )

container = database.get_container_client( CONTAINER_NAME )
print( container )


def upload( json_data, counter ):
    json_file_data = json.dumps( json_data, indent=None )
        
    json_file_data = str(json_file_data)[1:-1] 

    json_file_data = (json_file_data.replace("},","}\n"))

    s3.put_object( Bucket=destinationBucket, Key=keyname_s3.format( counter ), Body=json_file_data )


def lambda_handler(event, context):

    class CosmosDBtoS3FailedException( Exception ):
        pass

    print('Event : ' , event)

    event['guid'] = str( uuid.uuid4() )

    try:

        totalWorkitems = 0
        counter = 1
        json_data = []

        for item in container.read_all_items():
            totalWorkitems = totalWorkitems + 1
            kinesis.put_record(
                    StreamName= "test",
				    Data= json.dumps( item ),
                    PartitionKey= "workItems"
                )
            kinesis.put_record(
                    StreamName= "test",
				    Data= "\n",
                    PartitionKey= "workItems"
                )

        print('\n')
        print('\n')
        print( "Total Workitems : ", totalWorkitems )    

        
        return event

    except Exception as err:

        print('This is exception, Error is :', err)
        