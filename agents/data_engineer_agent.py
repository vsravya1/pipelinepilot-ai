from services.gemini_service import generate_data_engineer_plan


def generate_transformation(dataset, target, onboarding_mode=None, goal=None):
    plan = generate_data_engineer_plan(dataset, target, onboarding_mode, goal)

    mode = onboarding_mode.get("mode") if onboarding_mode else "Raw load + dbt-style model"

    if mode == "One-time raw load":
        sql = f"""
-- One-time raw load mode
-- Raw records are loaded into BigQuery table:
-- {target}

-- No transformation model requested.
"""
        summary = f"Prepared one-time raw load recommendation for {dataset}."

    elif mode == "Medallion architecture plan":
        sql = f"""
-- Medallion architecture plan for {dataset}

-- Bronze:
-- Load raw records into BigQuery raw_orders.

-- Silver:
CREATE OR REPLACE TABLE `{target.replace('fact_orders', 'silver_orders')}` AS
SELECT
    order_id,
    NULLIF(customer_id, '') AS customer_id,
    CAST(order_amount AS FLOAT64) AS order_amount,
    LOWER(order_status) AS order_status,
    created_at AS order_timestamp,
    CURRENT_TIMESTAMP() AS ingestion_timestamp
FROM `gen-lang-client-0959380368.pipelinepilot_demo.raw_orders`;

-- Gold:
CREATE OR REPLACE TABLE `{target.replace('fact_orders', 'gold_order_summary')}` AS
SELECT
    order_status,
    COUNT(*) AS order_count,
    SUM(order_amount) AS total_order_amount
FROM `{target.replace('fact_orders', 'silver_orders')}`
GROUP BY order_status;
"""
        summary = f"Generated medallion architecture plan for {dataset}."

    else:
        sql = f"""
-- dbt-style transformation model for analytics readiness
CREATE OR REPLACE TABLE `{target}` AS
SELECT
    order_id,
    customer_id,
    CAST(order_amount AS FLOAT64) AS order_amount,
    LOWER(order_status) AS order_status,
    created_at AS order_timestamp,
    CURRENT_TIMESTAMP() AS ingestion_timestamp
FROM `gen-lang-client-0959380368.pipelinepilot_demo.raw_orders`;
"""
        summary = f"Generated dbt-style transformation model for {dataset}."

    validation_rules = [
        "order_id must be unique",
        "customer_id should not be null",
        "order_amount must be greater than or equal to 0",
        "created_at must be a valid timestamp",
        "order_status should be normalized to lowercase"
    ]

    return {
        "summary": summary,
        "target": target,
        "mode": mode,
        "sql": sql.strip(),
        "validation_rules": validation_rules,
        "gemini_plan": plan
    }