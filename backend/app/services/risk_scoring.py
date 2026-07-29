from ..models import CashFlowFeatures, RiskAssessment, RiskFlag


def _band_from_score(score: int) -> str:
    if score >= 65:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


FLAG_RULES = [
    {
        "condition": lambda f: f.revenue_volatility_pct >= 50,
        "severity": "high", "code": "REVENUE_VOLATILITY",
        "message": lambda f: (
            f"Monthly revenue varies by {f.revenue_volatility_pct}% "
            f"(coefficient of variation), indicating unpredictable cash inflows."
        ),
        "score": 25,
    },
    {
        "condition": lambda f: f.revenue_volatility_pct >= 25,
        "severity": "medium", "code": "REVENUE_VOLATILITY",
        "message": lambda f: (
            f"Monthly revenue varies by {f.revenue_volatility_pct}%, "
            f"moderate volatility worth noting."
        ),
        "score": 12,
    },
    {
        "condition": lambda f: f.top_customer_share_pct >= 50,
        "severity": "high", "code": "CUSTOMER_CONCENTRATION",
        "message": lambda f: (
            f"{f.top_customer_name} accounts for "
            f"{f.top_customer_share_pct}% of total revenue -- "
            f"losing this customer would be existential."
        ),
        "score": 25,
    },
    {
        "condition": lambda f: f.top_customer_share_pct >= 30,
        "severity": "medium", "code": "CUSTOMER_CONCENTRATION",
        "message": lambda f: (
            f"{f.top_customer_name} accounts for "
            f"{f.top_customer_share_pct}% of revenue -- "
            f"a meaningful concentration risk."
        ),
        "score": 12,
    },
    {
        "condition": lambda f: f.longest_negative_streak_months >= 3,
        "severity": "high", "code": "SUSTAINED_NEGATIVE_FLOW",
        "message": lambda f: (
            f"{f.longest_negative_streak_months} consecutive months "
            f"of negative net cash flow detected."
        ),
        "score": 40,
    },
    {
        "condition": lambda f: f.longest_negative_streak_months >= 1,
        "severity": "medium", "code": "NEGATIVE_FLOW_MONTHS",
        "message": lambda f: (
            f"{f.months_of_negative_flow} month(s) with negative net cash flow."
        ),
        "score": 10,
    },
    {
        "condition": lambda f: f.largest_mom_drop_pct <= -40,
        "severity": "high", "code": "SHARP_REVENUE_DROP",
        "message": lambda f: (
            f"Revenue dropped {abs(f.largest_mom_drop_pct)}% in "
            f"{f.largest_mom_drop_month} -- worth understanding the cause."
        ),
        "score": 15,
    },
    {
        "condition": lambda f: 0 < f.num_unique_customers <= 3,
        "severity": "medium", "code": "THIN_CUSTOMER_BASE",
        "message": lambda f: (
            f"Only {f.num_unique_customers} unique customer(s) across the period."
        ),
        "score": 10,
    },
]


def assess_risk(features: CashFlowFeatures) -> RiskAssessment:
    score = 0
    flags: list[RiskFlag] = []
    seen_codes: set[str] = set()

    for rule in FLAG_RULES:
        if rule["condition"](features) and rule["code"] not in seen_codes:
            score += rule["score"]
            flags.append(RiskFlag(
                severity=rule["severity"],
                code=rule["code"],
                message=rule["message"](features),
            ))
            seen_codes.add(rule["code"])

    score = min(score, 100)

    if not flags:
        flags.append(RiskFlag(
            severity="low", code="NO_MAJOR_FLAGS",
            message="No major cash-flow risk patterns detected in this period.",
        ))

    band_rank = {"low": 0, "medium": 1, "high": 2}
    worst_flag_band = max((f.severity for f in flags), key=lambda s: band_rank[s])
    score_band = _band_from_score(score)
    overall_band = max([score_band, worst_flag_band], key=lambda s: band_rank[s])

    return RiskAssessment(overall_score=score, overall_band=overall_band, flags=flags)
