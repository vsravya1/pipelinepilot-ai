import os
from dotenv import load_dotenv
from google.cloud import bigquery
from services.mongodb_service import get_orders

load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
BIGQUERY_DATASET = os.getenv("BIGQUERY_DATASET", "pipelinepilot_demo")
BIGQUERY_TABLE = os.getenv("BIGQUERY_TABLE", "raw_orders")


def load_orders_to_bigquery():
    if not GOOGLE_CLOUD_PROJECT:
        return {
            "status": "Skipped",
            "message": "GOOGLE_CLOUD_PROJECT is missing",
            "rows_loaded": 0,
            "table": None
        }

    rows = get_orders()

    if not rows:
        return {
            "status": "Skipped",
            "message": "No MongoDB orders found to load",
            "rows_loaded": 0,
            "table": None
        }

    client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)

    dataset_id = f"{GOOGLE_CLOUD_PROJECT}.{BIGQUERY_DATASET}"
    table_id = f"{dataset_id}.{BIGQUERY_TABLE}"

    dataset = bigquery.Dataset(dataset_id)
    dataset.location = "US"

    client.create_dataset(dataset, exists_ok=True)

    schema = [
        bigquery.SchemaField("order_id", "STRING"),
        bigquery.SchemaField("customer_id", "STRING"),
        bigquery.SchemaField("order_amount", "FLOAT"),
        bigquery.SchemaField("order_status", "STRING"),
        bigquery.SchemaField("created_at", "STRING"),
    ]

    table = bigquery.Table(table_id, schema=schema)
    client.delete_table(table_id, not_found_ok=True)
    client.create_table(table)

    clean_rows = []

    for row in rows:
        clean_rows.append({
            "order_id": str(row.get("order_id", "")),
            "customer_id": str(row.get("customer_id", "")),
            "order_amount": float(row.get("order_amount", 0)),
            "order_status": str(row.get("order_status", "")),
            "created_at": str(row.get("created_at", ""))
        })

    job_config = bigquery.LoadJobConfig(
    schema=schema,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
    )

    load_job = client.load_table_from_json(
        clean_rows,
        table_id,
        job_config=job_config
    )

    load_job.result()

    table_info = client.get_table(table_id)

    return {
        "status": "Success",
        "message": f"Loaded {table_info.num_rows} MongoDB order records into BigQuery using a load job.",
        "rows_loaded": table_info.num_rows,
        "table": table_id
    }