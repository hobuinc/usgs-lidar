#!/bin/bash


#./create-lambda-function.sh "pdal-info" "pdal_info"
LAMBDA_FUNCTION_NAME="$1"
LAMBDA_METHOD_NAME="$2"

PDAL_LAMBDA_LAYER_ARN=" arn:aws:lambda:us-east-1:163178234892:layer:pdal:8"
LAMDA_EXECUTION_ROLE="lambda_execution"

AWS_PROFILE="hobu"
AWS_REGION="us-east-1"

ROLE=$(aws iam get-role \
    --profile $AWS_PROFILE \
    --role-name $LAMDA_EXECUTION_ROLE )

ROLEARN=$(echo $ROLE |jq .Role.Arn -r)




aws lambda delete-function \
    --function-name $LAMBDA_FUNCTION_NAME \
    --region $AWS_REGION \
    --profile $AWS_PROFILE

rm lambda_function.zip; zip lambda_function.zip lambda_function.py

aws lambda create-function \
    --profile $AWS_PROFILE \
    --region $AWS_REGION \
    --function-name $LAMBDA_FUNCTION_NAME \
    --runtime python3.7 \
    --role $ROLEARN \
    --timeout 200 \
    --memory-size 400 \
    --publish \
    --description "run '$LAMBDA_FUNCTION_NAME' on an S3 or HTTP read-only object" \
    --handler lambda_function.$LAMBDA_METHOD_NAME \
    --layers $PDAL_LAMBDA_LAYER_ARN \
    --zip-file fileb://./lambda_function.zip
#

./scripts/create-resource.sh $LAMBDA_FUNCTION_NAME
