"""Thư viện bệnh lá chôm chôm (Nephelium lappaceum).

⚠️ Nội dung tham khảo, cần chuyên gia BVTV rà soát trước khi phát hành chính thức.
class_name phải trùng giá trị trong label_map của app/core/crops.yaml.
"""
from __future__ import annotations

from app.db.seed._format import Stage, disease_entry
from app.db.seed.fruit_common import algal_leaf_spot, anthracnose, sooty_mold

POWDERY_MILDEW = "Phấn trắng chôm chôm (Rambutan powdery mildew)"
ANTHRACNOSE = "Thán thư chôm chôm (Rambutan anthracnose)"
ALGAL = "Đốm rong chôm chôm (Rambutan algal leaf spot)"
SOOTY_MOLD = "Bồ hóng chôm chôm (Rambutan sooty mold)"

_powdery_mildew = disease_entry(
    class_name=POWDERY_MILDEW,
    description=(
        "Bệnh phấn trắng chôm chôm do nấm Oidium nephelii gây ra, tấn công lá non, đọt non, hoa và "
        "trái non. Bệnh phát triển mạnh vào mùa khô, khi chênh lệch nhiệt độ ngày đêm lớn và ẩm độ "
        "không khí ban đêm cao; gây hại nặng nhất ở giai đoạn ra đọt và ra hoa."
    ),
    symptoms=(
        "Lớp bột mịn màu trắng xám phủ trên mặt lá non, đọt non (và trên hoa, trái non). Lá non bị "
        "biến dạng, quăn, chuyển vàng rồi khô và rụng. Lớp phấn có thể lau đi được nhưng mô bên dưới "
        "đã bị hại, chuyển màu nâu."
    ),
    prevention=(
        "1. Tỉa cành sau thu hoạch, tạo tán thông thoáng.\n"
        "2. Phun phòng khi cây ra đọt non và trước khi ra hoa trong mùa khô.\n"
        "3. Bón phân cân đối, không bón thừa đạm.\n"
        "4. Thu gom và tiêu hủy lá, đọt bị bệnh."
    ),
    treatment=(
        "Phun Lưu huỳnh (Sulfur), Hexaconazole, Difenoconazole hoặc Azoxystrobin khi phát hiện bệnh; "
        "phun 2–3 lần cách nhau 7–10 ngày. Không phun lưu huỳnh khi trời quá nắng nóng để tránh cháy lá."
    ),
    stages=(
        Stage(
            "Ngày 1–2", "Phát hiện & cắt bỏ đọt bệnh",
            "Kiểm tra đọt non, cắt bỏ đọt bị phủ phấn trắng nặng và đem tiêu hủy.",
            "Lớp phấn trắng trên lá non và đọt non.",
            "Khoanh vùng được các cây và cành bị bệnh.",
            "Nếu cây đang ra hoa, phun thuốc ngay để bảo vệ hoa.",
        ),
        Stage(
            "Ngày 2–5", "Phun thuốc đặc trị lần 1",
            "Phun Hexaconazole hoặc Lưu huỳnh theo liều khuyến cáo, phun vào sáng sớm hoặc chiều mát.",
            "Lớp phấn trắng mới trên đọt non.",
            "Lớp phấn khô lại, không lan sang lá mới.",
            "Nếu thời tiết tiếp tục khô và lạnh về đêm, giữ lịch phun nhắc lại.",
        ),
        Stage(
            "Ngày 9–15", "Phun luân phiên & bảo vệ đọt mới",
            "Phun lần 2 bằng hoạt chất khác nhóm (Difenoconazole hoặc Azoxystrobin); bổ sung phân bón lá.",
            "Đọt non và hoa mới.",
            "Đọt mới xanh, không còn phấn trắng.",
            "Nếu bệnh vẫn xuất hiện, phun thêm lần 3.",
        ),
    ),
    recovery="3–4 tuần.",
    criteria=(
        "Không còn phấn trắng trên đọt non và lá non mới.",
        "Đọt mới phát triển bình thường, không biến dạng.",
        "Hoa và trái non (nếu có) không bị nhiễm.",
    ),
    note="Lá đã biến dạng không phục hồi; đánh giá khỏi bệnh dựa trên đợt đọt mới.",
    recovery_info=(
        "⏱️ Thời gian khống chế bệnh: 7–14 ngày.\n"
        "🌱 Đợt đọt mới sạch bệnh: 3–4 tuần.\n"
        "💡 Lưu ý: Phòng bệnh giai đoạn ra đọt và ra hoa trong mùa khô là then chốt."
    ),
)

RAMBUTAN_DISEASES = [
    _powdery_mildew,
    anthracnose(ANTHRACNOSE, "chôm chôm"),
    algal_leaf_spot(ALGAL, "chôm chôm"),
    sooty_mold(SOOTY_MOLD, "chôm chôm"),
]
