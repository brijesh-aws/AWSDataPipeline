echo 'Creating Analytics Resources...'
aws cloudformation package --template-file analytics.yaml          --output-template-file  analytics-deploy.yaml  --s3-bucket myworking-bucket     --profile brijesh --region us-east-2
aws cloudformation deploy  --template-file analytics-deploy.yaml   --stack-name            Glue-Analytics         --capabilities CAPABILITY_IAM  --profile brijesh --region us-east-2

