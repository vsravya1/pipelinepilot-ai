import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")


def generate_agent_summary(task_type, dataset, fivetran_status, quality_result, support_result=None, transformation=None):
    fallback = _fallback_summary(task_type, dataset, fivetran_status, quality_result, support_result)

    if not GOOGLE_API_KEY:
        return {
            "source": "rule-based fallback",
            "summary": fallback
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)

        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = f"""
You are a DataOps production support assistant.

Create a concise executive summary for this agent workflow.

Task Type: {task_type}
Dataset: {dataset}

Fivetran Status:
{fivetran_status}

Data Quality Result:
{quality_result}

Production Support Result:
{support_result}

Transformation:
{transformation}

Write the response as clean plain text with these headings:

What happened:
Why it matters:
Recommended next action:

Keep each section to 1-2 short sentences.
Do not use markdown symbols like **, backticks, or bullet points.
"""

        response = model.generate_content(prompt)

        return {
            "source": "gemini",
            "summary": response.text
        }

    except Exception as e:
        return {
            "source": "fallback",
            "summary": fallback + f"\n\nGemini fallback used because: {str(e)}"
        }


def _fallback_summary(task_type, dataset, fivetran_status, quality_result, support_result=None):
    issues = quality_result.get("issues", [])
    score = quality_result.get("score")
    status = quality_result.get("status")

    lines = [
        "1. What happened",
        f"PipelinePilot AI reviewed the {dataset} dataset for the task type: {task_type}.",
        f"The Fivetran pipeline status was checked and data quality validation returned a score of {score}/100 with status {status}.",
        "",
        "2. Why it matters"
    ]

    if issues:
        lines.append("The dataset has quality issues that may affect analytics reliability:")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("No major data quality issues were detected.")

    if support_result:
        lines.extend([
            "",
            "Production support finding:",
            f"- Root cause: {support_result.get('root_cause')}",
            f"- Impact: {support_result.get('impact')}"
        ])

    lines.extend([
        "",
        "3. Recommended next action",
        "Review the recommended safe fixes, approve the GitLab action, and resolve blockers before promoting the pipeline to production."
    ])

    return "\n".join(lines)