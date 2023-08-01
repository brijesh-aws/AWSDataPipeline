import json
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import boto3
import os
import time
import datetime
import uuid


def lambda_handler(event, context):

    client = boto3.resource('dynamodb')

    print( 'Event : ' , event )
    print( 'Context : ' , context )

    tableName = os.environ['tableName']
    print( 'Table Name : ' , tableName )


    table = client.Table( tableName )

    print( "Table Status {}".format( table.table_status) )

    eventName = ''
    comments  = ''
    jobName   = ''

    records = event['Records']
    print( 'Records : ', records )

    record = records[0]
    print( 'Record 0 : ', record )

    eventName = record['attributes']['MessageGroupId']
    print( 'Event Name : ', eventName )

    data = record['body']
    print( 'Data : ', data )

    dataObj = json.loads( data )

    status = "SUCCESSED"
    notify = False

    if 'Cause' in dataObj:

        print( "Logging error..." )
        cause = json.loads( dataObj['Cause'] )
        
        comments = cause['errorMessage']
        print( 'Comments : {} '.format( comments ) )

        jobName  = comments.split('~')[0]
        jobName = jobName.replace( '_raw', '' )
        jobName = jobName.replace( '_conf', '' )

        print( 'Job Name : {} '.format( jobName ) )

        comments = comments.replace( jobName, '' )
        status   = "FAILED"
        notify   = True
    
    else:

        jobName = dataObj['analytics_job_details']['name']
        comments = ""

        if "job_response" in dataObj:
            
            if( eventName != "ETL-Jobs-Completed" ):
                comments = "Job {} : ".format( dataObj['order'] )
                comments = comments + dataObj['job_response']['JobRunId']

                jobOrder = dataObj['order']
                eventName = eventName + "~" + jobOrder + "~" + dataObj['analytics_job_details']['etl_jobs'][ jobOrder ]

    
    
    if( eventName == 'ETL-Job-has-been-Initialized' ):
        try:
            items = table.query(
                    ProjectionExpression = "#job_name, event_name",
                    ExpressionAttributeNames={"#job_name": "job_name"},
                    KeyConditionExpression=Key('job_name').eq(jobName)
            )
            print( "Items : ", items )

            for item in items['Items']:
                table.delete_item(
                    Key={
                        'job_name' : item['job_name'],
                        'event_name' : item['event_name']
                    }
                )
        except ClientError as e:
            print( 'Not able to delete items!' )
            print(e)
    

    if( eventName == 'ETL-Jobs-Completed' ):
        notify = True


    item = {
        'job_name'      : jobName,
        'event_name'    : eventName,
        'status'        : status,
        'notify'        : notify,
        'datetime'      : datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'timestamp'     : round( time.time() ),
        'comments'      : comments
    }

    print( "Item : ", item )
    table.put_item( Item= item )

    event['guid'] = str( uuid.uuid4() )
    return event