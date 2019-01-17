#!/bin/bash


LAMBDA_FUNCTION_NAME="$1"

AWS_PROFILE="hobu"
AWS_REGION="us-east-1"


rm lambda_function.zip; zip lambda_function.zip lambda_function.py

aws lambda update-function-code \
    --profile $AWS_PROFILE \
    --region $AWS_REGION \
    --function-name $LAMBDA_FUNCTION_NAME \
    --publish \
    --zip-file fileb://./lambda_function.zip
#

