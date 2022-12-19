"""Test bootstrap handler."""

import json
from unittest.mock import patch

from handlers import db_handler


@patch("handlers.db_handler.requests")
@patch("handlers.db_handler.boto3")
def test_bootstrap(boto3, requests, database_url):
    """Test Bootstrap."""
    print(boto3)

    class put:
        """Fake requests.put response."""

        reason: str = "All Good"

    requests.put.return_value = put()
    boto3.client.return_value.get_secret_value.side_effect = [
        # connection_params
        {
            "SecretString": json.dumps(
                {
                    "dbname": "postgres",
                    "username": database_url.username,
                    "password": database_url.password,
                    "host": database_url.host,
                    "port": database_url.port,
                }
            )
        },
        # user_params
        {
            "SecretString": json.dumps(
                {
                    "dbname": "eoapi",
                    "username": "eouser",
                    "password": "mypassword",
                    "host": database_url.host,
                    "port": database_url.port,
                }
            )
        },
    ]

    event = {
        "StackId": "eoapi-test",
        "RequestId": "request-00001",
        "LogicalResourceId": "eoapi-test",
        "RequestType": "Create",
        "ResourceProperties": {
            "pgstac_version": "0.6.11",
            "context": True,
            "mosaic_index": True,
            "conn_secret_arn": "secret1",
            "new_user_secret_arn": "secret2",
        },
        "ResponseURL": "http://0.0.0.0",
    }

    class ctx:
        """Fake context object."""

        log_stream_name: str = "something"

    context = ctx()

    db_handler.handler(event, context)
