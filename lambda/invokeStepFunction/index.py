import json
import boto3
import os
import uuid

client_sf = boto3.client( service_name='stepfunctions', region_name=os.environ['AWS_REGION'] )

def lambda_handler(event, context):

    print( 'Event : ' , event )
    print( 'Context : ' , context )

    stateMachine = os.environ['stateMachine']
    bucketName   = os.environ['bucketName']
    key          = os.environ['key']


    try:

        inputData = {
            "detail" : {
                "requestParameters" : {
                    "bucketName" : bucketName,
                    "key"        : key
                }   
            }
        }


        print( "Input Data : {}".format( inputData ) )

        response = client_sf.start_execution(
            stateMachineArn = stateMachine,
            input           = json.dumps( inputData )
        )
        response['guid'] = str( uuid.uuid4() )
        return response


    except Exception as e:
        print("Error ::: ")
        print( e )

