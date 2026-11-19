from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.user import User
from app.models.diagnosis import DiagnosisHistory
from app.models.detection import DetectionResult
from app.models.disease import Disease
from sqlalchemy import text, inspect
import logging

logger = logging.getLogger(__name__)

DISEASE_DATA = [
    {
        "class_name": "Bệnh rầy xanh (Tea green leafhopper)",
        "display_name": "Bệnh rầy xanh (Tea green leafhopper)",
        "description": "Bệnh rầy xanh hại chè (Tea green leafhopper) - Do rầy xanh (chủ yếu là loài Jacobiasca formosana hoặc Empoasca onukii / Empoasca flavescens thuộc họ Cicadellidae) gây ra. Đây là một trong ba đối tượng dịch hại nguy hiểm và phổ biến nhất trên cây chè (Camellia sinensis) tại Việt Nam. Cả rầy non và rầy trưởng thành dùng vòi chích hút nhựa tế bào ở búp non, gân chính và cuống lá non, đồng thời tiết độc tố làm mô lá tê liệt, khô xác và cong queo từ mép lá vào trong ('cháy rầy'), làm teo búp chè, giảm sút nghiêm trọng sản lượng và phẩm cấp hương vị của chè búp thương phẩm.",
        "symptoms": "Triệu chứng đặc trưng: Búp chè non và lá non chuyển sang màu xanh vàng nhạt, mép lá bị quăn lại hình lòng máng hoặc uốn lượn gợn sóng. Vết chích ban đầu là các chấm nhỏ li ti màu vàng hoặc nâu nhạt ở gân lá và mép lá. Khi mật độ rầy cao, mép lá và chóp lá non khô xác chuyển sang màu nâu đỏ hoặc nâu đen như bị hơ lửa (hiện tượng 'cháy mép lá' hay 'cháy rầy'). Búp chè non bị cằn cỗi, chùn đọt không phát triển được, đốt thân ngắn lại, lá dày cộm giòn và dễ rụng sớm. Khi lay động nhẹ tán chè, quan sát thấy các con rầy nhỏ màu xanh lá mạ bò nhanh sang ngang hoặc búng nhảy lẩn trốn dưới mặt lá.",
        "prevention": "1. Thu hái chè triệt để, hái kỹ búp non và lá bánh tẻ đúng chu kỳ nhằm ngắt đứt nguồn thức ăn và triệt tiêu các ổ trứng rầy đẻ rải rác trong cuống lá.\n2. Vệ sinh nương chè sạch sẽ, làm sạch cỏ dại quanh gốc chè và các bờ bụi rậm rạp xung quanh để tán chè luôn thông thoáng.\n3. Đốn chè đúng kỹ thuật, đúng thời vụ giúp cây tập trung dinh dưỡng và hạn chế nơi rầy ẩn nấp qua mùa đông.\n4. Bón phân cân đối N-P-K, tăng cường bón phân hữu cơ vi sinh, Silic và phân Kali nhằm tăng độ dày biểu bì lá, tuyệt đối không bón thừa đạm làm búp non mềm mọng nước.\n5. Đặt bẫy dính màu vàng trên nương chè để theo dõi mật độ và bẫy bắt rầy trưởng thành; bảo vệ các loài thiên địch tự nhiên như nhện bắt mồi, bọ rùa, chuồn chuồn cỏ và bọ xít bắt mồi.",
        "treatment": "Lộ trình điều trị toàn diện: Thường xuyên kiểm tra mật độ rầy (ngưỡng can thiệp: > 5 con/búp hoặc > 10% số búp bị hại). Tạm dừng thu hái búp non. Phun dập dịch đợt 1 bằng các hoạt chất đặc trị rầy sinh học và thế hệ mới: Flonicamid (Teppeki 50WG), Buprofezin (Applaud 10WP - ức chế lột xác), Pymetrozine (Chess 50WG) hoặc Emamectin benzoate phối hợp dầu khoáng (SK Enspray 99EC). Phun kỹ mặt dưới tán lá vào lúc trời râm mát. Đến ngày 4–7, kiểm tra rầy nở đợt mới để phun đảo hoạt chất nếu mật độ còn cao. Từ ngày 8–14, phun bổ sung phân bón lá giàu Bo, Kẽm, Silic và Axit Amin để kích thích bung đọt chè mới. Từ ngày 15–21, phun nấm ký sinh côn trùng Metarhizium anisopliae (nấm xanh) hoặc Beauveria bassiana (nấm trắng) duy trì bảo vệ sinh học bền vững. Thời gian phục hồi ước tính: 3–4 tuần.",
        "treatment_steps": """Giai đoạn 1 — Ngày 1: Đánh giá mật độ & Khoanh vùng khẩn cấp:
• Hành động cần làm: Kiểm tra toàn diện nương chè, xác định tỷ lệ búp bị hại và mật độ rầy xanh (chú ý mặt dưới lá non). Nếu mật độ vượt ngưỡng phòng trừ (> 5 con/búp hoặc trên 10% búp chùn quăn), tạm dừng ngay việc hái búp để tránh rầy phân tán rộng. Thu hái hoặc bấm bỏ các búp đã bị cháy rầy khô đen mang đi tiêu hủy.
• Triệu chứng cần theo dõi: Mật độ rầy xanh non (màu xanh vàng nhạt bò ngang) và rầy trưởng thành (xanh lá mạ nhảy lẩn trốn) dưới mặt lá bánh tẻ và búp non.
• Dấu hiệu cải thiện: Xác định chính xác tâm điểm ổ dịch để tập trung phun dập dịch.
• Khi nào cần can thiệp bổ sung: Nếu mật độ rầy bùng phát diện rộng trên 20% số búp, cần tổ chức phun dập dịch đồng loạt toàn bộ nương chè.

Giai đoạn 2 — Ngày 2–3: Phun dập dịch đợt 1 & Cắt lứa rầy non:
• Hành động cần làm: Phun dập dịch ngay bằng một trong các hoạt chất đặc trị rầy xanh thế hệ mới có tính thẩm thấu và nội hấp cao: Flonicamid (Teppeki 50WG, 3–4g/bình 16L), Pymetrozine (Chess 50WG) hoặc Buprofezin (Applaud 10WP) phối hợp dầu khoáng nông nghiệp SK Enspray 99EC. Chỉnh béc phun sương mịn, phun kỹ mặt dưới tán lá và xung quanh búp non vào lúc sáng sớm râm mát hoặc chiều tắt nắng.
• Triệu chứng cần theo dõi: Số lượng rầy rơi rụng dưới gốc và ngừng chích hút dịch búp.
• Dấu hiệu cải thiện: Mật độ rầy sống sót giảm rõ rệt (> 85%), búp chè non không phát sinh thêm chấm vàng chích hút mới.
• Khi nào cần can thiệp bổ sung: Nếu trời mưa trong vòng 3 giờ sau phun, phải phun dặm lại khi thời tiết ráo tạnh.

Giai đoạn 3 — Ngày 4–7: Kiểm tra lứa trứng nở & Phun đảo hoạt chất:
• Hành động cần làm: Kiểm tra lại các ổ trứng rầy đẻ trong cuống lá non xem có lứa rầy non mới nở hay không. Nếu phát hiện rầy non mới nở tiếp tục gây hại, tiến hành phun đảo hoạt chất luân phiên (tránh hiện tượng quen thuốc) bằng Dinotefuran hoặc Thiamethoxam kết hợp hoạt chất sinh học Abamectin/Emamectin.
• Triệu chứng cần theo dõi: Mép lá non bắt đầu giãn dần, không còn co rúm thêm.
• Dấu hiệu cải thiện: Rầy non thế hệ mới bị tiêu diệt hoàn toàn, không còn rầy búng nhảy khi rung tán chè.
• Khi nào cần can thiệp bổ sung: Nếu phát hiện kèm nhện đỏ hoặc bọ xít muỗi cùng phát sinh, phối hợp thuốc đặc trị đa phổ.

Giai đoạn 4 — Ngày 8–14: Dưỡng búp non & Phục hồi tầng tán:
• Hành động cần làm: Khi mật độ rầy đã về mức an toàn, phun phân bón lá chuyên dùng cho chè giàu Silic, Bo, Kẽm và Axit Amin hữu cơ để kích thích mắt ngủ nách lá bung đọt mới. Bón gốc bổ sung phân hữu cơ hoai mục kết hợp Kali Sunfat (K2SO4) để tăng độ dày vách tế bào búp non.
• Triệu chứng cần theo dõi: Tốc độ bung mầm của các chồi nách phía dưới búp bị hại.
• Dấu hiệu cải thiện: Chồi nách bung lứa búp mới xanh sáng, phiến lá phẳng mướt, không có vết thâm chích.
• Khi nào cần can thiệp bổ sung: Nếu thấy búp non mới nhú có dấu hiệu quăn mép trở lại, lập tức kiểm tra mặt dưới lá tìm rầy di trú từ đồi bên cạnh.

Giai đoạn 5 — Ngày 15–21: Thiết lập hàng rào sinh học bền vững:
• Hành động cần làm: Phun chế phẩm sinh học nấm ký sinh rầy Metarhizium anisopliae (nấm xanh) hoặc Beauveria bassiana (nấm trắng) định kỳ để tạo bào tử nấm ký sinh trứng và ấu trùng rầy. Cắt cỏ mép nương để bảo vệ môi trường cho nhện bắt mồi và bọ rùa.
• Triệu chứng cần theo dõi: Sự phát triển đồng đều của toàn bộ tầng tán búp mới.
• Dấu hiệu cải thiện: Lứa búp chè 1 tôm 2 lá phát triển đều đặn, xanh mỡ màng, nương chè sẵn sàng cho kỳ thu hái mới.
• Khi nào cần can thiệp bổ sung: Chỉ can thiệp thuốc hóa học nếu có đợt thời tiết hanh khô kéo dài kích hoạt dịch rầy mới.

Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:
• Thời gian phục hồi ước tính: 3–4 tuần (phụ thuộc vào lứa chồi nách và chế độ dinh dưỡng).
• Tiêu chí xác định cây khỏi bệnh:
  1. Mật độ rầy xanh trên toàn nương duy trì dưới ngưỡng gây hại (< 1 con/búp chè) trong ít nhất 14 ngày liên tục.
  2. Toàn bộ lứa búp non mới bung đều, phiến lá phẳng phiu, màu xanh đọt chuối sáng bóng, không còn hiện tượng quăn mép hay cháy khô đầu ngọn.
  3. Tán chè phục hồi mật độ tán đồng đều, cây cho năng suất búp bình thường trở lại.
• Lưu ý quan trọng về phục hồi mô: Các mép lá và búp đã bị rầy chích hút làm khô cháy mép ('cháy rầy') trước đây sẽ không thể xanh tươi trở lại mà sẽ khô rụng; sự hồi phục thực sự được đánh giá qua sự sinh trưởng khỏe mạnh, mướt mát của lứa búp non kế tiếp.""",
        "recovery_info": "⏱️ Thời gian khống chế dịch rầy: 2–4 ngày (mật độ rầy giảm > 90%, ngừng chích hút đọt non).\n🌱 Thời gian bung lứa búp mới: 8–12 ngày (các chồi nách bung đọt chè mới khỏe mạnh, lá phẳng).\n🔄 Thời gian khỏi bệnh & phục hồi hoàn toàn: 3–4 tuần (toàn bộ tầng tán phục hồi chu kỳ thu hái bình thường).\n📊 Tiên lượng phục hồi: 90–95% nếu can thiệp kịp thời bằng các hoạt chất đặc trị và bổ sung dinh dưỡng qua lá.\n💡 Lưu ý phục hồi: Búp và mép lá đã bị rầy chích làm khô cháy sẽ không hồi xanh lại; phục hồi dựa vào lứa đọt non mới bung."
    },
    {
        "class_name": "Thối đen lá chè (Black rot of tea)",
        "display_name": "Thối đen lá chè (Black rot of tea)",
        "description": "Bệnh thối đen lá chè (Black rot of tea) do nấm Pestalotiopsis theae (Sawada) Steyaert (hoặc Pseudopestalotiopsis theae) gây ra. Đây là một trong những bệnh nấm lá chè phổ biến và gây hại nghiêm trọng nhất tại các vùng chè nhiệt đới và cận nhiệt đới. Nấm xâm nhiễm qua các vết thương cơ giới do hái chè, vết chích hút của côn trùng hoặc vết cháy nắng, gây khô cháy tầng lá tán, thối búp và rụng lá hàng loạt làm giảm sút nghiêm trọng sản lượng chè.",
        "symptoms": "Ban đầu là các chấm nhỏ màu nâu vàng hoặc nâu nhạt ở chóp lá, mép lá hoặc vết cắt búp chè. Vết bệnh nhanh chóng lan rộng thành các đốm lớn hình tròn hoặc bất định, đường kính 1–3 cm. Đặc điểm nhận diện điển hình: trung tâm vết bệnh chuyển sang màu thối đen, xám tro hoặc xám bạc như giấy nến, bao quanh bởi đường viền gợn sóng màu nâu đậm hoặc tím thẫm. Mặt trên của vết thối đen mọc lên vô số hạt đen li ti (quả thể nấm - acervuli) xếp thành các vòng đồng tâm rất rõ nét. Gặp trời ẩm, các giọt bào tử màu đen bóng nhầy trào ra từ các chấm đen này.",
        "prevention": "1. Vệ sinh nương chè định kỳ, thu gom lá rụng và cành khô đem tiêu hủy để triệt tiêu nguồn nấm lưu trú.\n2. Thu hái búp đúng lứa, tránh làm giập nát cành lá; sau khi đốn chè hoặc thu hái bằng máy cần phun thuốc phòng ngừa.\n3. Quản lý tốt các loài sâu bọ chích hút (bọ xít muỗi, bọ trĩ, rầy xanh) để ngăn ngừa tạo vết thương hở cho nấm xâm nhập.\n4. Đốn tỉa cành tăm, cành sâu bệnh bên trong tán để tạo độ thông thoáng, tăng cường ánh sáng chiếu vào lòng bụi chè.\n5. Bón đầy đủ phân Kali và phân hữu cơ vi sinh, hạn chế bón đạm đơn độc làm lá mỏng yếu.",
        "treatment": "Lộ trình điều trị toàn diện: Thu dọn sạch lá rụng và búp thối đen trên tán và dưới gốc chè. Phun thuốc đặc trị nấm đợt 1 bằng hỗn hợp Azoxystrobin + Difenoconazole (Amistar Top 325SC, 10–15ml/16L) hoặc Thiophanate-Methyl phối hợp Mancozeb (Dithane M-45 80WP, 30g/16L). Cắt tỉa cành tăm rậm rạp bên dưới tán. Bón bổ sung phân Kali Sunfat (K2SO4) và lân vi sinh trong ngày 4–7 để gia cố mô lá khỏe. Ngày 8–14, phun đảo hoạt chất Chlorothalonil hoặc Copper Oxychloride để bảo vệ lứa búp mới nhú. Nuôi dưỡng búp mới bằng amino axit hữu cơ từ ngày 15–28. Thời gian phục hồi ước tính: 4–6 tuần.",
        "treatment_steps": """Giai đoạn 1 — Ngày 1: Đánh giá ban đầu & Thu dọn vệ sinh nguồn bệnh:
• Hành động cần làm: Kiểm tra tầng lá mặt tán và lá bánh tẻ, xác định các đốm thối đen có viền nâu và các hạt đen li ti xếp vòng đồng tâm. Dùng tay hoặc kéo hái gom bỏ các lá bị đốm nặng và búp bị thối đen cho vào bao kín mang ra khỏi nương chè tiêu hủy. Quét sạch lá rụng dưới gốc chè để triệt tiêu nguồn lây lan.
• Triệu chứng cần theo dõi: Các đốm thối đen, xám bạc với viền nâu đỏ lượn sóng và vòng hạt đen acervuli trên mặt lá.
• Dấu hiệu cải thiện: Không còn lá bệnh già nằm rải rác trên bề mặt tán và gốc cây.
• Khi nào cần can thiệp bổ sung: Nếu phát hiện kèm theo bọ xít muỗi Helopeltis chích hút tạo nhiều vết châm đen, cần lên kế hoạch xử lý đồng thời cả nấm và bọ.

Giai đoạn 2 — Ngày 2–3: Phun thuốc đặc trị nấm đợt 1 & Cắt tỉa thông thoáng:
• Hành động cần làm: Phun hỗn hợp thuốc trừ nấm nội hấp và tiếp xúc: Azoxystrobin + Difenoconazole (Amistar Top 325SC, 10–15ml/bình 16L) hoặc Carbendazim / Thiophanate-Methyl phối hợp Mancozeb (Dithane M-45 80WP, 30g/bình 16L). Phun ướt đẫm bề mặt tán lá và tầng lá giữa của bụi chè. Cắt tỉa các cành tăm rậm rạp bên dưới tán để đón gió và ánh nắng.
• Triệu chứng cần theo dõi: Sự ngừng tiết dịch bào tử đen từ các hạt acervuli trên vết bệnh thối đen.
• Dấu hiệu cải thiện: Mép viền nâu đỏ sẫm màu lại, vết bệnh khô cứng, không loang rộng thêm sang phần phiến lá xanh.
• Khi nào cần can thiệp bổ sung: Nếu mưa kéo dài sau khi phun khiến thuốc bị trôi, cần phun dặm lại hoạt chất tiếp xúc bảo vệ.

Giai đoạn 3 — Ngày 4–7: Giám sát viền bệnh & Bổ sung dinh dưỡng rễ:
• Hành động cần làm: Kiểm tra mép ranh giới giữa vết bệnh và mô khỏe. Tiến hành bón gốc phân Kali Sunfat (K2SO4) kết hợp phân lân hữu cơ vi sinh nhằm gia cố sức đề kháng tự nhiên của bụi chè. Tạm ngưng phân đạm urê.
• Triệu chứng cần theo dõi: Kích thước của các đốm thối đen và màu sắc phiến lá bánh tẻ xung quanh.
• Dấu hiệu cải thiện: Đốm bệnh ngừng phát triển hoàn toàn; mô lá xanh xung quanh không bị úa vàng hay rụng non.
• Khi nào cần can thiệp bổ sung: Nếu thấy đốm bệnh tiếp tục xuất hiện trên lứa búp mới, cần đổi sang hoạt chất Chlorothalonil hoặc Difenoconazole liều tăng cường.

Giai đoạn 4 — Ngày 8–14: Phun đảo hoạt chất đợt 2 & Đánh giá bảo vệ lứa mới:
• Hành động cần làm: Phun luân phiên thuốc trừ nấm nhóm Chlorothalonil (Daconil 75WP, 20g/bình 16L) hoặc Copper Oxychloride (Coc 85, 30g/bình 16L) để bao phủ bảo vệ các đọt chè non mới chuẩn bị nhú, tránh nguy cơ nấm Pestalotiopsis kháng thuốc.
• Triệu chứng cần theo dõi: Các mắt mầm tại nách lá bắt đầu cựa bung chồi mới.
• Dấu hiệu cải thiện: Toàn bộ chồi non mới nhú có màu xanh nõn chuối sáng bóng, hoàn toàn không có vết sọc nâu hoặc chấm đen ở chóp mầm.
• Khi nào cần can thiệp bổ sung: Nếu thời tiết nhiều sương mù âm u kéo dài, duy trì phun phòng định kỳ 10 ngày/lần.

Giai đoạn 5 — Ngày 15–28: Dưỡng chồi non & Tái tạo tầng tán quang hợp:
• Hành động cần làm: Phun phân bón lá chứa vi lượng Kẽm, Magie và Axit Amin hữu cơ để kích thích búp mới bật đều và phiến lá mở to. Giữ đất đủ ẩm nhưng mặt luống khô thoáng.
• Triệu chứng cần theo dõi: Tốc độ bung lứa búp mới trên toàn bộ mặt tán chè.
• Dấu hiệu cải thiện: Mặt tán chè phủ kín màu xanh tươi mới; các đốm thối đen cũ khô đanh và bị tầng lá mới che phủ bên dưới.
• Khi nào cần can thiệp bổ sung: Chỉ bổ sung thuốc bảo vệ sinh học nếu có dấu hiệu côn trùng gây vết thương cơ giới.

Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:
• Thời gian phục hồi ước tính: 4–6 tuần (tương ứng với một chu kỳ sinh trưởng hoàn chỉnh của lứa chè mới).
• Tiêu chí xác định cây khỏi bệnh:
  1. 100% các vết đốm thối đen cũ đã khô giòn, mép nâu đóng vảy cứng, các hạt đen nấm không còn khả năng phát tán bào tử.
  2. Không xuất hiện bất kỳ vết đốm thối đen hay thối búp mới nào trên toàn bộ tầng lá non và búp tôm trong suốt 2 tuần theo dõi.
  3. Lứa búp chè mới đạt tiêu chuẩn 1 tôm 2 lá dày, giòn, hương vị đặc trưng, đủ điều kiện đưa vào thu hoạch thương phẩm.
• Lưu ý quan trọng về phục hồi mô: Phần mô lá màu thối đen chết khô do nấm phá hủy là tổn thương vĩnh viễn không thể xanh trở lại; bản chất của sự khỏi bệnh là nấm bị tiêu diệt hoàn toàn, không lây lan thêm và cây chè tái sinh thành công bộ lá và búp mới khỏe mạnh.""",
        "recovery_info": "⏱️ Thời gian khống chế bệnh: 3–5 ngày sau đợt phun thuốc đặc trị đầu tiên (vết đốm thối đen khô mép, hạt đen ngừng rỉ dịch bào tử).\n🌱 Thời gian bung chồi lá non mới: 10–14 ngày (chồi nách bung lứa búp xanh nõn khỏe mạnh).\n🔄 Thời gian khỏi bệnh & phục hồi hoàn toàn: 4–6 tuần (tán chè tái tạo hoàn toàn sinh khối búp thu hoạch).\n📊 Tiên lượng phục hồi: 90–95% nếu phát hiện sớm và xử lý đồng thời cả nấm lẫn sâu chích hút.\n💡 Lưu ý phục hồi: Mô lá thối đen chết khô là tổn thương vĩnh viễn; phục hồi được khẳng định khi nương chè mọc rộ búp mới sạch bệnh."
    },
    {
        "class_name": "Cháy nâu lá chè (Brown blight of tea)",
        "display_name": "Cháy nâu lá chè (Brown blight of tea)",
        "description": "Bệnh cháy nâu lá chè (Brown blight of tea) do nấm Colletotrichum camelliae Massee (giai đoạn hữu tính: Glomerella cingulata) gây nên. Bệnh gây hại nghiêm trọng trên cả lá già, lá bánh tẻ và đặc biệt là búp chè non ('thối búp nâu'). Bệnh phát sinh mạnh trong điều kiện thời tiết nóng ẩm, mưa rào mùa hè xen kẽ nắng gắt, làm cháy táp mép lá và thối khô đọt non, ảnh hưởng nghiêm trọng tới chu kỳ thu hái chè.",
        "symptoms": "Vết bệnh thường xuất hiện từ mép lá hoặc chóp lá, sau đó lan dần vào bên trong phiến lá thành các mảng lớn hình bán nguyệt, hình bầu dục hoặc hình dải bất định. Màu sắc vết bệnh có màu nâu đỏ đến nâu sô-cô-la đặc trưng, ranh giới giữa mô bệnh và mô khỏe là một đường viền nâu đậm hoặc tím sẫm nổi rõ. Trên bề mặt vết bệnh khi già xuất hiện rải rác các chấm đen nhỏ li ti (đĩa cành nấm - acervuli). Khi tấn công búp non, vết thối màu nâu sẫm lan nhanh làm khô cháy toàn bộ búp non và cành búp bị gãy gục. Khác với Thối đen lá chè (Black rot of tea), vết cháy nâu giữ nguyên màu nâu đỏ/nâu đậm đồng nhất, không bị bạc màu thành tâm xám trắng tro.",
        "prevention": "1. Điều chỉnh bóng râm hợp lý: tỉa thưa cây che bóng trong vườn chè nếu độ che phủ vượt quá 30–40% để tăng ánh sáng tự nhiên.\n2. Vệ sinh nương chè sau mỗi đợt hái, thu dọn các tàn dư búp nâu và lá bệnh rơi rụng.\n3. Tránh hái chè khi lá còn ướt sương mai hoặc sau cơn mưa to.\n4. Bón phân NPK cân đối, bổ sung lân và kali giúp chè tăng khả năng chịu nhiệt và kháng nấm anthracnose.\n5. Đốn tỉa định kỳ tạo tán chè hình vòm xòe rộng, hạn chế cành la sát mặt đất.",
        "treatment": "Lộ trình điều trị toàn diện: Khảo sát, cách ly luống chè bị bệnh; tỉa bỏ các ngọn búp bị cháy nâu gom vào bao đem tiêu hủy. Phun thuốc đặc trị nấm nội hấp nhóm Triazole/Strobilurin: Difenoconazole (Score 250EC, 5–8ml/16L) hoặc Tebuconazole (Folicur 250EW) hoặc Azoxystrobin (Amistar 250SC, 8ml/16L). Tỉa bớt cành che bóng để tăng nắng gió. Ngày 4–7, theo dõi mép vết nâu se khô và phun Antracol hoặc Mancozeb chống rửa trôi. Ngày 8–14, phun luân phiên Propineb hoặc Chlorothalonil kết hợp bổ sung Kali và Silic. Bón phân hữu cơ vi sinh và Humic từ ngày 15–28 để thúc lứa búp mới. Thời gian phục hồi ước tính: 4–5 tuần.",
        "treatment_steps": """Giai đoạn 1 — Ngày 1: Nhận diện, cách ly & Vệ sinh cành bệnh:
• Hành động cần làm: Khảo sát các luống chè bị cháy mép màu nâu đỏ và búp non bị héo nâu. Tạm dừng thu hái trên các lô bị nhiễm. Dùng kéo tiệt trùng cắt tỉa các ngọn búp bị cháy nâu gom vào túi nilon đem ra ngoài hủy. Thu gom lá rụng quanh gốc cây.
• Triệu chứng cần theo dõi: Các mảng nâu đỏ hình bán nguyệt ở mép lá và các đọt búp non bị héo rũ màu nâu đen.
• Dấu hiệu cải thiện: Khu vực nhiễm bệnh được cô lập, không phát tán thêm tàn dư mô bệnh sang các hàng chè kế bên.
• Khi nào cần can thiệp bổ sung: Nếu thấy lớp chất nhờn màu hồng cam (khối bào tử Colletotrichum) xuất hiện trên vết bệnh trong điều kiện ẩm ướt, phải lập tức chuẩn bị thuốc nội hấp phổ rộng.

Giai đoạn 2 — Ngày 2–3: Phun thuốc đặc trị nội hấp đợt 1 & Điều chỉnh bóng mát:
• Hành động cần làm: Phun thuốc trừ nấm nội hấp nhóm Triazole hoặc Strobilurin: Difenoconazole (Score 250EC, 5–8ml/bình 16L) hoặc Tebuconazole (Folicur 250EW, 10ml/bình 16L) hoặc Azoxystrobin (Amistar 250SC, 8ml/bình 16L). Phun ướt đẫm 2 mặt lá và bao trùm các tầng cành mang búp. Tỉa bớt cành cây che bóng để tán chè đón đủ nắng mặt trời.
• Triệu chứng cần theo dõi: Sự ngừng mở rộng của quầng nâu đỏ ở rìa vết bệnh.
• Dấu hiệu cải thiện: Mép vết nâu sậm lại, khô cứng ráo nước, không có quầng vàng loang thêm sang mô lá xanh.
• Khi nào cần can thiệp bổ sung: Nếu sau 48 giờ vết nâu vẫn tiếp tục tiến sâu vào gân chính của lá, cần kiểm tra lại chất lượng nước pha thuốc và liều lượng hoạt chất.

Giai đoạn 3 — Ngày 4–7: Kiểm tra sự cầm cự & Chống rửa trôi:
• Hành động cần làm: Quan sát kỹ các búp chè vừa được xử lý. Duy trì độ thông thoáng hàng chè. Nếu có mưa rào mùa hè, phun bổ sung hoạt chất tiếp xúc có độ bám dính cao như Mancozeb (Dithane M-45, 30g/16L) hoặc Antracol 70WP để tạo màng chắn ion kẽm bảo vệ bề mặt lá.
• Triệu chứng cần theo dõi: Trạng thái của các mô lá xanh tiếp giáp vết hoại tử nâu.
• Dấu hiệu cải thiện: Vết bệnh khô giòn, có thể nứt rách ở giữa nhưng không lan rộng; không xuất hiện giọt bào tử nhầy màu hồng cam.
• Khi nào cần can thiệp bổ sung: Khi phát hiện đốm mới trên các cây khỏe liền kề, tiến hành phun bao vây một bán kính 5–7 mét quanh ổ bệnh.

Giai đoạn 4 — Ngày 8–14: Phun luân phiên đợt 2 & Bổ sung phân bón lá tăng lực:
• Hành động cần làm: Luân chuyển nhóm thuốc: Phun Propineb hoặc Chlorothalonil phối hợp phân bón lá giàu Silic và Kali để tăng độ dày lớp biểu bì lá chè mới. Không bón đạm urê trong giai đoạn này.
• Triệu chứng cần theo dõi: Sự hình thành mầm non tại các nách lá phía dưới ngọn búp đã tỉa.
• Dấu hiệu cải thiện: Chồi nách bật mầm khỏe khoắn, các mầm búp mới vươn thẳng màu xanh nõn, không có chấm nâu ở đỉnh mầm.
• Khi nào cần can thiệp bổ sung: Nếu thấy bọ cánh tơ hoặc nhện đỏ tấn công chồi non, cần kết hợp thuốc thảo mộc hoặc dầu khoáng trừ dịch hại.

Giai đoạn 5 — Ngày 15–28: Phục hồi sinh trưởng & Nuôi dưỡng búp mới:
• Hành động cần làm: Tưới gốc bổ sung Humic và phân bón hữu cơ sinh học để kích thích rễ hấp thụ dinh dưỡng tái tạo sinh khối. Duy trì chế độ làm cỏ thông thoáng luống chè.
• Triệu chứng cần theo dõi: Mức độ đồng đều của lứa búp mới trên toàn bộ mặt tán.
• Dấu hiệu cải thiện: Các búp mới phát triển vượt qua chiều cao tầng vết bệnh cũ, tán lá xanh mượt, bóng bẩy.
• Khi nào cần can thiệp bổ sung: Duy trì phun phòng sinh học định kỳ 14 ngày/lần trong mùa mưa rào.

Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:
• Thời gian phục hồi ước tính: 4–5 tuần.
• Tiêu chí xác định cây khỏi bệnh:
  1. 100% các vết cháy nâu cũ đã hóa sẹo khô cứng, ngừng hẳn sự mở rộng diện tích hoại tử trong tối thiểu 14 ngày.
  2. Không có thêm bất kỳ ngọn búp nào bị cháy nâu hoặc héo gục trên toàn diện tích điều trị.
  3. Lứa búp chè mới (1 tôm 2 lá) đạt độ đồng đều cao, lá dày, xanh mướt, chất lượng chè búp đạt tiêu chuẩn thu hái xuất xưởng.
• Lưu ý quan trọng về phục hồi mô: Các mảng lá màu nâu đỏ đã bị nấm phá hủy tế bào sẽ vĩnh viễn không thể hồi phục lại màu xanh ban đầu; sự phục hồi thành công được khẳng định khi nấm Colletotrichum bị tiêu diệt hoàn toàn và nương chè mọc rộ lứa búp mới xanh sạch bệnh.""",
        "recovery_info": "⏱️ Thời gian khống chế bệnh: 3–4 ngày sau đợt phun thuốc nội hấp đầu tiên (quầng nâu ngừng lan, mép khô giòn).\n🌱 Thời gian bung chồi lá non mới: 10–14 ngày (mầm nách bung lứa búp xanh bóng khỏe mạnh).\n🔄 Thời gian khỏi bệnh & phục hồi hoàn toàn: 4–5 tuần (toàn bộ tán chè phục hồi mật độ búp thu hoạch).\n📊 Tiên lượng phục hồi: 85–92% khi điều chỉnh kịp thời ánh sáng tán chè và xử lý thuốc lưu dẫn.\n💡 Lưu ý phục hồi: Mô lá nâu chết khô không thể xanh lại; cây khỏi bệnh được đánh giá qua sự bật rộ của lứa búp mới."
    },
    {
        "class_name": "Gỉ sắt lá chè (Leaf rust of tea)",
        "display_name": "Gỉ sắt lá chè (Leaf rust of tea)",
        "description": "Bệnh gỉ sắt lá chè (Leaf rust of tea) do nấm Elsinoë leucospila Bitanc. & Jenkins (dạng vô tính: Sphaceloma theae Hara) gây ra. Bệnh chuyên tấn công vào các bộ phận còn non mềm của cây chè như búp non, lá non và cọng non trong các đợt phát lộc mùa xuân hoặc mùa mưa phùn. Bệnh làm cho lá chè non bị co rúm, biến dạng, cọng búp hóa sẹo gỉ nâu giòn gãy, còi cọc và làm giảm sút nghiêm trọng chất lượng chè búp chất lượng cao.",
        "symptoms": "Ban đầu trên phiến lá non xuất hiện các chấm nhỏ li ti (đường kính 0.5–1mm) màu đỏ gỉ sắt, đỏ tía hoặc nâu đậm hơi lõm xuống. Sau đó, tâm vết bệnh mở rộng dần (1–3mm) và hóa sẹo màu trắng xám, trắng phấn hoặc gỉ sắt, trũng xuống ở giữa, xung quanh bao bọc bởi gờ viền nổi cao màu tím than hoặc nâu đỏ sẫm rất đặc trưng. Nhiều vết sẹo gỉ liên kết lại làm phiến lá nhăn nhúm, gồ ghề, quăn queo và rách mép. Trên cọng búp và đốt thân non, vết bệnh tạo thành các vết sẹo gỉ sắt gồ ghề kéo dài, làm cọng búp khô giòn và dễ gãy ngang khi gió mạnh. Khác với Lá chè bị nhện đỏ gây hại, vết gỉ sắt có kích thước nhỏ, lõm với viền tím nổi gờ chứ không phồng to dạng chén nhung.",
        "prevention": "1. Chọn các giống chè bản địa có tầng cutin lá non dày và khả năng chống chịu bệnh gỉ sắt tốt.\n2. Vệ sinh nương chè, đốn tỉa đúng khung lịch kỹ thuật để chè ra lộc xuân tập trung, dễ quản lý dịch hại.\n3. Làm sạch cỏ dại dưới luống chè để triệt tiêu độ ẩm ngưng tụ vào sáng sớm mùa xuân.\n4. Bón phân hữu cơ vi sinh ủ hoai mục kết hợp vôi bột khử trùng đất trước chu kỳ phát lộc xuân.\n5. Không thu hái chè khi tán lá còn đẫm sương mù ẩm ướt.",
        "treatment": "Lộ trình điều trị toàn diện: Khảo sát lứa lộc non, tạm dừng hái bằng máy để tránh xây xát phát tán bào tử Sphaceloma. Phun thuốc đặc trị bệnh gỉ sắt: Thiophanate-Methyl (Topsin M 70WP, 15–20g/16L) hoặc Difenoconazole (Score 250EC, 6–8ml/16L) hoặc Copper Oxychloride (Coc 85, 30g/16L) tập trung vào tầng lá non trên đỉnh tán. Ngày 4–7, làm sạch cỏ dại luống chè để hạ độ ẩm và theo dõi độ mở phẳng của phiến lá. Ngày 8–14, phun luân phiên Chlorothalonil hoặc Mancozeb phối hợp vi lượng Bo, Kẽm và Axit Amin. Bón thúc phân NPK giàu Kali từ ngày 15–28 để búp non vươn dài mập mạp. Thời gian phục hồi ước tính: 3–5 tuần.",
        "treatment_steps": """Giai đoạn 1 — Ngày 1: Nhận diện vết chấm lõm & Đánh giá phân bố:
• Hành động cần làm: Kiểm tra kỹ các lá non mới mở và cọng búp lứa xuân tìm các chấm tròn nhỏ viền tím lõm màu gỉ sắt. Đánh dấu các băng chè bị nhiễm. Tạm ngừng hái bằng máy để tránh cọ xát cơ giới làm nứt vỡ các vết sẹo phát tán bào tử Sphaceloma.
• Triệu chứng cần theo dõi: Các chấm sẹo tròn màu gỉ sắt có gờ viền tím sẫm nổi cao trên lá non và cọng búp.
• Dấu hiệu cải thiện: Không có triệu chứng lan rộng cơ giới sang các luống chè non đang nhú bên cạnh.
• Khi nào cần can thiệp bổ sung: Nếu thấy cọng búp non bị thâm đen và gãy rạp hàng loạt, cần ưu tiên phun thuốc dập dịch ngay trong ngày.

Giai đoạn 2 — Ngày 2–3: Phun thuốc đặc trị đợt 1 & Vệ sinh tán lá:
• Hành động cần làm: Phun thuốc trừ nấm đặc trị bệnh gỉ sắt: Thiophanate-Methyl (Topsin M 70WP, 15–20g/bình 16L) hoặc Difenoconazole (Score 250EC, 6–8ml/bình 16L) hoặc Copper Oxychloride (Coc 85, 30g/bình 16L). Phun tập trung vào tầng lá non trên đỉnh tán nơi nấm Elsinoë đang hoạt động mạnh.
• Triệu chứng cần theo dõi: Tình trạng của các đốm đỏ tía mới chớm ở mặt dưới lá non.
• Dấu hiệu cải thiện: Vết chấm non ngừng lan rộng; vết sẹo cũ chuyển sang khô cứng, không phát sinh thêm chấm đỏ mới.
• Khi nào cần can thiệp bổ sung: Nếu trời có sương muối hoặc mưa phùn liên tục, tăng cường chất bám dính sinh học khi pha thuốc.

Giai đoạn 3 — Ngày 4–7: Kiểm tra độ quăn queo phiến lá & Thông thoáng luống chè:
• Hành động cần làm: Làm sạch cỏ dại dưới gốc chè, cắt tỉa cành la sát đất để gió lưu thông làm khô nhanh giọt sương trên búp vào buổi sáng.
• Triệu chứng cần theo dõi: Độ mở phẳng của các lá non tiếp theo trên búp chè.
• Dấu hiệu cải thiện: Các lá non mới mở ra không bị quăn queo gồ ghề hay biến dạng mép lá.
• Khi nào cần can thiệp bổ sung: Nếu cọng búp non mới vẫn xuất hiện vệt nâu lõm, cần chuẩn bị đổi sang hoạt chất nấm nội hấp nhóm Triazole khác.

Giai đoạn 4 — Ngày 8–14: Phun bảo vệ đợt 2 & Bổ sung vi lượng lá:
• Hành động cần làm: Phun luân phiên Chlorothalonil (Daconil 75WP, 20g/bình 16L) hoặc Mancozeb để tạo lớp màng bảo vệ các đọt chè non của lứa lộc kế tiếp. Phun kết hợp vi lượng Bo, Kẽm và Axit Amin giúp phiến lá chè phát triển cân đối, dẻo dai.
• Triệu chứng cần theo dõi: Bề mặt phiến lá lứa lộc mới.
• Dấu hiệu cải thiện: Các đốm sẹo gỉ sắt cũ cô lập hoàn toàn; lứa lá mới nhú lên phẳng phiu, xanh nõn và không có nốt sẹo.
• Khi nào cần can thiệp bổ sung: Nếu thời tiết chuyển ấm ẩm kích thích nấm lây lan, rút ngắn khoảng cách phun bảo vệ còn 7–10 ngày.

Giai đoạn 5 — Ngày 15–28: Ổn định tán chè & Đón lứa búp mới:
• Hành động cần làm: Bón thúc phân NPK chuyên dùng cho chè (giàu Kali và Lân) để kích thích búp vươn dài khỏe mạnh. Duy trì kiểm tra định kỳ 2 lần/tuần.
• Triệu chứng cần theo dõi: Độ giòn và độ thẳng của cọng búp non.
• Dấu hiệu cải thiện: Cọng búp mập mạp, thẳng tắp, nhẵn bóng không có sẹo gồ ghề; thu hoạch thử nghiệm đạt phẩm cấp tốt.
• Khi nào cần can thiệp bổ sung: Duy trì phun chế phẩm sinh học phòng ngừa định kỳ trong suốt mùa mưa phùn.

Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:
• Thời gian phục hồi ước tính: 3–5 tuần.
• Tiêu chí xác định cây khỏi bệnh:
  1. 100% các nốt gỉ sắt cũ đã đóng vảy khô trơ, gờ viền tím sẫm không còn hoạt động, không phát tán thêm bào tử.
  2. Toàn bộ lứa lá non và búp non mới phát triển hoàn toàn phẳng phiu, trơn láng, không bị co rúm, cong vẹo hay lấm tấm nốt đỏ.
  3. Cọng búp chè dẻo dai, không bị hóa sẹo giòn gãy, năng suất búp tươi phục hồi đạt chuẩn chế biến.
• Lưu ý quan trọng về phục hồi mô: Các vết sẹo màu gỉ sắt lõm và phần phiến lá đã bị co rúm trước đó sẽ giữ nguyên vết sẹo vĩnh viễn trên lá già; sự phục hồi bệnh học được đánh giá qua sự phát triển hoàn hảo, lành lặn và trơn bóng của toàn bộ lứa búp mới sinh ra sau đợt điều trị.""",
        "recovery_info": "⏱️ Thời gian khống chế bệnh: 3–5 ngày (vết chấm đỏ se khô, đóng vảy sẹo gỉ sắt trơ cứng).\n🌱 Thời gian bung chồi lá non mới: 10–14 ngày (lứa lá mới mở ra phẳng phiu, không co rúm).\n🔄 Thời gian khỏi bệnh & phục hồi hoàn toàn: 3–5 tuần (cọng búp nhẵn bóng, đạt chuẩn thương phẩm).\n📊 Tiên lượng phục hồi: 90–95% nếu phun chặn kịp thời ngay khi phát hiện chấm đỏ tía mùa xuân.\n💡 Lưu ý phục hồi: Vết gỉ sắt lõm trên lá già là tổn thương vĩnh viễn; cây khỏi bệnh khi lứa búp mới phẳng phiu, không tì vết."
    },
    {
        "class_name": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",
        "display_name": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf)",
        "description": "Lá chè bị nhện đỏ gây hại (Red spider mite infested tea leaf) do nhện đỏ hại chè và nấm chuyên tính gây ra. Đây là một trong những đối tượng gây hại nguy hiểm bậc nhất trên cây chè tại các vùng trồng chè đồi cao, khí hậu mát mẻ và nhiều sương mù (như Lâm Đồng, Sa Pa, Mộc Châu, Thái Nguyên...). Chúng chỉ tấn công vào các mô búp non và lá non dưới 30 ngày tuổi, làm phồng rộp biến dạng lá, lá chuyển màu đồng xơ xác và hủy hoại hoàn toàn lứa búp chè non, có thể làm sụt giảm 40–50% sản lượng chè búp nếu không phòng trừ kịp thời.",
        "symptoms": "Ban đầu trên lá non xuất hiện các đốm nhỏ trong mờ như giọt dầu, màu vàng nhạt hoặc hồng phấn nhạt do vết chích hút. Sau vài ngày, vết bệnh phát triển mạnh: mặt trên phiến lá bị lõm sâu xuống thành hình chén (concave), trong khi mặt dưới tương ứng phồng lồi lên thành một khối u phồng dạng bán cầu. Điểm đặc trưng nhất: bề mặt khối u phồng ở mặt dưới phủ kín một lớp phấn mịn như nhung màu trắng như tuyết (lớp đảm và bào tử đảm của nấm) hoặc lấm tấm mạng tơ nhện đỏ. Sau đó, khối phồng chuyển sang màu nâu đen, khô quắt, thủng rách phiến lá và búp non khô héo gãy gục.",
        "prevention": "1. Điều chỉnh tỉa bớt cây bóng mát trong vườn chè, đảm bảo ánh nắng mặt trời chiếu trực tiếp vào tán chè ít nhất 4–5 giờ mỗi ngày.\n2. Áp dụng chu kỳ hái dày (hái ngắn ngày 7–8 ngày/lần) để kịp thời thu hái các búp non trước khi dịch hại hoàn thành chu kỳ sinh sản.\n3. Đốn tỉa hạ thấp độ cao tán chè định kỳ, dọn sạch cỏ dại và cành tăm để luống chè luôn khô ráo.\n4. Theo dõi sát các đợt dự báo thời tiết sương mù, mưa phùn kéo dài ở vùng chè cao nguyên để chủ động phòng ngừa.\n5. Bón bổ sung phân lân và kali, hạn chế bón đạm hữu cơ hoặc vô cơ khi đang có sương mù ẩm ướt.",
        "treatment": "Lộ trình điều trị toàn diện: KHẨN CẤP — Tỉa cành cây che bóng để đón ánh nắng trực tiếp chiếu vào tán chè. Ngắt bỏ tiêu hủy các lá có khối phồng nhung trắng hoặc nhện đỏ trước khi trời tối. Phun thuốc đặc trị đợt 1 bằng hỗn hợp Copper Oxychloride (Coc 85, 30g/16L) phối hợp Hexaconazole (Anvil 5SC, 15–20ml/16L) hoặc Propiconazole (Tilt 250EC, 5ml/16L) hoặc dầu khoáng trừ nhện phủ kín 2 mặt lá. Thực hiện hái ngắn ngày (7–8 ngày/lần) từ ngày 4–7. Ngày 8–14, phun luân phiên Difenoconazole (Score 250EC) kết hợp phân bón lá Canxi-Silic và Kali để làm đanh cứng lớp biểu bì lá non mới. Bón NPK cân đối từ ngày 15–28. Thời gian phục hồi ước tính: 3–4 tuần.",
        "treatment_steps": """Giai đoạn 1 — Ngày 1: Báo động khẩn cấp & Tỉa cành đón nắng tức thì:
• Hành động cần làm: ⚠️ KHẨN CẤP: Dịch hại có khả năng phát tán theo gió cực nhanh trong sương mù. Lập tức tỉa cành cây che bóng trong vườn chè để đón ánh nắng trực tiếp chiếu vào tán chè. Dùng tay ngắt bỏ toàn bộ các lá có khối tổn thương nhung trắng đang sinh bào tử cho vào túi đóng kín đem chôn sâu hoặc đốt tiêu hủy ngay trước khi trời tối.
• Triệu chứng cần theo dõi: Các đốm lõm tròn hình chén mặt trên và khối u phồng màu nhung trắng như tuyết hoặc vết chích hút ở mặt dưới lá non.
• Dấu hiệu cải thiện: Không còn các ổ tổn thương lộ thiên phát tán dịch hại ra không khí.
• Khi nào cần can thiệp bổ sung: Nếu thấy trên 20% số búp non trên nương chè có chấm trong mờ, phải triển khai phun thuốc bảo vệ thực vật khẩn cấp trong vòng 24 giờ.

Giai đoạn 2 — Ngày 2–3: Phun thuốc đặc trị đợt 1 (Hỗn hợp Đồng + Triazole):
• Hành động cần làm: Phun hỗn hợp thuốc trừ tiếp xúc gốc đồng và nội hấp: Copper Oxychloride (Coc 85, 30g/bình 16L) phối hợp Hexaconazole (Anvil 5SC, 15–20ml/bình 16L) hoặc Propiconazole (Tilt 250EC, 5ml/bình 16L). Phun dạng sương mù cực mịn phủ kín cả mặt trên và mặt dưới khối tổn thương của toàn bộ búp non và tầng lá tán.
• Triệu chứng cần theo dõi: Lớp phấn trắng nhung của khối u phồng mặt dưới lá.
• Dấu hiệu cải thiện: Lớp nhung trắng chuyển sang màu vàng xám tro, xẹp dần và khô quắt lại, không còn bụi phấn bám vào tay khi chạm nhẹ.
• Khi nào cần can thiệp bổ sung: Nếu thời tiết âm u không có ánh nắng kéo dài, bắt buộc duy trì chu kỳ phun dập dịch 5–7 ngày/lần.

Giai đoạn 3 — Ngày 4–7: Kiểm soát mầm bệnh tiềm ẩn & Rút ngắn chu kỳ hái:
• Hành động cần làm: Thực hiện hái triệt để các búp chè đủ tiêu chuẩn trên nương (hái ngắn ngày) nhằm lấy đi các mô non mẫn cảm trước khi dịch hại kịp xâm nhiễm. Kiểm tra độ ẩm tán chè.
• Triệu chứng cần theo dõi: Sự phát sinh đốm vàng trong mờ non mới trên các lá búp vừa nhú.
• Dấu hiệu cải thiện: Không phát hiện thêm đốm trong mờ nào mới; các khối tổn thương cũ chuyển sang màu nâu giòn và rụng thủng tâm.
• Khi nào cần can thiệp bổ sung: Nếu mưa kéo dài làm trôi lớp thuốc đồng, tiến hành phun dặm ngay khi trời hửng sáng.

Giai đoạn 4 — Ngày 8–14: Phun củng cố đợt 2 & Bổ sung dinh dưỡng đanh lá:
• Hành động cần làm: Phun luân phiên thuốc nội hấp Difenoconazole (Score 250EC, 6ml/bình 16L) để tiêu diệt các sợi nấm đang ủ bệnh bên trong mô lá. Phun bổ sung Canxi-Silic và phân bón lá Kali để tăng tốc độ hóa già, làm cứng nhanh lớp biểu bì của lứa búp mới (chỉ xâm nhiễm được mô dưới 30 ngày tuổi).
• Triệu chứng cần theo dõi: Độ dày và độ cứng của phiến lá lứa lộc kế tiếp.
• Dấu hiệu cải thiện: Búp non mới vươn dài đanh chắc, mở lá nhanh, phiến lá phẳng phiu xanh mướt không có vết phồng lõm.
• Khi nào cần can thiệp bổ sung: Nếu thời tiết trở lại khô ráo có nắng trên 5 giờ/ngày, có thể dừng sử dụng thuốc hóa học.

Giai đoạn 5 — Ngày 15–28: Phục hồi chu kỳ búp & Giữ vườn khô thoáng:
• Hành động cần làm: Bón phân thúc búp NPK cân đối kết hợp phân hữu cơ vi sinh. Tiếp tục duy trì mật độ che bóng thông thoáng dưới 30%.
• Triệu chứng cần theo dõi: Tỷ lệ búp mù xòe và sức bật của lứa búp thương phẩm mới.
• Dấu hiệu cải thiện: Toàn nương chè ra búp đồng loạt, búp mập, màu xanh nõn tự nhiên, không còn bóng dáng ổ nhện đỏ gây hại.
• Khi nào cần can thiệp bổ sung: Duy trì kiểm tra hàng tuần trong suốt các tháng mùa mưa cao điểm.

Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:
• Thời gian phục hồi ước tính: 3–4 tuần (phục hồi nhanh khi có đầy đủ ánh nắng mặt trời và thời tiết khô ráo).
• Tiêu chí xác định cây khỏi bệnh:
  1. 100% các khối tổn thương cũ đã khô đen hoàn toàn, bong tróc hoặc rụng lỗ thủng, tuyệt đối không còn lớp phấn trắng nhung sinh sản.
  2. Toàn bộ lứa búp non mới (1 tôm 2–3 lá non) phát triển phẳng phiu, không có vết lõm chén mặt trên hay u phồng mặt dưới.
  3. Năng suất thu hái búp chè trở lại bình thường, búp đạt tiêu chuẩn búp tươi loại 1 của nhà máy chế biến.
• Lưu ý quan trọng về phục hồi mô: Các vết tổn thương cũ khi chết đi sẽ tạo thành các lỗ thủng tròn màu nâu khô trên phiến lá già và không thể hồi phục lại nguyên vẹn; sự khỏi bệnh được xác định bằng việc triệt tiêu hoàn toàn sự sinh sản của dịch hại và lứa búp non mới phát triển hoàn hảo không tì vết.""",
        "recovery_info": "⏱️ Thời gian khống chế bệnh: 2–3 ngày (khối u phồng xẹp lại, lớp nhung trắng lụi tàn, ngừng phát tán mầm bệnh).\n🌱 Thời gian bung chồi lá non mới: 8–12 ngày (búp mới bật lên xanh đanh chắc dưới ánh nắng mặt trời).\n🔄 Thời gian khỏi bệnh & phục hồi hoàn toàn: 3–4 tuần (chu kỳ búp thương phẩm trở lại bình thường).\n📊 Tiên lượng phục hồi: 90–96% nếu tăng cường ánh nắng mặt trời và phun kết hợp thuốc gốc đồng + Triazole.\n💡 Lưu ý phục hồi: Vết tổn thương cũ khi hoại tử sẽ để lại lỗ thủng trên lá già; sự khỏi bệnh thể hiện ở lứa búp mới hoàn toàn nhẵn phẳng."
    },
    {
        "class_name": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",
        "display_name": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf)",
        "description": "Lá chè bị bọ xít muỗi gây hại (Tea mosquito bug infested leaf) do bọ xít muỗi (Helopeltis spp.) chích hút kết hợp tảo và nấm ký sinh Cephaleuros virescens gây nên. Đây là đối tượng gây hại phổ biến trên lá bánh tẻ, lá già và các cành nhánh của bụi chè ở vùng nhiệt đới ẩm. Vết chích hút và sợi tảo không chỉ làm tổn thương lớp biểu bì lá gây suy giảm khả năng quang hợp mà còn xâm nhiễm vào vỏ cành, làm nứt nẻ vỏ thân, gây chết khô cành chè và làm suy kiệt toàn bộ sức sống của nương chè nếu không được điều trị kịp thời.",
        "symptoms": "Trên mặt trên phiến lá già và lá bánh tẻ, bệnh xuất hiện dưới dạng các đốm châm chích, đốm tròn hơi gồ cao, đường kính 3–8mm, bề mặt phủ một lớp lông tơ mịn màu cam sáng, đỏ gỉ sắt hoặc thâm đen dạng giọt dầu chích hút. Về sau, khi vết thương già và khô đi, vết đốm chuyển sang màu xanh xám, xám nâu hoặc màu tro xơ cứng như lớp vảy mốc bám chặt vào biểu bì lá. Trên cọng búp non và thân cành, vỏ cành bị phồng rộp, nứt nẻ dọc thân, vỏ sần sùi bong tróc; các cành bị nhiễm nặng thường vàng lá, rụng lá dần và chết khô từ ngọn xuống.",
        "prevention": "1. Vệ sinh nương chè và phát quang bụi rậm: Thường xuyên làm sạch cỏ dại, phát quang các bờ bụi rậm rạp xung quanh nương chè để triệt tiêu nơi trú ẩn và sinh sản của bọ xít muỗi trưởng thành.\n2. Đốn tỉa tạo tán thông thoáng và trồng cây che bóng hợp lý: Đốn chè đúng kỹ thuật, tỉa bỏ cành tăm, cành sâu bệnh trong lòng tán giúp nương chè thông thoáng ánh nắng; trồng cây che bóng mật độ thích hợp (150–250 cây/ha).\n3. Thu hái búp đúng lứa và chủ động hái chặn: Hái chè đúng chu kỳ để loại bỏ kịp thời các búp non chứa trứng bọ xít muỗi; khi phát hiện ổ dịch cục bộ (tỷ lệ búp bị chích 5–10%), bấm bỏ ngay các búp non bị chích thâm đen đem tiêu hủy để cắt đứt nguồn lây.\n4. Bón phân cân đối N-P-K, không bón thừa đạm: Bón phân cân đối kết hợp phân hữu cơ hoai mục, tăng cường Kali và vi lượng giúp chồi non cứng cáp; hạn chế bón thừa đạm đơn độc làm búp non vươn dài, mềm mọng thu hút bọ xít muỗi đến chích hút.\n5. Ứng dụng biện pháp sinh học và bảo tồn thiên địch: Đặt bẫy dính màu trên nương chè để theo dõi mật độ kết hợp phun định kỳ chế phẩm sinh học nấm xanh (Metarhizium anisopliae) hoặc nấm trắng (Beauveria bassiana); hạn chế phun thuốc hóa học tràn lan để bảo vệ nhện bắt mồi, kiến vống và bọ rùa tự nhiên.",
        "treatment": "Lộ trình điều trị toàn diện: Khơi thông ngay toàn bộ rãnh thoát nước giữa các luống chè để chống ngập úng rễ. Cắt tỉa cành bị nứt vỏ sần sùi hoặc chết khô dưới vết bệnh 3–5cm. Phun thuốc đặc trị bọ xít muỗi và sát khuẩn vết chích hút: Phối hợp thuốc sinh học trừ bọ xít muỗi (Emamectin benzoate hoặc Abamectin) cùng thuốc gốc đồng Copper Oxychloride (Coc 85, 30–40g/16L) hoặc Copper Hydroxide (Champion 77WP) làm ướt đẫm lá và toàn bộ khung thân cành. Ngày 4–7, bón phân Kali Sunfat (K2SO4) kết hợp Magie Sunfat (MgSO4) qua gốc để hỗ trợ vỏ cây liền sẹo. Ngày 8–14, phun nhắc lại lần 2 để diệt triệt để lứa bọ mới nở và du bào tử. Phun vi lượng và axit amin từ ngày 15–35 để nuôi chồi mới. Thời gian phục hồi ước tính: 6–8 tuần.",
        "treatment_steps": """Giai đoạn 1 — Ngày 1: Đánh giá tổn thương vỏ cành & Khơi thông thoát nước:
• Hành động cần làm: Kiểm tra toàn diện nương chè, phân biệt các vết chích hút màu thâm đen, đốm lông nhung màu đỏ cam trên lá già và các cành bị nứt vỏ sần sùi do bọ xít muỗi gây hại. Khơi thông ngay toàn bộ rãnh thoát nước giữa các hàng chè. Dùng kéo tiệt trùng cắt bỏ các cành bị chết khô hoặc nứt vỏ nặng dưới vết bệnh 3–5cm, đem ra khỏi vườn tiêu hủy.
• Triệu chứng cần theo dõi: Các đốm châm chích thâm đen, đốm nhung màu đỏ rỉ sắt/cam sáng trên lá và vết nứt sùi màu gỉ đồng trên vỏ cành.
• Dấu hiệu cải thiện: Nước thừa đọng ở rãnh luống rút cạn; các cành chết khô bị loại bỏ gọn gàng.
• Khi nào cần can thiệp bổ sung: Nếu thấy mật độ bọ xít muỗi trưởng thành xuất hiện nhiều vào lúc sáng sớm hoặc chiều mát, cần kết hợp bẫy dính và phun dập dịch ngay.

Giai đoạn 2 — Ngày 2–3: Phun thuốc trừ bọ xít muỗi & Sát khuẩn gốc đồng đợt 1:
• Hành động cần làm: Phun kết hợp thuốc trị bọ xít muỗi sinh học cùng thuốc sát khuẩn gốc đồng: Copper Oxychloride (Coc 85, 30–40g/bình 16L) hoặc Champion 77WP phối hợp hoạt chất sinh học trừ bọ chích hút. Phun ướt đẫm cả mặt trên lá non, lá già và đặc biệt là toàn bộ khung thân cành bên trong bụi chè vào lúc sáng sớm khi bọ xít muỗi ít di chuyển.
• Triệu chứng cần theo dõi: Sự biến đổi màu sắc của các vết châm chích và lớp lông nhung trên lá và cành.
• Dấu hiệu cải thiện: Vết châm chích se khô miệng, không loang thâm đen; mật độ bọ xít muỗi giảm rõ rệt.
• Khi nào cần can thiệp bổ sung: Nếu gặp mưa to trôi lớp thuốc trước 6 giờ, cần phun nhắc lại khi tán cây ráo nước.

Giai đoạn 3 — Ngày 4–7: Bổ sung dinh dưỡng hồi sức rễ & Cải tạo đất:
• Hành động cần làm: Bón phân bổ sung qua gốc: Phân Kali Sunfat (K2SO4) kết hợp Magie Sunfat (MgSO4) và phân hữu cơ vi sinh nhằm hỗ trợ phục hồi hệ mạch dẫn vỏ cây. Xới xáo phá váng lớp đất mặt quanh tán chè.
• Triệu chứng cần theo dõi: Độ bám dính và khô se của các vết thương trên mặt lá.
• Dấu hiệu cải thiện: Vết bệnh khô giòn lại, chuyển thành các vảy xám bong mép; không xuất hiện vết chích hút ướt mới.
• Khi nào cần can thiệp bổ sung: Nếu trên các cành non vẫn còn bọ xít muỗi phát sinh, cần phun chế phẩm nấm ký sinh côn trùng Metarhizium.

Giai đoạn 4 — Ngày 8–14: Phun củng cố diệt ấu trùng đợt 2:
• Hành động cần làm: Phun nhắc lại lần 2 bằng hoạt chất tiếp xúc thảo mộc hoặc Copper Oxychloride để bảo vệ lứa búp mới nhú khỏi lứa bọ non mới nở. Phun bao quát cả lớp đất quanh gốc chè.
• Triệu chứng cần theo dõi: Trạng thái của lớp vỏ cành tại các mắt ngủ trên thân chè.
• Dấu hiệu cải thiện: Vết nứt trên vỏ cành se lại, khô ráo, không còn rỉ nhựa hay sùi bọt; các mắt ngủ bắt đầu nhú điểm xanh báo hiệu chồi mới.
• Khi nào cần can thiệp bổ sung: Duy trì khoảng cách thông thoáng giữa các tán chè để giảm ẩm ướt nơi bọ xít muỗi ẩn nấp.

Giai đoạn 5 — Ngày 15–35: Tái tạo tầng vỏ mô sẹo & Bật chồi mới:
• Hành động cần làm: Phun phân bón lá giàu Axit Amin hữu cơ và Trung vi lượng để kích thích phân bào tái tạo tầng biểu bì vỏ thân. Giữ luống chè sạch cỏ dại.
• Triệu chứng cần theo dõi: Sự hình thành mô sẹo tại các vết nứt vỏ cành và sự phát triển của chồi nách mới.
• Dấu hiệu cải thiện: Vỏ cành liền sẹo, mượt mà trở lại; chồi non mới mọc khỏe khoắn từ thân cành đã khỏi bệnh, lá xanh dày bóng.
• Khi nào cần can thiệp bổ sung: Bổ sung vôi bột định kỳ 6 tháng/lần vào mùa mưa để khử chua đất.

Giai đoạn cuối — Đánh giá phục hồi & Tiêu chuẩn khỏi bệnh:
• Thời gian phục hồi ước tính: 6–8 tuần.
• Tiêu chí xác định cây khỏi bệnh:
  1. 100% các vết chích hút và đốm nhung đỏ cam trên lá đã khô chết hoàn toàn, biến thành các vảy xám tro, hoàn toàn không còn khả năng lây lan.
  2. Các vết nứt vỏ trên thân cành đã liền sẹo hoàn toàn, không còn hiện tượng vàng lá hay chết cành khô từ ngọn xuống.
  3. Cây chè hồi sinh bộ tán, chồi búp mới bật rộ từ các cành sạch bệnh, màu xanh đậm tự nhiên, mật độ bọ xít muỗi về mức an toàn sinh học.
• Lưu ý quan trọng về phục hồi mô: Các vết lõm sẹo trên phiến lá già và các vết rạn nứt cũ trên vỏ gỗ sẽ để lại vết sẹo xám vĩnh viễn không thể phẳng nhẵn như ban đầu; sự khỏi bệnh được khẳng định khi bọ xít muỗi và mầm bệnh bị tiêu diệt hoàn toàn, vỏ thân ngừng hủy hoại và cây chè phục hồi trọn vẹn sức sinh trưởng đâm búp mới.""",
        "recovery_info": "⏱️ Thời gian khống chế bệnh: 5–7 ngày (vết châm chích khô miệng, mật độ bọ xít muỗi giảm triệt để).\n🌱 Thời gian bung chồi lá non mới: 14–21 ngày (chồi nách mới bật lên từ các đốt thân sạch bệnh).\n🔄 Thời gian khỏi bệnh & phục hồi hoàn toàn: 6–8 tuần (vỏ cành liền sẹo, toàn bộ tán chè phục hồi sinh lực).\n📊 Tiên lượng phục hồi: 85–90% khi cải tạo tốt hệ thống thoát nước rễ và quản lý tốt bọ xít muỗi.\n💡 Lưu ý phục hồi: Vết nứt sẹo cũ trên vỏ gỗ sẽ để lại dấu tích vĩnh viễn; cây khỏi bệnh khi vết nứt se khô liền sẹo và búp mới phát triển mạnh."
    }
]

def init_database():
    """Create all tables and seed disease data with Tea Plant diseases."""
    Base.metadata.create_all(bind=engine)
    
    # Add new columns if they don't exist yet (SQLite migration)
    insp = inspect(engine)
    existing_columns = [col["name"] for col in insp.get_columns("diseases")]
    with engine.connect() as conn:
        if "treatment_steps" not in existing_columns:
            conn.execute(text("ALTER TABLE diseases ADD COLUMN treatment_steps TEXT"))
            conn.commit()
            logger.info("Added 'treatment_steps' column to diseases table.")
        if "recovery_info" not in existing_columns:
            conn.execute(text("ALTER TABLE diseases ADD COLUMN recovery_info TEXT"))
            conn.commit()
            logger.info("Added 'recovery_info' column to diseases table.")
    
    db = SessionLocal()
    try:
        tea_class_names = [item["class_name"] for item in DISEASE_DATA]
        existing_diseases = db.query(Disease).all()
        has_old_data = any(d.class_name not in tea_class_names for d in existing_diseases)
        
        if len(existing_diseases) == 0 or has_old_data:
            # Cleanly replace catalog entries with the 6 verified Tea Plant diseases
            db.query(Disease).delete()
            db.commit()
            for item in DISEASE_DATA:
                disease = Disease(**item)
                db.add(disease)
            db.commit()
            logger.info("Initialized disease library with 6 verified Tea Plant (Camellia sinensis) diseases.")
        else:
            # Update descriptions if needed
            for item in DISEASE_DATA:
                existing = db.query(Disease).filter(Disease.class_name == item["class_name"]).first()
                if existing:
                    existing.display_name = item["display_name"]
                    existing.description = item["description"]
                    existing.symptoms = item["symptoms"]
                    existing.prevention = item["prevention"]
                    existing.treatment = item["treatment"]
                    existing.treatment_steps = item.get("treatment_steps")
                    existing.recovery_info = item.get("recovery_info")
            db.commit()
            logger.info("Verified and updated Tea Plant disease catalog.")
    finally:
        db.close()
