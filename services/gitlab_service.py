def prepare_gitlab_action(task_type, dataset, quality_result, support_result=None, transformation=None):
    title = f"{task_type}: Review required for {dataset}"

    lines = [
        f"Task Type: {task_type}",
        f"Dataset: {dataset}",
        f"Readiness Score: {quality_result['score']}/100",
        f"Status: {quality_result['status']}",
        "",
        "Data Quality Issues:"
    ]

    if quality_result["issues"]:
        for issue in quality_result["issues"]:
            lines.append(f"- {issue}")
    else:
        lines.append("- No data quality issues found")

    lines.append("")
    lines.append("Recommended Safe Fixes:")

    for fix in quality_result["safe_fixes"]:
        lines.append(f"- {fix}")

    if support_result:
        lines.append("")
        lines.append("Production Support Finding:")
        lines.append(f"- Root Cause: {support_result['root_cause']}")
        lines.append(f"- Impact: {support_result['impact']}")
        lines.append(f"- Recommended Fix: {support_result['recommended_fix']}")

    if transformation:
        lines.append("")
        lines.append("Generated Transformation SQL:")
        lines.append(transformation["sql"])

    return {
        "title": title,
        "description": "\n".join(lines),
        "status": "Prepared - waiting for human approval",
        "gitlab_url": None
    }