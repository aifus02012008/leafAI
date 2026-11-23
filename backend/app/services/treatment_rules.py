"""Pure decision rules for treatments: pre-harvest interval and treatment response.

Agronomy note: fungicides do not erase existing lesions. A treatment "works" when lesions
STOP GROWING and no new ones appear, so the verdict is based on lesion growth, not on
lesions disappearing. Thresholds are configurable constants pending expert review.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Literal

Verdict = Literal["effective", "unclear", "ineffective", "inconclusive"]

EFFECTIVE_MAX_GROWTH = 0.10    # <= +10% relative lesion area: disease contained
UNCLEAR_MAX_GROWTH = 0.30      # +10..30%: keep watching
BASELINE_FLOOR_PCT = 2.0       # avoid huge relative swings on tiny baselines

INEFFECTIVE_CHECKLIST = (
    "Kiểm tra lại chẩn đoán: có đúng loại bệnh không (chụp thêm lá khác, hỏi cán bộ BVTV).",
    "Mưa trong vòng vài giờ sau phun có thể đã rửa trôi thuốc.",
    "Pha đúng liều trên nhãn và phun ướt đều cả hai mặt lá chưa?",
    "Thời điểm phun: nên phun lúc sáng sớm hoặc chiều mát.",
    "Nếu các yếu tố trên đều ổn, sâu bệnh CÓ THỂ đã kháng hoạt chất — nên đổi sang hoạt chất khác nhóm tác động.",
)


@dataclass(frozen=True)
class SprayRecord:
    applied_on: date
    phi_days: int | None

    def __post_init__(self) -> None:
        if self.phi_days is not None and self.phi_days < 0:
            raise ValueError("phi_days must be >= 0")


@dataclass(frozen=True)
class ResponseOutcome:
    verdict: Verdict
    relative_change: float | None
    message: str
    checklist: tuple[str, ...] = ()


def harvest_safe_date(sprays: Iterable[SprayRecord]) -> date | None:
    """Earliest harvest date that respects every spray's pre-harvest interval."""
    dates = [s.applied_on + timedelta(days=s.phi_days) for s in sprays if s.phi_days is not None]
    return max(dates) if dates else None


def evaluate_response(before_pct: float | None, after_pct: float | None) -> ResponseOutcome:
    if before_pct is None or after_pct is None:
        return ResponseOutcome(
            verdict="inconclusive",
            relative_change=None,
            message="Không đo được diện tích vết bệnh trên một trong hai ảnh. Hãy chụp lại rõ lá, đủ sáng, nền đơn giản.",
        )
    change = (after_pct - before_pct) / max(before_pct, BASELINE_FLOOR_PCT)
    change = round(change, 4)
    if change <= EFFECTIVE_MAX_GROWTH:
        return ResponseOutcome(
            verdict="effective",
            relative_change=change,
            message="Thuốc có tác dụng: vết bệnh không lan rộng thêm. Tiếp tục theo dõi lá non mới ra.",
        )
    if change <= UNCLEAR_MAX_GROWTH:
        return ResponseOutcome(
            verdict="unclear",
            relative_change=change,
            message="Vết bệnh còn tăng nhẹ, chưa đủ cơ sở kết luận. Theo dõi thêm 2–3 ngày rồi chụp lại.",
        )
    return ResponseOutcome(
        verdict="ineffective",
        relative_change=change,
        message="Vết bệnh tiếp tục lan rộng — thuốc có thể chưa hiệu quả. Rà soát danh sách dưới đây trước khi đổi thuốc.",
        checklist=INEFFECTIVE_CHECKLIST,
    )


def suggest_rotation(used: dict | None, candidates: Iterable[dict]) -> list[dict]:
    """Non-banned candidates from a different mode-of-action group than the active just used."""
    used_code = used["code"] if used else None
    used_moa = used.get("moa_code") if used else None
    return [
        c for c in candidates
        if not c["banned"]
        and c["code"] != used_code
        and (used_moa is None or c.get("moa_code") != used_moa)
    ]
