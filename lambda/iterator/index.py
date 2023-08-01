import json
import os
import time
import uuid

def lambda_handler(event, context):

    class IteratorException( Exception ):
        pass

    print( 'Event : ' , event )
    print( 'Context : ' , context )

    event['guid'] = str( uuid.uuid4() )

    keyName = os.environ['keyName']

    print('Key Name: {}'.format(keyName))

    try:

        data  = event['analytics_job_details']['iterator']
        index = data['index']

        if keyName in event:
            
            keyValue = event[ keyName ]
            print('Key Value (from event) : {}'.format( keyValue ))
            index = int( keyValue )
            
            event.pop( keyName )
            event.pop( 'job_response' )
            event.pop( 'JobRunId' )

        
        step  = data['step']
        count = data['count']

        print( "Index >> " , index )
        print( "Step  >> " , step  )
        print( "Counter >> " , count )
        
        index = index + step

        print( "Index NEW >> " , index )

        continueRun = index <= count
        print( "Continue ? " , continueRun )

        event['analytics_job_details']['iterator']['index'] = index
        event['analytics_job_details']['iterator']['continueRun'] = continueRun
        event[keyName] = str( index )

        return event
    
    except Exception as e:
        print( "Error in Iterator : ", e )
        raise IteratorException( 'Error in Iterator' )