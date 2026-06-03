def investigate_issue(dataset, fivetran_status, quality_result):
    root_cause = "Data quality failures detected in source records."
    impact = "Analytics dashboards may show incorrect or incomplete results."
    recommended_fix = "Apply validation rules, quarantine invalid records, and rerun the pipeline."

    if fivetran_status.get("schema_drift"):
        root_cause = "Schema drift detected after new fields appeared in the source data."
        impact = "Downstream transformations and dashboards may not include the latest source changes."
        recommended_fix = "Review new fields, update transformation mapping, and rerun Fivetran sync."

    if quality_result.get("score", 100) < 75:
        root_cause += " Data quality score is below production threshold."
        impact += " Business users may lose trust in reporting accuracy."

    return {
        "summary": f"Investigated production support issue for {dataset}. Root cause: {root_cause}",
        "root_cause": root_cause,
        "impact": impact,
        "recommended_fix": recommended_fix
    }