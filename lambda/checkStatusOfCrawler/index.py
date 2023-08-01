import json
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import boto3
import os
import time
import uuid


client = boto3.client(service_name='glue', region_name=os.environ['AWS_REGION'],
                    endpoint_url='https://glue.{}.amazonaws.com'.format(os.environ['AWS_REGION']))


def lambda_handler(event, context):
    class CrawlerException(Exception):
        pass

    print('Event : ', event)
    print('Context : ', context)

    event['guid'] = str(uuid.uuid4())

    crawlerName = os.environ['crawlerName']

    print('Clawler Name: {}'.format(crawlerName))

    if 'crawlerName' in event['analytics_job_details']:
        crawlerName = event['analytics_job_details']['crawlerName']
        print('Clawler Name (from event) : {}'.format(crawlerName))

    response = client.get_crawler_metrics(CrawlerNameList=[crawlerName])

    print(response)

    if (response['CrawlerMetricsList'][0]['StillEstimating']):
        print('Clawler In Progress ! (StillEstimating) ')
        raise CrawlerException('Crawler In Progress!')

    elif (response['CrawlerMetricsList'][0]['TimeLeftSeconds'] > 0):
        print('Clawler In Progress ! (TimeLeftSeconds) ')
        raise CrawlerException('Crawler In Progress!')

    else:
        print('Clawler completed successfully ! END !')
        return event