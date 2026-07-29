import os
import json
from ..models import CashFlowFeatures, RiskAssessment

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SYSTEM_PROMPT = """You are a credit underwriting assistant. You will be given
pre-computed cash-flow statistics for a small business, already calculated by
a data pipeline. Your ONLY job is to explain these numbers in clear,
professional, underwriter-facing prose.

STRICT RULES:
- Never invent, estimate, or restate a number differently than given.
- Every figure you mention must come directly from the provided JSON.
- If the data doesn't cover something, say so rather than guessing.
- Write 3-5 short paragraphs: (1) overall cash-flow health, (2) volatility
  and concentration risk, (3) any red flags, (4) a one-line balanced summary.
- Tone: neutral, factual, underwriter-to-underwriter. No hype, no alarmism.
"""


def _build_user_prompt(features: CashFlowFeatures, risk: RiskAssessment) -> str:
    payload = {
        "period": f"{features.start_date} to {features.end_date} ({features.num_months} months)",
        "total_inflow": features.total_inflow,
        "total_outflow": features.total_outflow,
        "net_cash_flow": features.net_cash_flow,
        "revenue_volatility_pct": features.revenue_volatility_pct,
        "largest_month_over_month_drop_pct": features.largest_mom_drop_pct,
        "largest_drop_month": features.largest_mom_drop_month,
        "top_customer_share_pct": features.top_customer_share_pct,
        "top_customer_name": features.top_customer_name,
        "top_3_customer_share_pct": features.top_3_customer_share_pct,
        "num_unique_customers": features.num_unique_customers,
        "seasonality_detected": features.seasonality_detected,
        "seasonal_low_months": features.seasonal_low_months,
        "seasonal_high_months": features.seasonal_high_months,
        "avg_monthly_burn": features.avg_monthly_burn,
        "months_of_negative_flow": features.months_of_negative_flow,
        "longest_negative_streak_months": features.longest_negative_streak_months,
        "risk_score_0_to_100": risk.overall_score,
        "risk_band": risk.overall_band,
        "risk_flags": [{"severity": f.severity, "message": f.message} for f in risk.flags],
    }
    return (
        "Here is the pre-computed cash-flow data for one small business. "
        "Write the underwriting narrative described in your instructions, "
        "using ONLY these numbers:\n\n" + json.dumps(payload, indent=2)
    )


def _fallback_narrative(features: CashFlowFeatures, risk: RiskAssessment) -> str:
    lines = [
        f"Over {features.start_date} to {features.end_date} ({features.num_months} months), "
        f"total inflows were {features.total_inflow:,.2f} against outflows of "
        f"{abs(features.total_outflow):,.2f}, for a net cash flow of {features.net_cash_flow:,.2f}.",
        "",
        f"Revenue volatility (coefficient of variation) is {features.revenue_volatility_pct}%. "
        + (
            f"The top customer, {features.top_customer_name}, represents "
            f"{features.top_customer_share_pct}% of total revenue"
            if features.top_customer_name else "No dominant customer was identified"
        )
        + f", and the top 3 customers together represent {features.top_3_customer_share_pct}%.",
        "",
        "Risk flags:",
    ]
    for f in risk.flags:
        lines.append(f"  [{f.severity.upper()}] {f.message}")
    lines.append("")
    lines.append(f"Overall risk score: {risk.overall_score}/100 ({risk.overall_band} risk).")
    return "\n".join(lines)


def generate_narrative(features: CashFlowFeatures, risk: RiskAssessment) -> str:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return _fallback_narrative(features, risk)

    try:
        from groq import Groq
    except ImportError:
        return _fallback_narrative(features, risk)

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(features, risk)},
        ],
        temperature=0.2,
        max_tokens=700,
    )
    return response.choices[0].message.content
