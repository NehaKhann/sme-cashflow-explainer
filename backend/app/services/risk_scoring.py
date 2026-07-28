"""
Deterministic risk scoring. No LLM involvement here on purpose --
an underwriter needs to trust the score itself, and "the AI decided"
is not an acceptable answer for why a loan was flagged risky.

Each rule is simple, documented, and independently testable.
"""

from dataclasses import dataclass
from .feature_extraction import CashFlowFeatures


@dataclass
class RiskFlag:
    severity: str  # "low" | "medium" | "high"
    code: str
    message: str


@dataclass
class RiskAssessment:
    overall_score: int  # 0-100, higher = riskier
    overall_band: str  # "low" | "medium" | "high"
    flags: list


def _band_from_score(score: int) -> str:
    if score >= 65:
        return "high"
    if score >= 35:
        return "medium"
    return "low"


def assess_risk(features: CashFlowFeatures) -> RiskAssessment:
    score = 0
    flags: list[RiskFlag] = []

    # -- revenue volatility --
    if features.revenue_volatility_pct >= 50:
        score += 25
        flags.append(RiskFlag(
            "high", "REVENUE_VOLATILITY",
            f"Monthly revenue varies by {features.revenue_volatility_pct}% "
            f"(coefficient of variation), indicating unpredictable cash inflows."
        ))
    elif features.revenue_volatility_pct >= 25:
        score += 12
        flags.append(RiskFlag(
            "medium", "REVENUE_VOLATILITY",
            f"Monthly revenue varies by {features.revenue_volatility_pct}%, "
            f"moderate volatility worth noting."
        ))

    # -- customer concentration --
    if features.top_customer_share_pct >= 50:
        score += 25
        flags.append(RiskFlag(
            "high", "CUSTOMER_CONCENTRATION",
            f"{features.top_customer_name} accounts for "
            f"{features.top_customer_share_pct}% of total revenue -- "
            f"losing this customer would be existential."
        ))
    elif features.top_customer_share_pct >= 30:
        score += 12
        flags.append(RiskFlag(
            "medium", "CUSTOMER_CONCENTRATION",
            f"{features.top_customer_name} accounts for "
            f"{features.top_customer_share_pct}% of revenue -- "
            f"a meaningful concentration risk."
        ))

    # -- negative cash flow streaks --
    if features.longest_negative_streak_months >= 3:
        score += 40
        flags.append(RiskFlag(
            "high", "SUSTAINED_NEGATIVE_FLOW",
            f"{features.longest_negative_streak_months} consecutive months "
            f"of negative net cash flow detected."
        ))
    elif features.longest_negative_streak_months >= 1:
        score += 10
        flags.append(RiskFlag(
            "medium", "NEGATIVE_FLOW_MONTHS",
            f"{features.months_of_negative_flow} month(s) with negative net cash flow."
        ))

    # -- steep single-month drop --
    if features.largest_mom_drop_pct <= -40:
        score += 15
        flags.append(RiskFlag(
            "high", "SHARP_REVENUE_DROP",
            f"Revenue dropped {abs(features.largest_mom_drop_pct)}% in "
            f"{features.largest_mom_drop_month} -- worth understanding the cause."
        ))

    # -- thin customer base --
    if features.num_unique_customers <= 3 and features.num_unique_customers > 0:
        score += 10
        flags.append(RiskFlag(
            "medium", "THIN_CUSTOMER_BASE",
            f"Only {features.num_unique_customers} unique customer(s) across the period."
        ))

    score = min(score, 100)
    if not flags:
        flags.append(RiskFlag(
            "low", "NO_MAJOR_FLAGS",
            "No major cash-flow risk patterns detected in this period."
        ))

    # A single "high" severity flag should never round down to a "low" overall
    # band just because its point weight alone doesn't cross the threshold --
    # the band is the max of the score-derived band and the worst individual flag.
    band_rank = {"low": 0, "medium": 1, "high": 2}
    worst_flag_band = max((f.severity for f in flags), key=lambda s: band_rank[s], default="low")
    score_band = _band_from_score(score)
    overall_band = max([score_band, worst_flag_band], key=lambda s: band_rank[s])

    return RiskAssessment(overall_score=score, overall_band=overall_band, flags=flags)
