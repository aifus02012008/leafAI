"""Bệnh lá dùng chung cho các cây ăn trái (sầu riêng, măng cụt, chôm chôm).

Đốm rong, thán thư và bồ hóng có cùng tác nhân/cách xử lý trên nhiều cây ăn trái;
các hàm dưới đây sinh nội dung theo tên cây để tránh lặp văn bản.
⚠️ Nội dung tham khảo, cần chuyên gia BVTV rà soát trước khi phát hành chính thức.
"""
from __future__ import annotations

from app.db.seed._format import Stage, disease_entry


def algal_leaf_spot(class_name: str, tree: str) -> dict:
    return disease_entry(
        class_name=class_name,
        description=(
            f"Bệnh đốm rong (đốm tảo) trên {tree} do tảo ký sinh Cephaleuros virescens gây ra. "
            "Bệnh phổ biến ở vườn già, rậm rạp, ẩm độ cao và thiếu ánh sáng; lây lan qua bào tử "
            "theo nước mưa và gió. Bệnh ít khi làm chết cây nhưng làm giảm diện tích quang hợp, "
            "cây suy yếu và là dấu hiệu vườn quá ẩm, thiếu thông thoáng."
        ),
        symptoms=(
            "Đốm tròn nhỏ 2–10 mm, hơi nổi gồ trên mặt lá (chủ yếu mặt trên lá già), bề mặt mịn "
            "như nhung. Lúc đầu màu xanh xám, khi sinh bào tử chuyển sang màu cam hoặc màu gỉ sắt. "
            "Các đốm có thể liên kết thành mảng; mô lá dưới đốm chuyển vàng nâu."
        ),
        prevention=(
            "1. Tỉa cành tạo tán thông thoáng, cắt bỏ cành vượt, cành trong tán để ánh sáng lọt vào.\n"
            "2. Giữ mật độ trồng hợp lý, làm sạch cỏ và khơi thông mương thoát nước để giảm ẩm độ vườn.\n"
            "3. Bón phân cân đối, tăng hữu cơ và kali để cây khỏe.\n"
            "4. Thu gom lá bệnh rụng dưới gốc đem tiêu hủy."
        ),
        treatment=(
            "Tỉa bỏ lá, cành bị nặng. Phun thuốc gốc đồng (Copper hydroxide, Copper oxychloride) "
            "ướt đều cả hai mặt lá, phun 2 lần cách nhau 10–15 ngày vào lúc trời khô ráo."
        ),
        stages=(
            Stage(
                "Ngày 1–3", "Vệ sinh vườn & tỉa thông thoáng",
                "Tỉa cành tăm, cành sâu bệnh, cành trong tán; thu gom lá bệnh rụng đem tiêu hủy.",
                "Mật độ đốm rong trên lá già ở tầng tán dưới, nơi khuất sáng.",
                "Tán cây thông thoáng, ánh nắng chiếu được vào bên trong tán.",
                "Nếu đốm phủ trên 20% số lá, chuyển ngay sang phun thuốc gốc đồng.",
            ),
            Stage(
                "Ngày 4–7", "Phun thuốc gốc đồng lần 1",
                "Phun Copper hydroxide hoặc Copper oxychloride theo liều trên nhãn, ướt đều hai mặt lá.",
                "Màu sắc của các đốm (cam tươi là đang sinh bào tử).",
                "Đốm khô lại, chuyển màu xám nhạt, không lan sang lá mới.",
                "Nếu mưa trong vòng 4–6 giờ sau phun, phun lại khi trời ráo.",
            ),
            Stage(
                "Ngày 15–20", "Phun nhắc lại & bồi dưỡng cây",
                "Phun thuốc gốc đồng lần 2; bón bổ sung phân hữu cơ, kali giúp cây ra lá mới khỏe.",
                "Lá non mới ra có xuất hiện đốm mới hay không.",
                "Không còn đốm mới trên lá non; lá mới xanh bóng.",
                "Nếu vẫn xuất hiện đốm mới, kiểm tra lại độ ẩm vườn và độ thông thoáng của tán.",
            ),
        ),
        recovery="3–6 tuần.",
        criteria=(
            "Không xuất hiện đốm rong mới trên lá non trong 3 tuần liên tiếp.",
            "Các đốm cũ đã khô, xám lại, không còn lớp nhung màu cam.",
            "Tán cây thông thoáng, ẩm độ trong vườn giảm rõ rệt.",
        ),
        note="Vết đốm cũ trên lá già không biến mất; cây được coi là khỏi khi bệnh ngừng lây sang lá mới.",
        recovery_info=(
            "⏱️ Thời gian khống chế bệnh: 2–3 tuần.\n"
            "🌱 Lá mới sạch bệnh: 3–4 tuần.\n"
            "💡 Lưu ý: Đốm cũ trên lá già vẫn còn dấu vết; quan trọng là lá mới không bị nhiễm."
        ),
    )


def anthracnose(class_name: str, tree: str) -> dict:
    return disease_entry(
        class_name=class_name,
        description=(
            f"Bệnh thán thư trên {tree} do nấm Colletotrichum gloeosporioides gây ra. Nấm tấn công "
            "lá non, đọt non, hoa và trái; phát triển mạnh khi mưa nhiều, ẩm độ cao, nhiệt độ "
            "25–30°C. Bào tử lây lan nhanh theo nước mưa và nước tưới văng."
        ),
        symptoms=(
            "Đốm màu nâu đến nâu đen, hình tròn hoặc bất định, thường bắt đầu từ chóp hoặc mép lá. "
            "Vết bệnh lan rộng thành mảng cháy khô, có thể có vòng đồng tâm và viền vàng bao quanh; "
            "trên vết bệnh già có các chấm đen li ti (ổ bào tử). Lá non bị biến dạng, cháy khô và rụng."
        ),
        prevention=(
            "1. Tỉa cành sau thu hoạch, cắt bỏ cành lá bệnh, tạo tán thông thoáng.\n"
            "2. Phun phòng khi cây ra đọt non và trong mùa mưa.\n"
            "3. Tránh tưới phun mưa lên tán lá vào chiều tối.\n"
            "4. Bón phân cân đối, không bón thừa đạm làm đọt non mềm yếu."
        ),
        treatment=(
            "Cắt bỏ lá, đọt bệnh đem tiêu hủy. Phun một trong các hoạt chất: Azoxystrobin + "
            "Difenoconazole, Propineb, Mancozeb hoặc thuốc gốc đồng; phun 2–3 lần cách nhau 7–10 ngày."
        ),
        stages=(
            Stage(
                "Ngày 1–2", "Khoanh vùng & cắt bỏ nguồn bệnh",
                "Cắt bỏ lá, đọt bị bệnh nặng, thu gom lá rụng đem tiêu hủy, không để lại trong vườn.",
                "Tỷ lệ lá non, đọt non có vết cháy nâu.",
                "Xác định được các cây và khu vực bị nặng để tập trung xử lý.",
                "Nếu trên 30% đọt non bị bệnh, phun thuốc ngay trong ngày.",
            ),
            Stage(
                "Ngày 3–7", "Phun thuốc đặc trị lần 1",
                "Phun Azoxystrobin + Difenoconazole hoặc Propineb theo liều khuyến cáo, ướt đều tán lá.",
                "Vết bệnh cũ có tiếp tục lan rộng hay xuất hiện vết mới.",
                "Vết bệnh khô lại, không còn viền úng nước lan rộng.",
                "Nếu mưa kéo dài, rút ngắn khoảng cách phun lần 2 còn 7 ngày.",
            ),
            Stage(
                "Ngày 10–17", "Phun luân phiên hoạt chất & nuôi đọt mới",
                "Phun lần 2 bằng hoạt chất khác nhóm (ví dụ Mancozeb hoặc thuốc gốc đồng); bổ sung phân bón lá trung vi lượng.",
                "Đọt non mới ra có sạch bệnh hay không.",
                "Đọt mới phát triển xanh tốt, không còn vết cháy mới.",
                "Nếu vẫn có vết bệnh mới, phun thêm lần 3 và kiểm tra lại độ thông thoáng vườn.",
            ),
        ),
        recovery="3–5 tuần.",
        criteria=(
            "Không xuất hiện vết bệnh mới trên lá non và đọt non trong 2–3 tuần.",
            "Vết bệnh cũ đã khô, không còn lan rộng.",
            "Cây ra đợt đọt mới khỏe, xanh đều.",
        ),
        note="Lá đã cháy không xanh lại được; đánh giá khỏi bệnh dựa trên lá và đọt mới.",
        recovery_info=(
            "⏱️ Thời gian khống chế bệnh: 7–14 ngày.\n"
            "🌱 Đợt đọt non mới: 3–4 tuần.\n"
            "💡 Lưu ý: Phòng bệnh ngay từ khi cây ra đọt non hiệu quả hơn nhiều so với trị khi bệnh đã nặng."
        ),
    )


def sooty_mold(class_name: str, tree: str) -> dict:
    return disease_entry(
        class_name=class_name,
        description=(
            f"Bệnh bồ hóng (muội đen) trên {tree} do nhóm nấm hoại sinh (như Capnodium spp.) phát triển "
            "trên lớp mật ngọt do côn trùng chích hút tiết ra (rệp sáp, rệp vảy, rầy mềm, rầy phấn). "
            "Nấm không ký sinh trực tiếp vào mô lá nhưng phủ kín mặt lá, làm giảm quang hợp và cây suy yếu."
        ),
        symptoms=(
            "Mặt lá phủ một lớp muội màu đen như bồ hóng bếp, có thể bóc hoặc lau ra được, để lại mặt "
            "lá còn xanh bên dưới. Thường đi kèm côn trùng chích hút ở mặt dưới lá, đọt non hoặc trên cành, "
            "và có kiến bò nhiều (kiến ăn mật ngọt)."
        ),
        prevention=(
            "1. Kiểm tra định kỳ và quản lý sớm côn trùng chích hút (rệp sáp, rệp vảy, rầy).\n"
            "2. Quản lý kiến vì kiến bảo vệ và phát tán rệp.\n"
            "3. Tỉa cành thông thoáng, hạn chế ẩm độ trong tán.\n"
            "4. Bảo vệ thiên địch như bọ rùa, ong ký sinh."
        ),
        treatment=(
            "Xử lý tận gốc côn trùng chích hút bằng dầu khoáng hoặc hoạt chất phù hợp (Buprofezin, "
            "Spirotetramat...). Sau đó rửa trôi lớp muội bằng nước sạch hoặc nước pha xà phòng loãng; "
            "có thể phun thuốc gốc đồng nếu muội phủ dày."
        ),
        stages=(
            Stage(
                "Ngày 1–3", "Xác định & diệt côn trùng chích hút",
                "Tìm rệp sáp, rệp vảy, rầy ở mặt dưới lá và cành; phun dầu khoáng hoặc thuốc đặc trị phù hợp.",
                "Mật độ côn trùng chích hút và kiến trên cây.",
                "Côn trùng giảm rõ, không còn mật ngọt mới đọng trên lá.",
                "Nếu có nhiều kiến, xử lý kiến quanh gốc để chặn nguồn lây rệp.",
            ),
            Stage(
                "Ngày 5–10", "Làm sạch lớp muội đen",
                "Phun rửa lá bằng nước sạch hoặc nước xà phòng loãng; với muội dày có thể phun thuốc gốc đồng.",
                "Độ che phủ của lớp muội đen trên mặt lá.",
                "Lớp muội bong tróc dần, mặt lá xanh trở lại.",
                "Nếu muội vẫn tái xuất hiện, côn trùng chích hút chưa được diệt hết, cần phun nhắc lại.",
            ),
            Stage(
                "Ngày 14–21", "Theo dõi & phòng tái phát",
                "Kiểm tra lại côn trùng; phun nhắc dầu khoáng nếu còn; bón phân giúp cây phục hồi.",
                "Côn trùng chích hút trên đọt non mới.",
                "Lá mới sạch, không còn mật ngọt và muội.",
                "Duy trì kiểm tra định kỳ 1–2 tuần/lần trong mùa khô.",
            ),
        ),
        recovery="2–4 tuần.",
        criteria=(
            "Không còn côn trùng chích hút và mật ngọt trên lá.",
            "Lá mới ra sạch muội đen.",
            "Lớp muội trên lá cũ đã bong tróc phần lớn.",
        ),
        note="Bồ hóng chỉ khỏi hẳn khi diệt được côn trùng tiết mật ngọt.",
        recovery_info=(
            "⏱️ Thời gian khống chế: 1–2 tuần sau khi diệt côn trùng chích hút.\n"
            "🌱 Lá sạch trở lại: 2–4 tuần.\n"
            "💡 Lưu ý: Trị bồ hóng mà không trị rệp/rầy thì bệnh sẽ quay lại."
        ),
    )
