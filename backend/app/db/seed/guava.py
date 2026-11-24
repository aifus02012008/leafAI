"""Thư viện bệnh lá ổi (Psidium guajava).

⚠️ Nội dung tham khảo, cần chuyên gia BVTV rà soát trước khi phát hành chính thức.
class_name phải trùng giá trị trong label_map của app/core/crops.yaml.
"""
from __future__ import annotations

from app.db.seed._format import Stage, disease_entry
from app.db.seed.fruit_common import anthracnose

ANTHRACNOSE = "Thán thư ổi (Guava anthracnose)"
CANKER = "Loét lá ổi (Guava canker)"
DOT = "Đốm lá ổi (Guava leaf dot)"
RUST = "Gỉ sắt ổi (Guava rust)"


def _stages(cultural: tuple[str, str, str, str], bio: tuple[str, str, str, str], chem: tuple[str, str, str, str]) -> tuple[Stage, ...]:
    """(action, monitoring, improvement, extra) for the cultural → biological → chemical stages."""
    return (
        Stage("Ngày 1–3", "Canh tác — Vệ sinh vườn, giảm nguồn bệnh", *cultural),
        Stage("Ngày 3–7", "Sinh học — Tăng sức đề kháng, chế phẩm sinh học", *bio),
        Stage("Ngày 7–21", "Hóa học — Phun thuốc khi thật sự cần", *chem),
    )


_canker = disease_entry(
    class_name=CANKER,
    description=(
        "Do nấm Pestalotiopsis psidii gây ra, xâm nhập qua vết thương trên lá, cành non và trái. Bệnh phát triển "
        "mạnh khi mưa nhiều, ẩm độ cao, vườn rậm rạp và cây bị côn trùng chích hút gây vết thương."
    ),
    symptoms=(
        "Vết bệnh màu nâu đến nâu đen, khô, thường bắt đầu từ mép hoặc chóp lá rồi lan vào trong; mô bệnh giòn, "
        "nứt, có thể rách; ranh giới với mô khỏe có viền vàng nhạt. Trên trái có vết loét sần, nứt."
    ),
    prevention=(
        "1. Tỉa cành tạo tán thông thoáng, cắt bỏ cành lá bệnh sau thu hoạch.\n"
        "2. Hạn chế vết thương: quản lý côn trùng chích hút, không làm dập lá khi chăm sóc.\n"
        "3. Bón phân cân đối, bổ sung kali, canxi.\n"
        "4. Thoát nước tốt mùa mưa."
    ),
    treatment=(
        "Cắt bỏ lá, cành bị bệnh nặng đem tiêu hủy. Phun Copper hydroxide, Mancozeb hoặc Azoxystrobin + "
        "Difenoconazole, 7–10 ngày/lần, 2–3 lần, luân phiên hoạt chất. Dùng đúng liều và thời gian cách ly trên nhãn."
    ),
    stages=_stages(
        ("Cắt bỏ lá, cành bị loét, gom tiêu hủy; tỉa tán thông thoáng; khử trùng kéo cắt.",
         "Vết loét mới trên lá non và cành non.", "Không xuất hiện vết loét mới.",
         "Mưa nhiều và vết bệnh lan nhanh: chuyển giai đoạn 3."),
        ("Bón phân hữu cơ ủ Trichoderma; phun bổ sung kali, canxi qua lá.",
         "Tốc độ lan của vết bệnh cũ.", "Vết bệnh cũ khô, không lan.",
         "Không cải thiện sau 1 tuần: dùng thuốc."),
        ("Phun Copper hydroxide hoặc Mancozeb, hoặc Azoxystrobin + Difenoconazole, 2–3 lần cách 7–10 ngày.",
         "Vết bệnh mới sau mỗi lần phun.", "Không còn vết bệnh mới sau 2 tuần.",
         "Vẫn lan: chụp lại trên LEAF AI để đánh giá và đổi hoạt chất khác nhóm."),
    ),
    recovery="3–5 tuần (đánh giá trên lá mới).",
    criteria=("Không có vết loét mới trên đợt lá kế tiếp.", "Cành non không khô chết.", "Trái non không bị loét."),
    note="Vết bệnh cũ không mất; theo dõi đợt lá mới.",
    recovery_info="⏱️ Khống chế: 2–3 tuần.\n🌱 Lá mới sạch bệnh: 3–5 tuần.\n💡 Hạn chế vết thương là cách phòng tốt nhất.",
)

_dot = disease_entry(
    class_name=DOT,
    description=(
        "Đốm lá do nấm (thường gặp Cercospora, Phyllosticta) gây ra, phát triển khi ẩm độ cao, lá ướt lâu, vườn "
        "rậm. Bệnh làm giảm diện tích quang hợp, nặng gây vàng và rụng lá."
    ),
    symptoms=(
        "Nhiều đốm nhỏ tròn hoặc góc cạnh, màu nâu đỏ đến nâu sẫm, rải rác trên phiến lá; về sau tâm đốm xám, "
        "viền nâu đậm; nhiều đốm liên kết thành mảng."
    ),
    prevention=(
        "1. Tỉa cành, giữ tán thông thoáng.\n"
        "2. Thu gom lá bệnh rụng.\n"
        "3. Tưới gốc, tránh làm ướt tán lá chiều tối.\n"
        "4. Bón phân cân đối."
    ),
    treatment=(
        "Thu gom, tiêu hủy lá bệnh. Phun Mancozeb, Propineb, Azoxystrobin hoặc Difenoconazole khi bệnh chớm xuất "
        "hiện, 2 lần cách 7–10 ngày."
    ),
    stages=_stages(
        ("Thu gom lá bệnh, tỉa tán, giảm ẩm trong vườn.", "Số lá có đốm mới.", "Đốm mới giảm rõ.",
         "Thời tiết ẩm kéo dài: chuyển giai đoạn 2–3."),
        ("Phun chế phẩm Trichoderma hoặc Bacillus subtilis; bón hữu cơ, kali.", "Mật độ đốm trên lá non.", "Lá non sạch đốm.",
         "Không giảm: dùng thuốc."),
        ("Phun Mancozeb hoặc Propineb, luân phiên Azoxystrobin/Difenoconazole, 2 lần cách 7–10 ngày.",
         "Đốm mới sau phun.", "Không còn đốm mới sau 10–14 ngày.", "Vẫn lan: hỏi cán bộ BVTV."),
    ),
    recovery="2–4 tuần.",
    criteria=("Không có đốm mới trên lá non.", "Tỷ lệ lá rụng giảm.", "Cây ra lá mới khỏe."),
    note="Đốm cũ không mất; đánh giá trên lá mới.",
    recovery_info="⏱️ Khống chế: 1–2 tuần.\n🌱 Lá mới sạch: 2–4 tuần.\n💡 Giữ tán thông thoáng là quan trọng nhất.",
)

_rust = disease_entry(
    class_name=RUST,
    description=(
        "Do nấm gỉ sắt (Austropuccinia psidii) gây ra, tấn công lá non, đọt, hoa và trái non. Bệnh lây nhanh qua "
        "bào tử theo gió khi thời tiết mát, ẩm, sương nhiều."
    ),
    symptoms=(
        "Mặt lá có các đốm vàng nhạt, mặt dưới nổi ổ bào tử màu vàng cam đến nâu như bột gỉ sắt; lá non quăn, "
        "biến dạng, khô; lá già vàng loang và rụng sớm."
    ),
    prevention=(
        "1. Cắt bỏ đọt, lá bệnh và tiêu hủy.\n"
        "2. Tỉa tán thông thoáng; không trồng quá dày.\n"
        "3. Theo dõi kỹ các đợt lộc non khi trời mát ẩm."
    ),
    treatment=(
        "Cắt bỏ đọt bệnh. Phun Hexaconazole, Propiconazole, Azoxystrobin hoặc Mancozeb khi phát hiện ổ bệnh đầu "
        "tiên, 2–3 lần cách 7–10 ngày, luân phiên nhóm hoạt chất."
    ),
    stages=_stages(
        ("Cắt bỏ đọt, lá có ổ gỉ sắt; tỉa tán.", "Ổ bào tử mới ở mặt dưới lá non.", "Không thấy ổ bào tử mới.",
         "Trời mát ẩm kéo dài: chuyển giai đoạn 3 sớm."),
        ("Bón cân đối, tăng kali; phun lưu huỳnh vi lượng phòng bệnh trên lộc non.", "Mật độ ổ bệnh.", "Lộc non sạch bệnh.",
         "Bệnh lan: dùng thuốc đặc trị."),
        ("Phun Hexaconazole hoặc Propiconazole, luân phiên Azoxystrobin/Mancozeb, 2–3 lần cách 7–10 ngày.",
         "Ổ bào tử mới sau phun.", "Không còn ổ bào tử mới sau 2 tuần.",
         "Vẫn lan: chụp lại trên LEAF AI và đổi hoạt chất khác nhóm."),
    ),
    recovery="3–5 tuần (đánh giá trên lộc mới).",
    criteria=("Lộc non mới không có ổ gỉ sắt.", "Lá non phát triển bình thường.", "Hoa, trái non không bị bệnh."),
    note="Lá đã bệnh không hồi phục; bảo vệ đợt lộc mới.",
    recovery_info="⏱️ Khống chế: 2–3 tuần.\n🌱 Lộc mới sạch bệnh: 3–5 tuần.\n💡 Phun sớm khi thấy ổ bệnh đầu tiên.",
)

GUAVA_DISEASES = [
    anthracnose(ANTHRACNOSE, "ổi"),
    _canker,
    _dot,
    _rust,
]
