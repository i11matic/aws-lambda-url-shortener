import boto3
import os
from secrets import token_urlsafe

dynamodb_endpoint_url = os.getenv(
    "DYNAMODB_ENDPOINT_URL", "http://localhost:8000"
)
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
            "ReadCapacityUnits": os.getenv("DYNAMODB_READ_CAPACITY", 1),
            "WriteCapacityUnits": os.getenv("DYNAMODB_WRITE_CAPACITY", 1),
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
        create_table(dynamodb)

    if event["httpMethod"] == "POST":
        short_url = create_short_url(
            event["body"]["url"], dynamodb, table_name
        )
        return {
            "statusCode": 200,
            "body": {
                "shortlink": short_url,
            },
        }

    if event["httpMethod"] == "GET":
        url = get_original_url(
            event["requestContext"]["path"].strip("/"),
            dynamodb,
            table_name,
        )
        return {"statusCode": 302, "headers": {"Location": url}}
