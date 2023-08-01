echo 'Creating Common Resources...'
aws cloudformation package --template-file common.yaml          --output-template-file  common-deploy.yaml    --s3-bucket    myworking-bucket  --profile brijesh --region us-east-2
aws cloudformation deploy  --template-file common-deploy.yaml   --stack-name            Glue-Analytics-Common --capabilities CAPABILITY_IAM  --profile brijesh --region us-east-2
