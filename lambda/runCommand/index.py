import time
import boto3
import os
import sys

client = boto3.client(service_name='ssm', region_name=os.environ['AWS_REGION'])

def lambda_handler(event, context):

    instance_id = os.environ[ 'EC2InstanceId' ]
    print( 'EC2 Instance ID : ', instance_id )

    response = client.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunShellScript',
        Parameters={
            'commands': [
                "cp /var/log/boot.log /tmp/boot.log "
            ]
        }
    )
    #'if [ -e /etc/hosts ]; then echo -n True; else echo -n False; fi'

    command_id = response['Command']['CommandId']
    print( 'Command ID : ', command_id )

    tries = 0
    output = 'False'

    while tries < 10:
        tries = tries + 1
        try:
            time.sleep(0.5)  # some delay always required...
            result = client.get_command_invocation(
                CommandId=command_id,
                InstanceId=instance_id,
            )
            if result['Status'] == 'InProgress':
                continue
            output = result['StandardOutputContent']
            print( 'Output : ', output )

            break

        except client.exceptions.InvocationDoesNotExist:
            continue

    return output