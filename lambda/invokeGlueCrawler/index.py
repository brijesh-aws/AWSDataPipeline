import json
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import boto3
import os
import uuid

#client = boto3.client('glue')

client = boto3.client( service_name='glue', region_name=os.environ['AWS_REGION'] )


def lambda_handler(event, context):
    print("Starting Glue Crawler - CloudMgrAnalyticsCrawlerRaw...")

    print( 'Event : ' , event )
    print( 'Context : ' , context )

    event['guid'] = str( uuid.uuid4() )

    crawlerName = os.environ['crawlerName']

    print('Clawler Name: {}'.format(crawlerName))

    if 'crawlerName' in event['analytics_job_details']:
        crawlerName = event['analytics_job_details']['crawlerName']
        print('Clawler Name (from event) : {}'.format(crawlerName))

    class CrawlerRunningException(Exception):
        pass

    try:
        print( 'Starting Crawler...' )
        client.start_crawler( Name=crawlerName )
        print('Starting Crawler...Done!')

        return event

    except client.exceptions.CrawlerRunningException:
        print('Crawler in progress...')
        raise CrawlerRunningException('Crawler In Progress!')

    except Exception as e:
        print('Problem while invoking crawler')
        print( 'Error:' )
        print( e )