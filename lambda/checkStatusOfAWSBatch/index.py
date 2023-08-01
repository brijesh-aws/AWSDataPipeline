import os
import uuid
import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

client = boto3.client(service_name='batch', region_name=os.environ['AWS_REGION'] )


def lambda_handler(event, context):

    class AWSBatchRunning(Exception):
        pass
    class AWSBatchPending(Exception):
        pass
    class AWSBatchFailed(Exception):
        pass
    class AWSBatchJobNotFound(Exception):
        pass

    print('Event : ', event)
    print('Context : ', context)

    event['guid'] = str(uuid.uuid4())

    batchJobQueue = os.environ['batchJobQueue']
    print('BatchJobQueue (event) : ', batchJobQueue)

    if 'AWSBatch' in event:
        if 'JobQueue' in event['AWSBatch']:
            batchJobQueue = event['AWSBatch']['JobQueue']

    print("------------------------------------------------------------")
    print('BatchJobQueue : ', batchJobQueue)

    try:

        batchJobId = ''

        if 'AWSBatch' in event:
            if 'JobId' in event['AWSBatch']:
                batchJobId = event['AWSBatch']['JobId']
            else:
                raise AWSBatchJobNotFound('AWS Batch Job Not Found!')
        else:
            raise AWSBatchJobNotFound('AWS Batch Job Not Found!')

        print( 'Batch Job ID >> ', batchJobId )

        # Check if Job is Running
        jobs = client.list_jobs( jobQueue = batchJobQueue, jobStatus='RUNNING' )

        for data in jobs['jobSummaryList']:
            if batchJobId == data['jobId']:
                raise AWSBatchRunning('AWS Batch is Running! ({})'.format( batchJobId ) )

        # Check if Job Failed
        jobs = client.list_jobs( jobQueue = batchJobQueue, jobStatus='FAILED' )

        for data in jobs['jobSummaryList']:
            if batchJobId == data['jobId']:
                raise AWSBatchFailed('{}~AWS Batch ID : {}'.format( event["analytics_job_details"]["name"], batchJobId ) )

        # Check if Job completed Successfully
        jobs = client.list_jobs( jobQueue = batchJobQueue, jobStatus='SUCCEEDED' )

        for data in jobs['jobSummaryList']:
            if batchJobId == data['jobId']:
                return event

        print( 'Job Response : ', jobs )

        error = 'AWS Batch is Pending! ({})'.format(batchJobId)
        raise AWSBatchPending( error )

    except Exception as e:
        print('Error:')
        print(e)
        raise e

