import azure.functions as func
import logging
import json
import os
from azure.data.tables import TableServiceClient
from azure.core.exceptions import ResourceNotFoundError

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TABLE_NAME = "VisitorCount"
PARTITION_KEY = "resume"
ROW_KEY = "counter"


def increment_and_get_count(table_client):
    """
    Core business logic: read the current count from the table,
    increment it by 1, save it back, and return the new count.

    Separated from the HTTP handler so it can be tested without
    needing a real HTTP request or a real Azure connection —
    tests can pass in a fake/mock table_client instead.
    """
    try:
        entity = table_client.get_entity(partition_key=PARTITION_KEY, row_key=ROW_KEY)
        new_count = entity["count"] + 1
        entity["count"] = new_count
        table_client.update_entity(entity)
    except ResourceNotFoundError:
        new_count = 1
        entity = {
            "PartitionKey": PARTITION_KEY,
            "RowKey": ROW_KEY,
            "count": new_count,
        }
        table_client.create_entity(entity)

    return new_count


@app.route(route="visitorcounter", methods=["GET"])
def VisitorCounter(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("VisitorCounter function triggered.")

    connection_string = os.environ["TABLE_CONNECTION_STRING"]

    table_service = TableServiceClient.from_connection_string(connection_string)
    table_client = table_service.get_table_client(TABLE_NAME)

    new_count = increment_and_get_count(table_client)

    response_body = json.dumps({"count": new_count})

    return func.HttpResponse(
        response_body,
        status_code=200,
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"},
    )
