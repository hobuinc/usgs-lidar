#!/bin/bash

# adapted from https://docs.aws.amazon.com/lambda/latest/dg/with-on-demand-https-example-configure-event-source.html

# useful tidbit https://forums.aws.amazon.com/thread.jspa?threadID=192977&start=25&tstart=0

FNAME="$1"
APINAME="pdal"

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

# delete all the APIs with the name $APINAME
# you can only delete one API per minute, so we
# have to wait if there are more with the same name
for k in $APIKEY; do
    echo "Deleting API with id then waiting 60 seconds: " $k
    aws apigateway delete-rest-api \
        --rest-api-id $k \
        --region $AWS_REGION ;
    sleep 61;

done;


APIKEY=$(aws apigateway create-rest-api \
    --name $APINAME \
    --region $AWS_REGION \
    --endpoint-configuration types=REGIONAL \
    --api-key-source HEADER | jq -r .id)

echo "APIKEY: " $APIKEY

