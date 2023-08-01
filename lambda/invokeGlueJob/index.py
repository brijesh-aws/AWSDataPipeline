import json
import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

import os
import uuid

client = boto3.client(service_name='glue', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):
    class ETLException(Exception):
        pass

    print('Event : ', event)
    print('Context : ', context)

    event['guid'] = str(uuid.uuid4())

    try:

        order = event['order']
        print("Job Key : {}".format(order))

        jobDetailsMain = event["analytics_job_details"]
        print("Job Details Main : {}".format(jobDetailsMain))

        jobDetails = jobDetailsMain['etl_jobs']
        print("Job Details : {}".format(jobDetails))

        etlBuckets = event["analytics_job_details"]['buckets']
        currBucketName = etlBuckets['curr_bucket']
        print("Curration Bucket : {}".format(currBucketName))

        confBucketName = etlBuckets['conf_bucket']
        print("Confirm Bucket : {}".format(confBucketName))

        rawBucketName = etlBuckets['raw_bucket']
        print("Raw Bucket : {}".format(rawBucketName))

        archiveBucket = etlBuckets['archive_bucket']
        print("Archive Bucket : {}".format(archiveBucket))

        envType = jobDetailsMain['envType']
        print("Env Type : {}".format(envType))

        projectName = jobDetailsMain['projectName']
        print("Project Name : {}".format(projectName))

        databases = event["analytics_job_details"]['databases']

        rawDatabase         = databases['raw_database']
        print("Raw Database : {}".format(rawDatabase))

        curatedDatabase     = databases['curated_database']
        print("Curated Database : {}".format(curatedDatabase))

        confirmedDatabase   = databases['confirmed_database']
        print("Confirmed Database : {}".format(confirmedDatabase))


        jobName = jobDetails[order]
        print('Glue ETL Job : ' + jobName)

        event.pop('JobRunId', None)
        event.pop('job_response', None)

        response = client.start_job_run(JobName=jobName, Arguments={"--currBucketName": currBucketName,
                                                                    "--confBucketName": confBucketName,
                                                                    "--rawBucketName": rawBucketName,
                                                                    "--archiveBucket": archiveBucket,
                                                                    "--rawDB": rawDatabase,
                                                                    "--curratedDB": curatedDatabase,
                                                                    "--confDB": confirmedDatabase
                                                                    })
        print("ETL Job ran with ID : {} ".format(response['JobRunId']))

        output = {}
        output['analytics_job_details'] = jobDetailsMain
        output['order'] = order
        output['job_response'] = response

        event['output'] = str(uuid.uuid4())
        return output

    except client.exceptions.ConcurrentRunsExceededException:
        print('ETL Job in progress...')
        raise ETLException('ETL Job In Progress!')

    except Exception as e:
        print('Error:')
        print(e)
        raise e
