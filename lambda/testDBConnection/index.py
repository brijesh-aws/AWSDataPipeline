import pyodbc
import boto3
import base64
import os
import json
from botocore.exceptions import ClientError

secret_name = "atadataPassword"
region_name = "us-east-1"

session = boto3.session.Session()
smclient = session.client(
    service_name='secretsmanager',
    region_name=os.environ['AWS_REGION']
)


def lambda_handler(event, context):
    server = os.environ['server']
    database = os.environ['database']
    username = os.environ['username']
    password = ''

    get_secret_value_response = smclient.get_secret_value(SecretId=secret_name)

    password = json.loads(get_secret_value_response['SecretString'])

    password = password[secret_name]

    print("Password : ", password)

    cnxn = pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = cnxn.cursor()

    print(cursor.execute('select GETUTCDATE()').fetchall())
    cursor.execute('SELECT * from ATADATA_DB.dbo.DATABASE_INSTANCES where IS_DELETE=0')
    row2 = cursor.fetchone()

    while row2:
        results = row2[0]
        row2 = cursor.fetchone()

    print("Test Result : ", results)

# lambda_handler( 'test', '1' )


