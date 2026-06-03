from datetime import datetime
from services.mongodb_service import get_orders


def _valid_date(value):
    try:
        datetime.fromisoformat(str(value))
        return True
    except Exception:
        return False


def run_quality_checks():
    rows = get_orders()

    missing_customer = 0
    negative_amount = 0
    invalid_dates = 0
    duplicate_orders = 0

    seen_orders = set()

    for row in rows:
        order_id = row.get("order_id")

        if order_id in seen_orders:
            duplicate_orders += 1
        seen_orders.add(order_id)

        if not row.get("customer_id"):
            missing_customer += 1

        if row.get("order_amount", 0) < 0:
            negative_amount += 1

        if not _valid_date(row.get("created_at", "")):
            invalid_dates += 1

    score = 100
    score -= missing_customer * 10
    score -= negative_amount * 10
    score -= invalid_dates * 5
    score -= duplicate_orders * 10
    score = max(score, 0)

    issues = []

    if missing_customer:
        issues.append(f"{missing_customer} records missing customer_id")

    if negative_amount:
        issues.append(f"{negative_amount} records have negative order_amount")

    if invalid_dates:
        issues.append(f"{invalid_dates} records have invalid created_at format")

    if duplicate_orders:
        issues.append(f"{duplicate_orders} duplicate order_id values found")

    if score >= 85:
        status = "Ready"
    elif score >= 75:
        status = "Needs Review"
    else:
        status = "Blocked"

    safe_fixes = [
        "Standardize timestamp format before analytics release",
        "Normalize order_status values to lowercase",
        "Quarantine records with negative order_amount for manual review",
        "Do not guess missing customer_id; route missing IDs to data owner"
    ]

    return {
        "row_count": len(rows),
        "score": score,
        "status": status,
        "issues": issues,
        "safe_fixes": safe_fixes,
        "summary": f"Checked {len(rows)} records. Data quality score is {score}/100. Status: {status}."
    }