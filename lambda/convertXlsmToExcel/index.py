import boto3
import datetime as dt
import os
import pandas as pd
import io
import json

s3 = boto3.client("s3")
s3res = boto3.resource('s3')


def read_config_file(configfile):
    config_data = json.load(open(configfile))
    data = json.dumps(config_data)
    dict_json = json.loads(data)
    return dict_json


def lambda_handler(event, context):

    class FilesNotFoundException(Exception):
        pass

    datestamp = dt.datetime.now().strftime("%m-%d-%Y")
    timestamp = dt.datetime.now().strftime("%H%M%S")

    sourceBucket = os.environ["sourceBucket"]
    # sourcePath = os.environ["sourcePath"]
    destinationBucket = sourceBucket
    destinationPath = os.environ["destinationPath"]
    # archivePath = os.environ["archivePath"]
    # destinationKey = destinationPath + "_{ds}_{ts}.xlsx".format(ds=datestamp, ts=timestamp)
    ctbConfigData = read_config_file("config.json")
    totalFiles = 0
    try:
        for obj in s3.list_objects_v2(Bucket=sourceBucket, Prefix="input/")['Contents']:
            print(obj['Key'])
            if obj['Key'].endswith('.xlsm'):
                xlsmFile = s3.get_object(Bucket=sourceBucket, Key=obj['Key'])
                xlsmData = xlsmFile['Body'].read()
                copy_source_object = {'Bucket': sourceBucket, 'Key': obj['Key']}
                fileName = obj['Key'].partition('.')
                destinationKey = fileName[0] + "_{ds}_{ts}.xlsx".format(ds=datestamp, ts=timestamp)
                archivePath = "archive/" + obj['Key']
                df = pd.read_excel(io.BytesIO(xlsmData), encoding='utf-8', sheetname=None)
                with io.BytesIO() as output:
                    with pd.ExcelWriter(output) as writer1:
                        for i in df.keys():
                            df1 = df[i]
                            df1.to_excel(writer1, sheet_name=i, index=False)
                    s3res.Bucket(destinationBucket).put_object(Key=destinationKey,
                                                               Body=output.getvalue())
                    s3.copy_object(CopySource=copy_source_object, Bucket=sourceBucket, Key=archivePath)
                    s3.delete_object(Bucket=sourceBucket, Key=obj['Key'])
                    totalFiles = totalFiles + 1
        print("Total files processed : ", totalFiles)
        if totalFiles == 0:
            error = 'No Files Found for XLSM To XLSX Conversion'
            print("Error : ", error)
            raise FilesNotFoundException(error)

        return event

    except FilesNotFoundException as ferr:
        print('File not found exception, Error is :', ferr)
        raise ferr

    except Exception as err:
        print('Exception, Error is :', err)
        raise err
