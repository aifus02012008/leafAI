"""Thư viện bệnh lá sầu riêng (Durio zibethinus).

⚠️ Nội dung tham khảo, cần chuyên gia BVTV rà soát trước khi phát hành chính thức.
class_name phải trùng giá trị trong label_map của app/core/crops.yaml.
"""
from __future__ import annotations

from app.db.seed._format import Stage, disease_entry
from app.db.seed.fruit_common import algal_leaf_spot, anthracnose

PHYTOPHTHORA = "Cháy lá do Phytophthora trên sầu riêng (Durian Phytophthora leaf blight)"
RHIZOCTONIA = "Cháy lá chết ngọn sầu riêng (Durian Rhizoctonia leaf blight)"
ANTHRACNOSE = "Thán thư sầu riêng (Durian anthracnose)"
ALGAL = "Đốm rong sầu riêng (Durian algal leaf spot)"
PSYLLID = "Rầy phấn trắng hại sầu riêng (Durian psyllid)"

_phytophthora = disease_entry(
    class_name=PHYTOPHTHORA,
    description=(
        "Do Phytophthora palmivora (nhóm nấm noãn) gây ra — tác nhân nguy hiểm nhất trên sầu riêng, "
        "gây thối rễ, nứt thân xì mủ, thối trái và cháy lá. Bệnh bùng phát mạnh trong mùa mưa, khi "
        "đất ngập úng, thoát nước kém và ẩm độ cao. Lá cháy hàng loạt thường là dấu hiệu bộ rễ hoặc "
        "thân đã nhiễm bệnh, cần kiểm tra cả gốc và thân."
    ),
    symptoms=(
        "Trên lá xuất hiện vết bệnh màu nâu sẫm, úng nước, thường bắt đầu từ chóp hoặc mép lá rồi lan "
        "nhanh thành mảng cháy không định hình, ranh giới giữa mô bệnh và mô khỏe không rõ. Lá héo, "
        "vàng rồi rụng hàng loạt, cành non có thể khô. Kiểm tra thân và gốc: vỏ chảy nhựa nâu đỏ "
        "(xì mủ), phần vỏ bên trong thối nâu; rễ tơ thối đen."
    ),
    prevention=(
        "1. Lên líp, đắp mô cao, khơi thông mương để vườn không đọng nước sau mưa.\n"
        "2. Bón vôi và phân hữu cơ hoai mục ủ nấm đối kháng Trichoderma định kỳ.\n"
        "3. Tỉa cành sát đất, giữ gốc thông thoáng; tủ gốc cách thân 20–30 cm.\n"
        "4. Tránh gây vết thương ở gốc, rễ khi làm cỏ, xới đất; khử trùng dụng cụ cắt tỉa.\n"
        "5. Phun hoặc tiêm phòng hoạt chất phosphonate vào đầu mùa mưa theo khuyến cáo."
    ),
    treatment=(
        "Cắt bỏ lá, cành bệnh đem tiêu hủy. Phun hoạt chất đặc trị Phytophthora: Fosetyl-aluminium, "
        "Metalaxyl-M + Mancozeb, Dimethomorph hoặc Potassium phosphonate (phun lá hoặc tiêm thân). "
        "Nếu thân xì mủ: cạo sạch phần vỏ bệnh rồi quét thuốc lên vết cạo. Nếu rễ nhiễm: tưới thuốc "
        "vào vùng rễ. Sau 7–10 ngày dùng thuốc hóa học, bổ sung Trichoderma để phục hồi rễ."
    ),
    stages=(
        Stage(
            "Ngày 1", "Kiểm tra toàn cây & khoanh vùng",
            "Kiểm tra lá, thân, gốc và rễ; cắt bỏ cành lá cháy; khơi rãnh thoát nước ngay nếu gốc đọng nước.",
            "Vết xì mủ trên thân, màu vỏ bên trong, tình trạng rễ tơ.",
            "Xác định được bệnh chỉ ở lá hay đã vào thân/rễ để chọn cách xử lý.",
            "Nếu thân đã xì mủ hoặc rễ thối, phải xử lý thân và rễ ngay, không chỉ phun lá.",
        ),
        Stage(
            "Ngày 2–3", "Phun & xử lý thuốc đặc trị",
            "Phun Fosetyl-aluminium hoặc Metalaxyl-M + Mancozeb ướt đều tán lá; cạo và quét thuốc vết xì mủ; tưới thuốc vùng rễ nếu cần.",
            "Tốc độ rụng lá và độ lan rộng của vết cháy.",
            "Lá ngừng cháy lan, vết xì mủ khô lại.",
            "Nếu mưa lớn trong 6 giờ sau phun, phun lại khi trời ráo.",
        ),
        Stage(
            "Ngày 10–14", "Phun luân phiên & phục hồi rễ",
            "Phun lần 2 bằng hoạt chất khác nhóm (Dimethomorph hoặc Potassium phosphonate); bón Trichoderma và phân hữu cơ hoai mục.",
            "Rễ tơ mới, đọt non mới.",
            "Rễ tơ trắng mới xuất hiện, cây bắt đầu nhú đọt.",
            "Nếu cây tiếp tục rụng lá, cân nhắc tiêm thân phosphonate theo hướng dẫn kỹ thuật.",
        ),
        Stage(
            "Ngày 15–45", "Nuôi cây & phòng tái nhiễm",
            "Bón phân cân đối, hạn chế đạm; duy trì thoát nước tốt; theo dõi chặt trong suốt mùa mưa.",
            "Vết xì mủ mới, lá cháy mới sau các đợt mưa.",
            "Cây ra đọt đều, lá xanh dày, vết cạo trên thân liền sẹo.",
            "Khi có đợt mưa dầm kéo dài, phun phòng nhắc lại.",
        ),
    ),
    recovery="6–10 tuần (lâu hơn nếu bệnh đã vào thân hoặc rễ).",
    criteria=(
        "Không còn lá cháy mới và không còn vết xì mủ đang chảy trên thân.",
        "Rễ tơ trắng mới phát triển, cây ra đọt non đều.",
        "Vết cạo trên thân khô, liền sẹo.",
    ),
    note="Cây đã mất nhiều rễ cần ít nhất một mùa để phục hồi năng suất; không nên để cây mang nhiều trái trong giai đoạn này.",
    recovery_info=(
        "⏱️ Thời gian khống chế bệnh: 2–3 tuần.\n"
        "🌱 Ra đọt và rễ mới: 4–6 tuần.\n"
        "🔄 Phục hồi hoàn toàn: 6–10 tuần trở lên.\n"
        "💡 Lưu ý: Thoát nước tốt là biện pháp quan trọng nhất; thuốc chỉ hiệu quả khi vườn không còn úng."
    ),
)

_rhizoctonia = disease_entry(
    class_name=RHIZOCTONIA,
    description=(
        "Do nấm Rhizoctonia solani gây ra, phổ biến trong mùa mưa ở vườn rậm rạp, ẩm độ cao. Nấm lan "
        "theo tơ nấm từ lá này sang lá khác, làm lá cháy, đọt non chết khô từ ngọn xuống."
    ),
    symptoms=(
        "Vết bệnh như bị bỏng nước sôi, màu nâu xám, lan từ chóp hoặc mép lá vào trong. Các lá bệnh "
        "dính chùm lại với nhau bởi lớp tơ nấm màu trắng đến nâu; lá khô nhưng thường còn treo trên "
        "cành. Đọt non và cành non chết khô từ ngọn."
    ),
    prevention=(
        "1. Tỉa cành tạo tán thông thoáng, đặc biệt trước mùa mưa.\n"
        "2. Cắt bỏ cành lá bệnh, không để lá bệnh treo trên cây.\n"
        "3. Bón phân cân đối, không bón thừa đạm.\n"
        "4. Phun phòng khi thời tiết mưa nhiều, ẩm độ cao kéo dài."
    ),
    treatment=(
        "Cắt bỏ cành lá bị bệnh (kể cả chùm lá khô dính tơ nấm) đem tiêu hủy. Phun Validamycin, "
        "Hexaconazole hoặc Azoxystrobin + Difenoconazole; phun 2 lần cách nhau 7–10 ngày."
    ),
    stages=(
        Stage(
            "Ngày 1–2", "Cắt bỏ nguồn bệnh",
            "Cắt bỏ chùm lá cháy dính tơ nấm và đọt khô, đem ra khỏi vườn tiêu hủy.",
            "Tơ nấm trắng/nâu trên lá và cành non.",
            "Không còn chùm lá khô dính tơ nấm trên cây.",
            "Nếu bệnh lan nhiều cây, phun thuốc ngay sau khi cắt tỉa.",
        ),
        Stage(
            "Ngày 2–5", "Phun thuốc đặc trị lần 1",
            "Phun Validamycin hoặc Hexaconazole theo liều khuyến cáo, ướt đều tán lá.",
            "Vết cháy mới trên lá kế cận.",
            "Vết bệnh ngừng lan, tơ nấm khô lại.",
            "Nếu mưa trong vòng 4–6 giờ sau phun, phun lại.",
        ),
        Stage(
            "Ngày 10–14", "Phun luân phiên & nuôi đọt mới",
            "Phun lần 2 bằng hoạt chất khác nhóm (Azoxystrobin + Difenoconazole); bổ sung phân bón lá.",
            "Đọt non mới.",
            "Đọt mới phát triển bình thường, không chết ngọn.",
            "Nếu vẫn có lá cháy mới, kiểm tra lại độ thông thoáng của tán.",
        ),
    ),
    recovery="3–5 tuần.",
    criteria=(
        "Không còn lá cháy mới và tơ nấm trên cây.",
        "Đọt non mới phát triển bình thường.",
        "Không còn chùm lá khô treo trên cành.",
    ),
    note="Cành đã chết khô không hồi phục; cây sẽ bật chồi mới từ các mắt ngủ bên dưới.",
    recovery_info=(
        "⏱️ Thời gian khống chế bệnh: 7–14 ngày.\n"
        "🌱 Đọt mới: 3–4 tuần.\n"
        "💡 Lưu ý: Tỉa thông thoáng trước mùa mưa giúp giảm mạnh nguy cơ tái phát."
    ),
)

_psyllid = disease_entry(
    class_name=PSYLLID,
    description=(
        "Rầy phấn trắng (Allocaridara malayensis) chích hút nhựa lá non và đọt non sầu riêng. Rầy non "
        "tiết sáp trắng như bông và mật ngọt, tạo điều kiện cho nấm bồ hóng phát triển. Rầy gây hại "
        "nặng vào các đợt cây ra đọt non."
    ),
    symptoms=(
        "Lá non có chấm vàng do chích hút, quăn queo, biến dạng, cháy mép rồi rụng. Mặt dưới lá và đọt "
        "non có lớp sáp trắng như bông, kèm mật ngọt và muội đen (bồ hóng). Đọt non chậm phát triển."
    ),
    prevention=(
        "1. Điều khiển cho cây ra đọt tập trung để dễ quản lý rầy.\n"
        "2. Kiểm tra đọt non thường xuyên trong mỗi đợt ra đọt.\n"
        "3. Bảo vệ thiên địch (bọ rùa, nhện, ong ký sinh); hạn chế phun thuốc phổ rộng không cần thiết.\n"
        "4. Tỉa bỏ đọt lai rai, đọt bị hại nặng."
    ),
    treatment=(
        "Phun khi đọt non vừa nhú và khi phát hiện rầy: dầu khoáng, Imidacloprid, Thiamethoxam, "
        "Dinotefuran hoặc Abamectin; phun kỹ mặt dưới lá và đọt non, luân phiên hoạt chất."
    ),
    stages=(
        Stage(
            "Ngày 1", "Kiểm tra đọt non & đánh giá mật độ rầy",
            "Kiểm tra mặt dưới lá non và đọt non; tỉa bỏ đọt bị hại nặng.",
            "Lớp sáp trắng, rầy non và rầy trưởng thành trên đọt.",
            "Xác định được mức độ gây hại để quyết định phun.",
            "Nếu trên 10–20% đọt có rầy, tiến hành phun ngay.",
        ),
        Stage(
            "Ngày 2–3", "Phun trừ rầy lần 1",
            "Phun Thiamethoxam hoặc Imidacloprid kết hợp dầu khoáng, phun kỹ mặt dưới lá và đọt non.",
            "Rầy sống sót và sáp trắng mới.",
            "Mật độ rầy giảm mạnh, không còn sáp trắng mới.",
            "Nếu trời mưa ngay sau phun, phun lại khi trời ráo.",
        ),
        Stage(
            "Ngày 7–10", "Phun luân phiên & xử lý bồ hóng",
            "Phun lần 2 bằng hoạt chất khác nhóm (Dinotefuran hoặc Abamectin); rửa lá nếu có bồ hóng.",
            "Rầy non mới nở trên đọt.",
            "Đọt non mới phát triển bình thường, lá không còn quăn.",
            "Tiếp tục theo dõi ở đợt ra đọt kế tiếp.",
        ),
    ),
    recovery="2–4 tuần (đợt đọt mới).",
    criteria=(
        "Không còn rầy và sáp trắng trên đọt non.",
        "Đọt non mới ra lá xanh, không quăn queo.",
        "Không còn mật ngọt và bồ hóng mới.",
    ),
    note="Lá đã quăn không phẳng lại được; đánh giá dựa trên đợt đọt mới.",
    recovery_info=(
        "⏱️ Thời gian khống chế: 7–10 ngày.\n"
        "🌱 Đợt đọt mới sạch rầy: 2–4 tuần.\n"
        "💡 Lưu ý: Phun phòng đúng lúc đọt non vừa nhú là thời điểm hiệu quả nhất."
    ),
)

DURIAN_DISEASES = [
    _phytophthora,
    _rhizoctonia,
    anthracnose(ANTHRACNOSE, "sầu riêng"),
    algal_leaf_spot(ALGAL, "sầu riêng"),
    _psyllid,
]
