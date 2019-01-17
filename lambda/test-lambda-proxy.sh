
API="obyg4wcjtb"


read -d '' JSON << END
{
  "pipeline": [
    {
      "type": "readers.ept",
      "filename": "http://na.entwine.io/nyc",
      "bounds": "([-8242669, -8242529], [4966549, 4966674])"
    },
    {
      "type":"filters.range",
      "limits":"Classification![7:7]"
    },
    {
      "type":"filters.assign",
      "assignment":"Classification[:]=0"
    },
    {
      "type":"filters.smrf",
      "ignore":"Classification[7:7]"
    },
    {
      "resolution": 2.0,
      "filename":"/tmp/dtm.tif"
    }
  ]
}
END

curl -s -X POST \
  'https://'$API'.execute-api.us-east-1.amazonaws.com/prod/pdal-pipeline' \
  -H "Accept: image/png" \
  -d "$JSON" -o o.png

echo $RESPONSE
