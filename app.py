import boto3
import os
import json
from secrets import token_urlsafe

dynamodb_endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
dynamodb = boto3.resource("dynamodb", endpoint_url=dynamodb_endpoint_url)
dynamodb_client = boto3.client("dynamodb", endpoint_url=dynamodb_endpoint_url)
table_name = os.getenv("DYNAMODB", "url-shortener")


def create_table(dynamodb, table_name):
    dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {"AttributeName": "shortUrl", "KeyType": "HASH"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "shortUrl", "AttributeType": "S"},
        ],
        ProvisionedThroughput={
            "ReadCapacityUnits": 1,
            "WriteCapacityUnits": 1,
        },
    )


def create_short_url(url, dynamodb, table_name):
    table = dynamodb.Table(table_name)
    short_url = token_urlsafe(nbytes=5)
    table.put_item(Item={"shortUrl": short_url, "orginalUrl": url})
    return short_url


def get_original_url(short_url, dynamodb, table_name):
    table = dynamodb.Table(table_name)
    item = table.get_item(Key={"shortUrl": short_url})
    return item["Item"]["orginalUrl"]


def lambda_handler(event, context):
    if table_name not in dynamodb_client.list_tables()["TableNames"]:
        create_table(dynamodb, table_name)

    if event["requestContext"]["http"]["method"] == "POST":
        body = json.loads(event["body"])
        short_url = create_short_url(body["url"], dynamodb, table_name)
        response = dict()
        response["statusCode"] = 200
        response["body"] = json.dumps({"shortlink": short_url})
        return response
        # return json.dumps(
        #     {
        #         "statusCode": 200,
        #         "body": {
        #             "shortlink": short_url,
        #         },
        #     }
        # )
    if event["requestContext"]["http"]["method"] == "GET":
        url = get_original_url(
            event["pathParameters"]["proxy"],
            dynamodb,
            table_name,
        )
        response = dict()
        response["statusCode"] = 302
        response["body"] = json.dumps(dict())
        response["headers"] = {"Location": url}
        return response
        # return json.dumps(
        #     {
        #         "statusCode": 301,
        #         "headers": {"Location": url},
        #         "Access-Control-Allow-Origin": "*",
        #     }
        # )
