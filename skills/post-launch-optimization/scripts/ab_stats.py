#!/usr/bin/env python3
"""A/B statistical significance helper for post-launch-optimization Layer 5.

Two-proportion z-test for conversion-rate comparison. Returns p-value,
95% confidence interval on the absolute lift, minimum-sample-size estimate
for the detected effect, and a winner verdict that respects both
significance and minimum-sample rules.

Pure stdlib — math only, no scipy/numpy dependency.

CLI:
    python ab_stats.py <conv_a> <imp_a> <conv_b> <imp_b>
        e.g. python ab_stats.py 42 1000 28 1000

Module:
    from ab_stats import compare
    result = compare(conv_a=42, imp_a=1000, conv_b=28, imp_b=1000)
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass, asdict
from typing import Optional


# Statistical decision thresholds — see analysis-framework.md Layer 5.
P_VALUE_THRESHOLD = 0.05          # conventional 5% alpha
MIN_CONVERSIONS_PER_VARIANT = 20  # don't declare a winner with tiny-sample noise
MIN_IMPRESSIONS_PER_VARIANT = 1000
MIN_DAYS = 7                      # external check — caller passes days_running


@dataclass
class ABResult:
    """Outcome of a two-sample proportion test on A vs B."""
    conv_a: int
    imp_a: int
    cvr_a: float
    conv_b: int
    imp_b: int
    cvr_b: float
    lift_abs: float                 # CVR_b - CVR_a (percentage points)
    lift_rel_pct: Optional[float]   # (CVR_b - CVR_a) / CVR_a * 100
    z_score: float
    p_value: float                  # two-tailed
    ci_low: float                   # 95% CI on absolute lift
    ci_high: float
    min_sample_per_variant: Optional[int]  # for the observed effect at 80% power
    verdict: str                    # see _decide_verdict
    notes: list[str]


# ── Statistical primitives ───────────────────────────────────────────────────

def _normal_cdf(x: float) -> float:
    """Standard-normal CDF using math.erf — accurate to ~7 decimals, no SciPy."""
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _two_tailed_p(z: float) -> float:
    """Two-tailed p-value from a z-score."""
    return 2.0 * (1.0 - _normal_cdf(abs(z)))


def _pooled_se(p1: float, n1: int, p2: float, n2: int) -> float:
    """Pooled standard error for the difference in two proportions (null-hypothesis form)."""
    if n1 == 0 or n2 == 0:
        return float("inf")
    p_pool = (p1 * n1 + p2 * n2) / (n1 + n2)
    return math.sqrt(p_pool * (1 - p_pool) * (1 / n1 + 1 / n2))


def _unpooled_se(p1: float, n1: int, p2: float, n2: int) -> float:
    """Unpooled standard error — used for the confidence interval on the lift."""
    if n1 == 0 or n2 == 0:
        return float("inf")
    return math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)


def _required_sample_size(p1: float, p2: float, alpha: float = 0.05, power: float = 0.8) -> Optional[int]:
    """Minimum sample size per variant to detect an effect of |p2 - p1| at given alpha+power.
    Returns None if the observed effect is 0 (no effect to size for)."""
    if p1 == p2:
        return None
    # z for two-tailed alpha
    z_alpha = _inverse_normal(1 - alpha / 2)
    z_beta = _inverse_normal(power)
    p_bar = (p1 + p2) / 2
    numerator = (z_alpha * math.sqrt(2 * p_bar * (1 - p_bar))
                 + z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    return int(math.ceil(numerator / denominator))


def _inverse_normal(p: float) -> float:
    """Inverse of the standard normal CDF via Beasley-Springer-Moro approximation.
    Used for sample-size math — fine for 0.01 <= p <= 0.99."""
    # Rational approximation for tails and central region (Acklam's algorithm).
    if p <= 0 or p >= 1:
        raise ValueError("p must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    p_low = 0.02425
    p_high = 1 - p_low
    if p < p_low:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > p_high:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
               ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
           (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


# ── Core API ─────────────────────────────────────────────────────────────────

def compare(
    conv_a: int, imp_a: int,
    conv_b: int, imp_b: int,
    days_running: Optional[int] = None,
    label_a: str = "A",
    label_b: str = "B",
) -> ABResult:
    """Compare two variants on CVR. Returns ABResult with full diagnostics."""
    notes: list[str] = []
    cvr_a = (conv_a / imp_a) if imp_a else 0.0
    cvr_b = (conv_b / imp_b) if imp_b else 0.0
    lift_abs = cvr_b - cvr_a
    lift_rel_pct = ((cvr_b - cvr_a) / cvr_a * 100.0) if cvr_a > 0 else None

    # Z-test on pooled SE
    se_null = _pooled_se(cvr_a, imp_a, cvr_b, imp_b)
    z = (cvr_b - cvr_a) / se_null if se_null not in (0, float("inf")) else 0.0
    p = _two_tailed_p(z) if se_null not in (0, float("inf")) else 1.0

    # 95% CI on lift — uses unpooled SE (standard for effect-size reporting)
    se_ci = _unpooled_se(cvr_a, imp_a, cvr_b, imp_b)
    z_95 = 1.959963984540054  # inverse_normal(0.975)
    ci_low = lift_abs - z_95 * se_ci
    ci_high = lift_abs + z_95 * se_ci

    # Required sample size for the OBSERVED effect at 80% power
    req_n: Optional[int] = None
    try:
        req_n = _required_sample_size(cvr_a, cvr_b)
    except (ValueError, ZeroDivisionError):
        req_n = None

    # Verdict composition
    significant = p < P_VALUE_THRESHOLD
    enough_conv = conv_a >= MIN_CONVERSIONS_PER_VARIANT and conv_b >= MIN_CONVERSIONS_PER_VARIANT
    enough_imp = imp_a >= MIN_IMPRESSIONS_PER_VARIANT and imp_b >= MIN_IMPRESSIONS_PER_VARIANT
    enough_time = days_running is None or days_running >= MIN_DAYS

    verdict = _decide_verdict(significant, enough_conv, enough_imp, enough_time,
                              cvr_a, cvr_b, label_a, label_b, notes,
                              conv_a, conv_b, days_running)

    return ABResult(
        conv_a=conv_a, imp_a=imp_a, cvr_a=cvr_a,
        conv_b=conv_b, imp_b=imp_b, cvr_b=cvr_b,
        lift_abs=lift_abs, lift_rel_pct=lift_rel_pct,
        z_score=z, p_value=p,
        ci_low=ci_low, ci_high=ci_high,
        min_sample_per_variant=req_n,
        verdict=verdict, notes=notes,
    )


def _decide_verdict(significant: bool, enough_conv: bool, enough_imp: bool, enough_time: bool,
                    cvr_a: float, cvr_b: float, label_a: str, label_b: str,
                    notes: list[str],
                    conv_a: int, conv_b: int, days_running: Optional[int]) -> str:
    if not enough_conv:
        notes.append(f"Min conversions/variant not met: {conv_a}, {conv_b} (need ≥{MIN_CONVERSIONS_PER_VARIANT})")
    if not enough_imp:
        notes.append(f"Min impressions/variant not met (need ≥{MIN_IMPRESSIONS_PER_VARIANT})")
    if not enough_time and days_running is not None:
        notes.append(f"Min runtime not met: {days_running}d (need ≥{MIN_DAYS})")

    # If any gate not met → NEED_MORE_DATA regardless of p
    if not (enough_conv and enough_imp and enough_time):
        return "NEED_MORE_DATA"
    if not significant:
        return "NO_WINNER"
    winner = label_b if cvr_b > cvr_a else label_a
    return f"WINNER:{winner}"


# ── CLI ──────────────────────────────────────────────────────────────────────

def _format_pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def main() -> int:
    if len(sys.argv) < 5:
        print(__doc__.strip())
        return 1
    try:
        conv_a, imp_a, conv_b, imp_b = (int(x) for x in sys.argv[1:5])
    except ValueError:
        print("All four inputs must be integers.", file=sys.stderr)
        return 2
    days = int(sys.argv[5]) if len(sys.argv) > 5 else None
    result = compare(conv_a, imp_a, conv_b, imp_b, days_running=days)
    print(f"Variant A: {result.conv_a}/{result.imp_a} = {_format_pct(result.cvr_a)} CVR")
    print(f"Variant B: {result.conv_b}/{result.imp_b} = {_format_pct(result.cvr_b)} CVR")
    print(f"Abs lift : {_format_pct(result.lift_abs)} pts"
          + (f"  (rel {result.lift_rel_pct:+.1f}%)" if result.lift_rel_pct is not None else ""))
    print(f"z-score  : {result.z_score:.3f}")
    print(f"p-value  : {result.p_value:.4f}  (threshold {P_VALUE_THRESHOLD})")
    print(f"95% CI on lift: [{_format_pct(result.ci_low)}, {_format_pct(result.ci_high)}] pts")
    if result.min_sample_per_variant is not None:
        print(f"Min n/variant for this effect (α=0.05, power=0.8): {result.min_sample_per_variant}")
    print(f"Verdict  : {result.verdict}")
    for n in result.notes:
        print(f"  note: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
