import json
import boto3
import os
import time
import datetime
import uuid
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from boto3.dynamodb.types import TypeDeserializer

sns = boto3.client( service_name='sns', region_name=os.environ['AWS_REGION'] )

serializer = TypeDeserializer()

def deserialize(data):
    if isinstance(data, list):
       return [deserialize(v) for v in data]

    if isinstance(data, dict):
        try: 
            return serializer.deserialize(data)
        except TypeError:
            return { k : deserialize(v) for k, v in data.iteritems() }
    else:
        return data


def lambda_handler(event, context):

    client = boto3.resource('dynamodb')

    print( 'Event : ' , event )
    print( 'Context : ' , context )

    event['guid'] = str( uuid.uuid4() )

    tableName = os.environ['tableName']
    print( 'Table Name : ' , tableName )

    snsTopic = os.environ['snsTopic']


    table = client.Table( tableName )

    print( "Table Status {}".format( table.table_status) )

    eventName = ''
    comments  = ''
    jobName   = ''

    for record in event['Records']:

        if "NewImage" in record['dynamodb']:

            eventName       = record['dynamodb']['NewImage']['event_name']['S']
            jobName         = record['dynamodb']['NewImage']['job_name']['S']
            datetimeItem    = record['dynamodb']['NewImage']['datetime']['S']
            timestampItem   = record['dynamodb']['NewImage']['timestamp']['N']
            comments        = record['dynamodb']['NewImage']['comments']['S']
            status          = record['dynamodb']['NewImage']['status']['S']
            notify          = record['dynamodb']['NewImage']['notify']['BOOL']

            item = {
                'job_name'      : jobName,
                'event_name'    : eventName,
                'status'        : status,
                'notify'        : notify,
                'datetime'      : datetimeItem,
                'timestamp'     : int(timestampItem),
                'comments'      : comments
            }

            print( "Item : ", item )
            table.put_item( Item= item )

            if( notify ):
                sns.publish(
                    TopicArn    = snsTopic,    
                    Message     = '{} <--> {} <--> {}'.format( jobName, eventName, status ),   
                    Subject     = 'CloudMigrationAnalytics ({}) : {} '.format( jobName, status )
                )

    return event