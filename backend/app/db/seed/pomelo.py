"""Thư viện bệnh, sâu hại trên lá bưởi (Citrus maxima).

⚠️ Nội dung tham khảo, cần chuyên gia BVTV rà soát trước khi phát hành chính thức.
Model bưởi được huấn luyện trên ảnh lá chanh (cùng chi Citrus) vì chưa có bộ ảnh lá bưởi công khai;
class_name phải trùng giá trị trong label_map của app/core/crops.yaml.
"""
from __future__ import annotations

from app.db.seed._format import Stage, disease_entry
from app.db.seed.fruit_common import anthracnose

ANTHRACNOSE = "Thán thư bưởi (Pomelo anthracnose)"
CANKER = "Loét lá bưởi (Citrus canker)"
GREENING = "Vàng lá gân xanh bưởi (Citrus greening / HLB)"
LEAFMINER = "Sâu vẽ bùa hại bưởi (Citrus leafminer)"
LEAF_CURL = "Xoăn lá bưởi do chích hút (Citrus leaf curl)"
SWALLOWTAIL = "Sâu xanh bướm phượng ăn lá bưởi (Swallowtail caterpillar)"


def _stages(cultural: tuple[str, str, str, str], bio: tuple[str, str, str, str], chem: tuple[str, str, str, str]) -> tuple[Stage, ...]:
    """(action, monitoring, improvement, extra) for the cultural → biological → chemical stages."""
    return (
        Stage("Ngày 1–3", "Canh tác — Vệ sinh vườn, cắt bỏ nguồn bệnh", *cultural),
        Stage("Ngày 3–7", "Sinh học — Thiên địch và chế phẩm sinh học", *bio),
        Stage("Ngày 7–21", "Hóa học — Phun thuốc khi thật sự cần", *chem),
    )


_canker = disease_entry(
    class_name=CANKER,
    description=(
        "Do vi khuẩn Xanthomonas citri subsp. citri gây ra. Vi khuẩn xâm nhập qua khí khổng và vết thương "
        "(đặc biệt vết đục của sâu vẽ bùa), lây lan mạnh theo mưa kèm gió và dụng cụ cắt tỉa. Bệnh gây hại lá, "
        "cành non và trái, làm rụng lá, trái bị sần sẹo mất giá trị thương phẩm."
    ),
    symptoms=(
        "Đốm nhỏ màu vàng nhạt, sau thành vết loét nâu, nổi gồ sần sùi như vảy, giữa vết bệnh nứt, có quầng "
        "vàng bao quanh rõ. Vết bệnh xuất hiện ở cả hai mặt lá, thường tập trung ở lá non và chỗ sâu vẽ bùa đục."
    ),
    prevention=(
        "1. Trồng cây giống sạch bệnh; trồng cây chắn gió quanh vườn.\n"
        "2. Quản lý sâu vẽ bùa trên các đợt lộc non để hạn chế vết thương.\n"
        "3. Cắt tỉa cành bệnh sau thu hoạch, khử trùng dụng cụ bằng cồn hoặc nước Javel loãng.\n"
        "4. Bón phân cân đối, không bón thừa đạm làm lộc non ra liên tục.\n"
        "5. Phun phòng thuốc gốc đồng khi lộc non vừa nhú trong mùa mưa."
    ),
    treatment=(
        "Cắt bỏ lá, cành bị loét nặng đem tiêu hủy. Phun thuốc gốc đồng (Copper hydroxide, Copper oxychloride) "
        "lúc lộc non và sau các trận mưa lớn, 7–10 ngày/lần, 2–3 lần. Kết hợp trừ sâu vẽ bùa. "
        "Dùng đúng liều và thời gian cách ly ghi trên nhãn."
    ),
    stages=_stages(
        ("Cắt bỏ lá, cành bị loét, gom tiêu hủy; khử trùng kéo cắt; tránh tưới phun lên tán.",
         "Vết loét mới trên lá non và cành non.", "Lộc non mới không xuất hiện vết loét.",
         "Gặp mưa kèm gió hoặc vết loét lan nhanh thì chuyển ngay sang giai đoạn hóa học."),
        ("Bón phân hữu cơ, bổ sung kali và canxi cho lá dày; bảo vệ thiên địch của sâu vẽ bùa (ong ký sinh, kiến vàng).",
         "Mật độ sâu vẽ bùa trên lộc non.", "Lộc non ít vết đục, ít vết loét mới.",
         "Nếu lộc non ra rộ trong mùa mưa, phun phòng bằng thuốc gốc đồng."),
        ("Phun Copper hydroxide hoặc Copper oxychloride ướt đều hai mặt lá, 7–10 ngày/lần, 2–3 lần; tránh phun lúc nắng gắt.",
         "Vết loét mới sau mỗi lần phun.", "Không còn vết loét mới sau 2 tuần.",
         "Bệnh vẫn lan: chụp lại lá trên LEAF AI và hỏi cán bộ BVTV; không lạm dụng thuốc đồng gây cháy lá non."),
    ),
    recovery="3–6 tuần (đánh giá trên đợt lộc mới).",
    criteria=("Không có vết loét mới trên đợt lộc kế tiếp.", "Lá non phát triển bình thường, không rụng.", "Trái non không bị đốm loét."),
    note="Vết loét cũ không mất; quản lý tốt sâu vẽ bùa là chìa khóa phòng loét.",
    recovery_info="⏱️ Khống chế: 2–3 tuần.\n🌱 Lộc mới sạch bệnh: 4–6 tuần.\n💡 Phun phòng ngay khi lộc non vừa nhú trong mùa mưa.",
)

_greening = disease_entry(
    class_name=GREENING,
    description=(
        "Bệnh nguy hiểm nhất trên cây có múi, do vi khuẩn Candidatus Liberibacter asiaticus sống trong mạch "
        "dẫn, lây qua rầy chổng cánh (Diaphorina citri) và cây giống nhiễm bệnh. HIỆN CHƯA CÓ THUỐC CHỮA: cây "
        "bệnh suy kiệt dần, trái nhỏ, méo, lệch tâm, chua."
    ),
    symptoms=(
        "Lá vàng loang lổ không đối xứng hai bên gân chính, gân lá còn xanh hoặc vàng; lá nhỏ, dày, mọc thẳng "
        "đứng, có thể giống thiếu kẽm. Bệnh thường bắt đầu từ một cành rồi lan ra cả cây; cây ra hoa trái vụ, rụng trái."
    ),
    prevention=(
        "1. Chỉ trồng cây giống sạch bệnh có nguồn gốc rõ ràng.\n"
        "2. Trừ rầy chổng cánh vào mỗi đợt lộc non; trồng ổi xen có thể giúp xua rầy.\n"
        "3. Kiểm tra vườn định kỳ, nhổ bỏ sớm cây có triệu chứng.\n"
        "4. Không lấy mắt ghép từ cây nghi bệnh."
    ),
    treatment=(
        "Không có thuốc đặc trị vi khuẩn. Nhổ bỏ và tiêu hủy cây bệnh nặng để cắt nguồn lây; trừ rầy chổng cánh "
        "bằng Thiamethoxam, Imidacloprid, Dinotefuran (luân phiên) hoặc dầu khoáng vào đầu mỗi đợt lộc; "
        "bón phân, bổ sung vi lượng để kéo dài sức sống cây mới nhiễm nhẹ."
    ),
    stages=_stages(
        ("Đánh dấu cây nghi bệnh; nhổ bỏ, tiêu hủy cây bệnh nặng; không lấy mắt ghép từ cây bệnh.",
         "Số cây có lá vàng loang không đối xứng.", "Không xuất hiện thêm cây mới có triệu chứng.",
         "Phát hiện rầy chổng cánh trên lộc non thì làm ngay giai đoạn 2–3."),
        ("Phun dầu khoáng xua rầy trên lộc non; bảo vệ thiên địch (bọ rùa, ong ký sinh Tamarixia); bón hữu cơ, vi lượng.",
         "Mật độ rầy chổng cánh trên lộc non.", "Lộc non sạch rầy.",
         "Mật độ rầy cao: dùng thuốc trừ rầy ở giai đoạn 3."),
        ("Trừ rầy chổng cánh bằng Thiamethoxam hoặc Dinotefuran, luân phiên nhóm khác; phun đồng loạt cả khu vực.",
         "Rầy sau mỗi lần phun; triệu chứng trên cây còn lại.", "Không còn rầy, không thêm cây bệnh.",
         "Xác nhận bệnh bằng xét nghiệm PCR tại trạm BVTV nếu chưa chắc chắn."),
    ),
    recovery="Không phục hồi: cây bệnh cần loại bỏ; mục tiêu là bảo vệ cây khỏe còn lại.",
    criteria=("Không phát sinh cây bệnh mới trong vườn.", "Rầy chổng cánh được kiểm soát trên mọi đợt lộc.", "Cây khỏe giữ được năng suất."),
    note="Đây là bệnh phải quản lý cả vùng: phối hợp với các vườn lân cận trừ rầy cùng lúc.",
    recovery_info="⏱️ Không chữa được: nhổ bỏ cây bệnh.\n🌱 Bảo vệ cây khỏe bằng trừ rầy mỗi đợt lộc.\n💡 Nên xét nghiệm PCR để xác nhận.",
)

_leafminer = disease_entry(
    class_name=LEAFMINER,
    description=(
        "Sâu non của bướm Phyllocnistis citrella đục dưới biểu bì lá non tạo đường hầm ngoằn ngoèo. Gây hại "
        "nặng trên các đợt lộc non, làm lá quăn, giảm quang hợp và tạo vết thương cho vi khuẩn loét xâm nhập."
    ),
    symptoms=(
        "Đường vẽ màu trắng bạc, ngoằn ngoèo như hình vẽ bùa dưới biểu bì lá non; lá cong, xoăn, biến dạng; "
        "cuối đường đục thường thấy nhộng ở mép lá cuộn lại."
    ),
    prevention=(
        "1. Điều khiển cho cây ra lộc tập trung để dễ quản lý.\n"
        "2. Cắt bỏ các chồi vượt, lộc lai rai.\n"
        "3. Bảo vệ thiên địch: ong ký sinh, kiến vàng.\n"
        "4. Kiểm tra lộc non 2–3 ngày/lần khi lộc vừa nhú."
    ),
    treatment=(
        "Phun khi lộc non dài 1–3 cm: dầu khoáng, Abamectin, Spinetoram hoặc Emamectin benzoate; phun lại sau "
        "7 ngày nếu lộc còn non; luân phiên hoạt chất khác nhóm. Thuốc chỉ hiệu quả khi phun đúng lúc lộc non."
    ),
    stages=_stages(
        ("Cắt bỏ chồi vượt, lộc lai rai bị hại; tưới, bón để cây ra lộc đồng loạt.",
         "Tỷ lệ lá non có đường vẽ bùa.", "Đợt lộc mới ít đường đục.",
         "Lộc non vừa nhú và thấy trứng/đường đục mới thì phun ngay."),
        ("Phun dầu khoáng xua bướm đẻ trứng; bảo vệ ong ký sinh, kiến vàng.",
         "Đường đục mới trên lá non.", "Mật độ sâu giảm, lá non phẳng.",
         "Mật độ cao trên lộc non: dùng thuốc ở giai đoạn 3."),
        ("Phun Abamectin hoặc Spinetoram khi lộc dài 1–3 cm, lặp lại sau 7 ngày; luân phiên nhóm.",
         "Sâu sống trong đường đục (đường đục còn ẩm, có sâu).", "Không có đường đục mới sau 1–2 tuần.",
         "Hiệu quả kém: kiểm tra thời điểm phun (phải lúc lộc non) và đổi hoạt chất khác nhóm."),
    ),
    recovery="2–3 tuần (đánh giá trên đợt lộc kế tiếp).",
    criteria=("Lộc non mới không có đường vẽ bùa.", "Lá non phát triển phẳng, không xoăn.", "Không phát sinh vết loét trên lá bị đục."),
    note="Lá đã bị đục không hồi phục; trọng tâm là bảo vệ đợt lộc mới.",
    recovery_info="⏱️ Khống chế: 1–2 tuần.\n🌱 Lộc mới sạch: 2–3 tuần.\n💡 Phun đúng lúc lộc non 1–3 cm là quan trọng nhất.",
)

_leaf_curl = disease_entry(
    class_name=LEAF_CURL,
    description=(
        "Lá bưởi xoăn, biến dạng thường do côn trùng chích hút (rệp muội, rầy chổng cánh, bọ trĩ, nhện) gây hại "
        "lộc non; đôi khi do virus lây qua rệp. Cây bị nặng ra lộc kém, giảm sức sinh trưởng."
    ),
    symptoms=(
        "Lá non xoăn, quăn, cong queo, nhăn nheo, có thể có đốm vàng hoặc vết chích; mặt dưới lá có rệp, nhện "
        "hoặc bọ trĩ; có mật ngọt và nấm bồ hóng đi kèm."
    ),
    prevention=(
        "1. Kiểm tra mặt dưới lá non thường xuyên.\n"
        "2. Bón phân cân đối, tránh thừa đạm.\n"
        "3. Bảo vệ thiên địch: bọ rùa, ruồi ăn rệp, nhện bắt mồi.\n"
        "4. Tưới đủ ẩm mùa khô (nhện và bọ trĩ phát triển mạnh khi khô hạn)."
    ),
    treatment=(
        "Xác định tác nhân trước khi phun: rệp, rầy dùng Thiamethoxam, Pymetrozine hoặc dầu khoáng; nhện dùng "
        "Abamectin, Hexythiazox; bọ trĩ dùng Spinetoram, Abamectin. Phun mặt dưới lá, luân phiên hoạt chất."
    ),
    stages=_stages(
        ("Cắt bỏ đọt bị hại nặng; tưới đủ ẩm; vệ sinh cỏ dại là nơi trú ẩn của côn trùng.",
         "Loại côn trùng ở mặt dưới lá non.", "Lá non mới ra phẳng, không xoăn.",
         "Mật độ côn trùng tăng nhanh: chuyển giai đoạn 2–3."),
        ("Phun dầu khoáng hoặc nước xà phòng loãng; thả hoặc bảo vệ bọ rùa, nhện bắt mồi.",
         "Mật độ rệp, nhện, bọ trĩ.", "Mật độ giảm rõ sau 1 tuần.",
         "Không giảm: dùng thuốc đặc hiệu ở giai đoạn 3."),
        ("Phun thuốc theo tác nhân (rệp/rầy: Thiamethoxam, Pymetrozine; nhện: Abamectin, Hexythiazox; bọ trĩ: Spinetoram).",
         "Côn trùng sống sau mỗi lần phun.", "Không còn côn trùng, lá mới phẳng.",
         "Lá xoăn kèm khảm vàng không do côn trùng: có thể do virus, liên hệ cán bộ BVTV."),
    ),
    recovery="2–4 tuần (lá xoăn cũ không phẳng lại).",
    criteria=("Lá non mới phẳng, xanh đều.", "Không còn côn trùng chích hút trên lộc non.", "Không còn mật ngọt và bồ hóng mới."),
    note="Lá đã xoăn không hồi phục; đánh giá trên đợt lộc mới.",
    recovery_info="⏱️ Khống chế: 1–2 tuần.\n🌱 Lộc mới bình thường: 2–4 tuần.\n💡 Xác định đúng loại côn trùng để chọn thuốc.",
)

_swallowtail = disease_entry(
    class_name=SWALLOWTAIL,
    description=(
        "Sâu non của bướm phượng (Papilio spp.) ăn khuyết lá non và lá bánh tẻ, nặng có thể ăn trụi đọt non, "
        "ảnh hưởng nhiều đến cây con và vườn mới trồng."
    ),
    symptoms=(
        "Lá bị ăn khuyết từ mép vào thành những vết khuyết lớn, cong; trên cành có sâu non màu nâu đen loang trắng "
        "(giống phân chim) khi nhỏ và màu xanh lá khi lớn, có sừng đỏ khi bị động."
    ),
    prevention=(
        "1. Kiểm tra lộc non, bắt sâu và ngắt trứng bằng tay (vườn nhỏ).\n"
        "2. Bảo vệ thiên địch: ong ký sinh, chim.\n"
        "3. Phát hiện sớm khi sâu còn nhỏ."
    ),
    treatment=(
        "Bắt sâu bằng tay là hiệu quả với vườn nhỏ. Khi mật độ cao: phun chế phẩm Bacillus thuringiensis (Bt) "
        "lúc sâu còn nhỏ, hoặc Spinetoram, Emamectin benzoate theo nhãn."
    ),
    stages=_stages(
        ("Bắt sâu, ngắt trứng trên lộc non; cắt đọt bị ăn trụi.",
         "Số sâu non trên cây con và lộc non.", "Không còn lá bị ăn khuyết mới.",
         "Vườn lớn, sâu nhiều: dùng chế phẩm sinh học."),
        ("Phun chế phẩm Bt khi sâu tuổi nhỏ, chiều mát; bảo vệ ong ký sinh.",
         "Sâu chết, ngừng ăn sau 1–2 ngày.", "Lá mới không bị ăn khuyết.",
         "Sâu tuổi lớn, mật độ cao: dùng thuốc ở giai đoạn 3."),
        ("Phun Spinetoram hoặc Emamectin benzoate theo nhãn, ướt đều tán lá non.",
         "Sâu sống sau phun.", "Không còn sâu sau 3–5 ngày.",
         "Hiếm khi cần phun lại; ưu tiên biện pháp thủ công và sinh học."),
    ),
    recovery="1–2 tuần (cây ra lộc mới).",
    criteria=("Không còn sâu trên cây.", "Lộc non mới không bị ăn khuyết.", "Cây con phục hồi tán lá."),
    note="Lá bị ăn khuyết không hồi phục; cây sẽ bù lại bằng lộc mới.",
    recovery_info="⏱️ Khống chế: vài ngày.\n🌱 Lộc mới: 1–2 tuần.\n💡 Bắt sâu bằng tay là cách rẻ và an toàn nhất.",
)

POMELO_DISEASES = [
    anthracnose(ANTHRACNOSE, "bưởi"),
    _canker,
    _greening,
    _leafminer,
    _leaf_curl,
    _swallowtail,
]
