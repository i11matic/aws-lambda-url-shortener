import amazondax
import boto3
import os
import json
from secrets import token_urlsafe

dynamodb_endpoint_url = os.getenv("DYNAMODB_ENDPOINT_URL")
dax_endpoint = os.getenv("DAX_ENDPOINT")
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
        if dax_endpoint:
            with amazondax.AmazonDaxClient.resource(
                endpoint_url=dax_endpoint
            ) as dax:
                short_url = create_short_url(body["url"], dax, table_name)
        else:
            short_url = create_short_url(body["url"], dynamodb, table_name)
        response = dict()
        response["statusCode"] = 200
        response["body"] = json.dumps({"shortlink": short_url})
        return response

    if event["requestContext"]["http"]["method"] == "GET":
        if dax_endpoint:
            with amazondax.AmazonDaxClient.resource(
                endpoint_url=dax_endpoint
            ) as dax:
                url = get_original_url(
                    event["pathParameters"]["proxy"],
                    dax,
                    table_name,
                )
        else:
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
