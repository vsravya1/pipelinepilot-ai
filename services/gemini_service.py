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

def infer_pipeline_onboarding_mode(goal, selected_mode):
    if selected_mode and selected_mode != "Auto - Let Gemini decide":
        return {
            "source": "user_selected",
            "mode": selected_mode,
            "reason": "User selected the pipeline mode explicitly."
        }

    fallback_mode = "Raw load + dbt-style model"

    if not GOOGLE_API_KEY:
        return {
            "source": "rule-based fallback",
            "mode": fallback_mode,
            "reason": "No Gemini key available. Defaulting to raw load plus dbt-style model."
        }

    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
You are a data engineering supervisor.

Classify this pipeline onboarding request into exactly one mode:

1. One-time raw load
2. Raw load + dbt-style model
3. Medallion architecture plan

User goal:
{goal}

Return only this format:
Mode: <one of the three modes>
Reason: <one short sentence>
"""

        response = model.generate_content(prompt)
        text = response.text.strip()

        mode = fallback_mode
        if "One-time raw load" in text:
            mode = "One-time raw load"
        elif "Medallion architecture plan" in text:
            mode = "Medallion architecture plan"
        elif "Raw load + dbt-style model" in text:
            mode = "Raw load + dbt-style model"

        return {
            "source": "gemini",
            "mode": mode,
            "reason": text
        }

    except Exception as e:
        return {
            "source": "rule-based fallback",
            "mode": fallback_mode,
            "reason": f"Gemini mode inference failed: {str(e)}"
        }
    

def generate_data_engineer_plan(dataset, target, onboarding_mode=None, goal=None):
    mode = onboarding_mode.get("mode") if onboarding_mode else "Raw load + dbt-style model"

    fallback = {
        "source": "rule-based fallback",
        "plan": (
            f"Pipeline onboarding mode: {mode}. "
            f"Load source dataset {dataset} into BigQuery raw_orders. "
            "Generate the appropriate transformation or architecture recommendation for engineering review."
        )
    }

    if not GOOGLE_API_KEY:
        return fallback

    try:
        import google.generativeai as genai

        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-2.0-flash")

        prompt = f"""
You are a senior data engineer.

Dataset: {dataset}
Target: {target}
Onboarding mode: {mode}
User goal: {goal}

Create a short practical onboarding plan.
Explain what should be executed now and what should be tracked for engineering review.
Do not use markdown tables.
Keep it under 120 words.
"""

        response = model.generate_content(prompt)

        return {
            "source": "gemini",
            "plan": response.text
        }

    except Exception as e:
        return {
            "source": "rule-based fallback",
            "plan": fallback["plan"] + f" Gemini fallback used because: {str(e)}"
        }    