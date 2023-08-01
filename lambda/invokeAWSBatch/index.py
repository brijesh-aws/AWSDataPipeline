import os
import uuid
import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
import time

#client = boto3.client('batch')

client = boto3.client( service_name='batch', region_name=os.environ['AWS_REGION'] )

def lambda_handler(event, context):

    class AWSBatchException(Exception):
        pass

    time.sleep(5)

    print('Event : ', event)
    print('Context : ', context)

    event['guid'] = str(uuid.uuid4())

    batchJobName = os.environ['batchJobName']
    print( 'BatchJobName (event) : ', batchJobName )

    batchJobDefination = os.environ['batchJobDefination']
    print( 'BatchJobDefination (event) : ', batchJobDefination )

    batchJobQueue = os.environ['batchJobQueue']
    print( 'BatchJobQueue (event) : ', batchJobQueue )

    batchJobMemory = int( os.environ['batchJobMemory'] )
    print( 'BatchJobMemory (event) : ', batchJobMemory )

    batchJobCPUs = int( os.environ['batchJobCPUs'] )
    print( 'BatchJobCPUs (event) : ', batchJobCPUs )

    if 'AWSBatch' in event:
        if 'JobName' in event['AWSBatch']:
            batchJobName = event['AWSBatch']['JobName']
        if 'JobQueue' in event['AWSBatch']:
            batchJobQueue = event['AWSBatch']['JobQueue']
        if 'JobDefination' in event['AWSBatch']:
            batchJobDefination = event['AWSBatch']['JobDefination']
        if 'JobMemory' in event['AWSBatch']:
            batchJobMemory = int( event['AWSBatch']['JobMemory'] )
        if 'JobCPUs' in event['AWSBatch']:
            batchJobCPUs = int( event['AWSBatch']['JobCPUs'] )

    print('BatchJobName : ', batchJobName)
    print('BatchJobDefination : ', batchJobDefination)
    print('BatchJobQueue : ', batchJobQueue)

    try:
        response = client.submit_job(
            jobDefinition = batchJobDefination,
            jobName = batchJobName,
            jobQueue = batchJobQueue,
            containerOverrides={
                'vcpus': batchJobCPUs,
                'memory': batchJobMemory
            }
        )

        print( 'Job Response : ', response )

        if 'AWSBatch' not in event:
            batchData = {
                "JobId" : response['jobId'],
                "JobName": batchJobName,
                "JobQueue": batchJobQueue,
                "JobDefination": batchJobDefination,
                "JobMemory": str(batchJobMemory),
                "JobCPUs": str(batchJobCPUs)
            }
            event['AWSBatch'] = batchData
        else:
            event['AWSBatch']['JobId']    = response['jobId']

        return event

    except Exception as e:
        print('Error:')
        print(e)
        raise AWSBatchException('AWS Batch failed!')

