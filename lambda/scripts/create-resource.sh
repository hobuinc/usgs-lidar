#!/bin/bash

# adapted from https://docs.aws.amazon.com/lambda/latest/dg/with-on-demand-https-example-configure-event-source.html

# useful tidbit https://forums.aws.amazon.com/thread.jspa?threadID=192977&start=25&tstart=0

FNAME="$1"
APINAME="pdal"

echo "FNAME:" $FNAME
ROLE="lambda_execution"
AWS_PROFILE="hobu"
AWS_REGION="us-east-1"

ACCOUNTID=$(aws sts \
    --region $AWS_REGION \
    get-caller-identity| jq '.Account' -r)
echo "ACCOUNTID: " $ACCOUNTID

APIKEY=$(aws apigateway \
    --region $AWS_REGION \
    get-rest-apis| jq '.items[] | select( .name == "'$APINAME'")| .id' -r)

echo "APIKEY: " $APIKEY

ROOTID=$(aws apigateway get-resources \
    --region $AWS_REGION \
    --rest-api-id $APIKEY | jq -r '.items[]| select(.path=="/") | .id')
echo "ROOTID: " $ROOTID

EXISTING_RESOURCE_ID=$(aws apigateway get-resources \
    --region $AWS_REGION \
    --rest-api-id $APIKEY | jq -r '.items[]| select(.pathPart=="'$FNAME'") | .id')

if [ -z "$EXISTING_RESOURCE_ID" ]
then
      echo "\$var is empty"
else
      echo "deleting existing resource"
      aws apigateway delete-resource \
        --rest-api-id $APIKEY \
        --region $AWS_REGION \
        --resource-id $EXISTING_RESOURCE_ID
fi

echo "ROOTID: " $ROOTID

RESOURCEID=$(aws apigateway create-resource \
    --rest-api-id $APIKEY \
    --region $AWS_REGION \
    --path-part "$FNAME" \
    --parent-id $ROOTID | jq -r .id)
echo "RESOURCEID: " $RESOURCEID

METHOD=$(aws apigateway put-method \
    --rest-api-id $APIKEY \
    --region $AWS_REGION \
    --resource-id $RESOURCEID \
    --http-method POST \
    --authorization-type NONE)
echo "METHOD: " $METHOD

FUNCTIONARN=$(aws lambda list-functions \
    --region $AWS_REGION | jq -r '.Functions[] | select (.FunctionName =="'$FNAME'") | .FunctionArn')
echo "FUNCTIONARN: " $FUNCTIONARN

URI="arn:aws:apigateway:$AWS_REGION:lambda:path/2015-03-31/functions/arn:aws:lambda:$AWS_REGION:$ACCOUNTID:function:$FNAME/invocations"
echo "URI: " $URI

METHOD=$(aws apigateway put-integration \
    --rest-api-id $APIKEY \
    --region $AWS_REGION \
    --resource-id $RESOURCEID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "$URI")
echo "METHOD: " $METHOD


if [ "$FNAME" == "pdal-pipeline" ]; then

#aws apigateway put-method-response \
#    --region $AWS_REGION \
#    --rest-api-id $APIKEY \
#    --resource-id $RESOURCEID \
#    --http-method POST \
#    --status-code 200 \
#    --response-models "{\"image/png\": \"Empty\"}"

aws apigateway put-integration-response \
    --region $AWS_REGION \
    --rest-api-id $APIKEY \
    --resource-id $RESOURCEID \
    --http-method POST \
    --status-code 200 \
    --content-handling CONVERT_TO_BINARY


# aws apigateway update-integration-response \
#  --rest-api-id $APIKEY \
#  --resource-id $RESOURCEID \
#  --region $AWS_REGION \
#  --http-method POST \
#  --status-code 200 \
#  --patch-operations op='replace',path='/contentHandling',value='CONVERT_TO_BINARY'

    aws apigateway update-rest-api \
        --rest-api-id $APIKEY \
        --region $AWS_REGION \
        --patch-operations '[{"op" : "replace", "path" : "/binaryMediaTypes/*~1*", "value" : "*~1*"}]'

else

aws apigateway put-method-response \
    --region $AWS_REGION \
    --rest-api-id $APIKEY \
    --resource-id $RESOURCEID \
    --http-method POST \
    --status-code 200  \
    --response-models "{\"application/json\": \"Empty\"}"

aws apigateway put-integration-response \
    --region $AWS_REGION \
    --rest-api-id $APIKEY \
    --resource-id $RESOURCEID \
    --http-method POST \
    --status-code 200 \
    --response-templates "{\"application/json\": \"\"}"
fi





DEPLOYMENTID=$(aws apigateway create-deployment \
    --rest-api-id $APIKEY \
    --region $AWS_REGION \
    --stage-name prod)


#aws lambda remove-permission --function-name "$FNAME" \
#    --region $AWS_REGION \
#    --statement-id "apigateway-prod-2-$FNAME"

ARN="arn:aws:execute-api:$AWS_REGION:$ACCOUNTID:$APIKEY/*/POST/$FNAME"
aws lambda add-permission \
    --function-name $FNAME \
    --region $AWS_REGION \
    --statement-id "apigateway-prod-2-$FNAME" \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "$ARN"
