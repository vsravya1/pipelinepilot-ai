def get_pipeline_status(source, dataset):
    return {
        "connector": f"{source} {dataset} connector",
        "status": "Healthy with warning",
        "last_sync": "18 minutes ago",
        "schema_drift": True,
        "new_fields": ["coupon_code", "delivery_partner"],
        "summary": (
            "Fivetran pipeline checked. Last sync was 18 minutes ago. "
            "Schema drift detected: new fields coupon_code and delivery_partner."
        )
    }