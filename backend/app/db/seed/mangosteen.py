"""Thư viện bệnh lá măng cụt (Garcinia mangostana).

⚠️ Nội dung tham khảo, cần chuyên gia BVTV rà soát trước khi phát hành chính thức.
class_name phải trùng giá trị trong label_map của app/core/crops.yaml.
"""
from __future__ import annotations

from app.db.seed._format import Stage, disease_entry
from app.db.seed.fruit_common import algal_leaf_spot, anthracnose, sooty_mold

ANTHRACNOSE = "Thán thư măng cụt (Mangosteen anthracnose)"
PESTALOTIOPSIS = "Đốm lá Pestalotiopsis trên măng cụt (Mangosteen Pestalotiopsis leaf spot)"
ALGAL = "Đốm rong măng cụt (Mangosteen algal leaf spot)"
SOOTY_MOLD = "Bồ hóng măng cụt (Mangosteen sooty mold)"

_pestalotiopsis = disease_entry(
    class_name=PESTALOTIOPSIS,
    description=(
        "Bệnh đốm lá (cháy lá) măng cụt do nấm Pestalotiopsis spp. gây ra. Nấm thường xâm nhập qua "
        "vết thương cơ giới, vết côn trùng chích hút hoặc vết cháy nắng; phát triển mạnh khi ẩm độ cao. "
        "Bệnh gây hại chủ yếu trên lá bánh tẻ và lá già, làm giảm diện tích quang hợp."
    ),
    symptoms=(
        "Đốm màu nâu xám, ranh giới rõ với viền nâu đậm, thường bắt đầu ở chóp hoặc mép lá. Giữa vết "
        "bệnh chuyển xám trắng, có nhiều chấm đen li ti (ổ bào tử của nấm). Các vết bệnh liên kết làm "
        "cháy một phần lớn phiến lá."
    ),
    prevention=(
        "1. Tỉa cành thông thoáng, thu gom và tiêu hủy lá bệnh.\n"
        "2. Hạn chế gây vết thương trên lá; quản lý côn trùng chích hút.\n"
        "3. Che bóng hợp lý cho cây con để tránh cháy nắng.\n"
        "4. Bón phân cân đối, bổ sung kali và canxi giúp lá dày, cứng."
    ),
    treatment=(
        "Cắt bỏ lá bệnh nặng. Phun Mancozeb, Propineb, thuốc gốc đồng hoặc Azoxystrobin + "
        "Difenoconazole; phun 2 lần cách nhau 7–10 ngày."
    ),
    stages=(
        Stage(
            "Ngày 1–2", "Vệ sinh lá bệnh",
            "Cắt bỏ lá bị cháy nặng, thu gom lá rụng đem tiêu hủy.",
            "Số lá có đốm nâu xám với chấm đen li ti.",
            "Giảm nguồn bào tử trong vườn.",
            "Nếu bệnh xuất hiện trên lá non, phun thuốc ngay.",
        ),
        Stage(
            "Ngày 3–7", "Phun thuốc lần 1",
            "Phun Mancozeb hoặc Propineb theo liều khuyến cáo, ướt đều hai mặt lá.",
            "Vết bệnh mới trên lá kế cận.",
            "Vết bệnh khô, không lan rộng thêm.",
            "Nếu mưa nhiều, rút ngắn khoảng cách giữa hai lần phun.",
        ),
        Stage(
            "Ngày 10–17", "Phun luân phiên & bồi dưỡng",
            "Phun lần 2 bằng Azoxystrobin + Difenoconazole hoặc thuốc gốc đồng; bón bổ sung kali.",
            "Đợt lá mới.",
            "Lá mới sạch bệnh, dày và xanh.",
            "Nếu vẫn có vết mới, kiểm tra côn trùng chích hút và vết thương trên lá.",
        ),
    ),
    recovery="3–5 tuần.",
    criteria=(
        "Không còn vết bệnh mới trong 2–3 tuần.",
        "Vết bệnh cũ đã khô, không lan.",
        "Đợt lá mới sạch bệnh.",
    ),
    note="Phần lá đã cháy không xanh lại; đánh giá theo lá mới.",
    recovery_info=(
        "⏱️ Thời gian khống chế bệnh: 7–14 ngày.\n"
        "🌱 Lá mới sạch bệnh: 3–5 tuần.\n"
        "💡 Lưu ý: Hạn chế vết thương trên lá là cách phòng bệnh hiệu quả."
    ),
)

MANGOSTEEN_DISEASES = [
    anthracnose(ANTHRACNOSE, "măng cụt"),
    _pestalotiopsis,
    algal_leaf_spot(ALGAL, "măng cụt"),
    sooty_mold(SOOTY_MOLD, "măng cụt"),
]
