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
    class InvalidInputException(Exception):
        pass

    class EntityNotFoundException(Exception):
        pass

    class InternalServiceException(Exception):
        pass

    class OperationTimeoutException(Exception):
        pass

    class ETLJobRunningException(Exception):
        pass

    class ETLJobFailedException(Exception):
        pass

    print('Event : ', event)
    print('Context : ', context)

    event['guid'] = str(uuid.uuid4())

    # jobName = os.environ['jobName']
    # print('ETL Job Name: {}'.format(jobName))

    order = event['order']
    print("Job Key : {}".format(order))

    jobDetails = event["analytics_job_details"]['etl_jobs']

    print("Job Details : {}".format(jobDetails))

    jobName = jobDetails[order]
    print('Glue ETL Job : ' + jobName)

    jobRunId = event['job_response']['JobRunId']
    print('ETL Job Run ID : ' + jobRunId)

    try:

        response = client.get_job_run(JobName=jobName, RunId=jobRunId)

        print(response)

        status = response['JobRun']['JobRunState']

        if (status == 'STARTING' or status == 'RUNNING' or status == 'STOPPING'):
            raise ETLJobRunningException("{}~ETL Job is running".format(jobName))

        elif (status == 'FAILED'):
            raise ETLJobFailedException('{}~ETL Job failed'.format( event['analytics_job_details']['name'] ))

        elif (status == 'STOPPED' or status == 'SUCCEEDED'):
            print("ETL Job with ID '{}' completed successfully!".format(jobName))
            return event


    except client.exceptions.InvalidInputException:
        print('ETL Job Invalid Input!')
        raise InvalidInputException('{}~Invalid Input'.format( event['analytics_job_details']['name'] ))

    except client.exceptions.EntityNotFoundException:
        print('ETL Job Invalid Input!')
        raise EntityNotFoundException('{}~Entity Not Found'.format( event['analytics_job_details']['name'] ))

    except client.exceptions.InternalServiceException:
        print('ETL Job Invalid Input!')
        raise InternalServiceException('{}~Internal Service Error'.format( event['analytics_job_details']['name'] ))

    except client.exceptions.OperationTimeoutException:
        print('ETL Job Invalid Input!')
        raise OperationTimeoutException('{}~ETL Job Timeoutout'.format( event['analytics_job_details']['name'] ))

    except Exception as e:
        print('Error:')
        print(e)
        raise e

