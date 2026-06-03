def generate_transformation(dataset, target):
    sql = f"""
CREATE OR REPLACE TABLE {target} AS
SELECT
    order_id,
    customer_id,
    CAST(order_amount AS DECIMAL(10,2)) AS order_amount,
    LOWER(order_status) AS order_status,
    created_at AS order_timestamp,
    CURRENT_TIMESTAMP AS ingestion_timestamp
FROM raw_{dataset};
"""

    validation_rules = [
        "order_id must be unique",
        "customer_id should not be null",
        "order_amount must be greater than or equal to 0",
        "created_at must be a valid timestamp",
        "order_status should be normalized to lowercase"
    ]

    return {
        "summary": f"Generated analytics transformation and validation rules for {dataset}.",
        "target": target,
        "sql": sql.strip(),
        "validation_rules": validation_rules
    }