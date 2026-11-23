"""Helpers that render treatment plans in the text format DiseaseDetailModal parses.

Format contract (frontend/src/components/DiseaseDetailModal.tsx):
    Giai đoạn <n> — <khung thời gian>: <tiêu đề>:
    • Hành động cần làm: ...
    • Triệu chứng cần theo dõi: ...
    • Dấu hiệu cải thiện: ...
    • Khi nào cần can thiệp bổ sung: ...
"""
from __future__ import annotations

from dataclasses import dataclass

SAFETY_NOTE = (
    "⚠️ Hoạt chất nêu trên là gợi ý tham khảo: dùng đúng liều trên nhãn thuốc, luân phiên "
    "hoạt chất để tránh kháng thuốc, tuân thủ thời gian cách ly trước thu hoạch (PHI) và quy "
    "định dư lượng (MRL) của thị trường xuất khẩu. Nên tham vấn cán bộ BVTV địa phương "
    "trước khi áp dụng."
)


@dataclass(frozen=True)
class Stage:
    timeframe: str
    title: str
    action: str
    monitoring: str
    improvement: str
    extra: str


def render_stage(number: int, stage: Stage) -> str:
    return (
        f"Giai đoạn {number} — {stage.timeframe}: {stage.title}:\n"
        f"• Hành động cần làm: {stage.action}\n"
        f"• Triệu chứng cần theo dõi: {stage.monitoring}\n"
        f"• Dấu hiệu cải thiện: {stage.improvement}\n"
        f"• Khi nào cần can thiệp bổ sung: {stage.extra}"
    )


def render_final(recovery: str, criteria: tuple[str, ...], note: str) -> str:
    numbered = "\n".join(f"  {i}. {item}" for i, item in enumerate(criteria, start=1))
    return (
        "Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:\n"
        f"• Thời gian phục hồi ước tính: {recovery}\n"
        "• Tiêu chí xác định cây khỏi bệnh:\n"
        f"{numbered}\n"
        f"• Lưu ý phục hồi: {note}"
    )


def render_plan(stages: tuple[Stage, ...], recovery: str, criteria: tuple[str, ...], note: str) -> str:
    parts = [render_stage(i, s) for i, s in enumerate(stages, start=1)]
    parts.append(render_final(recovery, criteria, note))
    return "\n\n".join(parts)


def disease_entry(
    *,
    class_name: str,
    description: str,
    symptoms: str,
    prevention: str,
    treatment: str,
    stages: tuple[Stage, ...],
    recovery: str,
    criteria: tuple[str, ...],
    note: str,
    recovery_info: str,
) -> dict:
    """Build one seed row; display_name mirrors class_name like the tea catalog."""
    return {
        "class_name": class_name,
        "display_name": class_name,
        "description": description,
        "symptoms": symptoms,
        "prevention": prevention,
        "treatment": f"{treatment}\n{SAFETY_NOTE}",
        "treatment_steps": render_plan(stages, recovery, criteria, note),
        "recovery_info": recovery_info,
    }
