import sys
import datetime
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job

#args = getResolvedOptions(sys.argv, ['JOB_NAME']) 
args = getResolvedOptions(sys.argv, ['JOB_NAME', 'currBucketName', 'confBucketName', 'rawDB', 'curratedDB', 'confDB' ]) 

currBucketName = args['currBucketName']
print( 'Currated Bucket is {}'.format( currBucketName ) )

confBucketName = args['confBucketName']
print( 'Confirm Bucket  is {}'.format( confBucketName ) )

rawDB = args['rawDB']
print( 'Raw DB  is {}'.format( rawDB ) )

curratedDB = args['curratedDB']
print( 'Currated DB  is {}'.format( curratedDB ) )

confDB = args['confDB']
print( 'Confirm DB  is {}'.format( confDB ) )


filePath = "s3://{}/currated/address".format( currBucketName )

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)

job.init(args['JOB_NAME'], args)

def handleMapping(rec):
  rec["curration_date"] = datetime.datetime.now().strftime('%m-%d-%Y')
  return rec


datasource0 = glueContext.create_dynamic_frame.from_catalog( database = rawDB, table_name = "address", transformation_ctx = "datasource0" )

datasource0.printSchema()


applymapping1 = ApplyMapping.apply(
        frame = datasource0, mappings = 
        [
            ("Line1", "string", "Address Line1", "string"), 
            ("Line2", "string", "Address Line2", "string"),
            ("City", "string", "City", "string"),  
            ("State", "string", "State", "string"),
            ("Zipcode", "string", "Zipcode", "string")
        ], 
        transformation_ctx = "applymapping1"
    )

mapped_dyF =  Map.apply( frame = applymapping1, f = handleMapping )
mapped_dyF.printSchema()


#datasink2 = glueContext.write_dynamic_frame.from_options(frame = mapped_dyF, connection_type = "s3", connection_options = {"path": "s3://dcmigrationdatacuration/currated/address"}, format = "json", transformation_ctx = "datasink2")


sink = glueContext.getSink(connection_type="s3", path=filePath, enableUpdateCatalog=True, updateBehavior="UPDATE_IN_DATABASE")

sink.setFormat("json")
sink.setCatalogInfo( catalogDatabase = curratedDB, catalogTableName = "address" )
sink.writeFrame( mapped_dyF )

job.commit()

