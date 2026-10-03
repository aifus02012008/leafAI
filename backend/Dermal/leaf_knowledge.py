# -*- coding: utf-8 -*-
"""
LEAF_AI Agricultural Knowledge Base
Chuẩn hóa kiến thức 6 bệnh cà chua và Cẩm nang chăm sóc & phòng bệnh chuẩn FAO.
"""

TOMATO_DISEASES = {
    "Bacterial_spot": {
        "id": "bacterial_spot",
        "name_en": "Bacterial Spot",
        "name_vi": "Đốm vi khuẩn",
        "pathogen": "Xanthomonas campestris pv. vesicatoria",
        "color": "#ef4444",
        "badge_class": "badge-danger",
        "symptoms": {
            "stage_1": "Các đốm nhỏ 1-2mm úng nước trên lá bánh tẻ và lá già, mép đốm có quầng vàng nhạt trong suốt.",
            "stage_2": "Vết bệnh mở rộng sẫm màu nâu đen, tâm hoại tử hơi lõm, bề mặt ráp sần sùi.",
            "stage_3": "Nhiều đốm liên kết làm rách phiến lá, lá vàng khô giòn và rụng sớm từ gốc lên ngọn."
        },
        "conditions": "Nhiệt độ ấm 24-30°C, ẩm độ cao >85%, giọt bắn mưa lớn hoặc tưới phun mưa đọng nước.",
        "prevention": "Sử dụng hạt giống đã xử lý nhiệt/hóa chất, luân canh cây khác họ cà ít nhất 2 năm, tưới rãnh hoặc nhỏ giọt.",
        "treatment": {
            "cultural": "Cắt tỉa lá già sát đất, vệ sinh tàn dư vườn, tránh chạm vào cây khi lá còn ướt sương.",
            "biological": "Phun chế phẩm sinh học chứa vi khuẩn đối kháng Bacillus subtilis hoặc Streptomyces spp.",
            "chemical": "Phun gốc đồng (Copper Hydroxide, Copper Oxychloride) phối hợp Kasugamycin luân phiên."
        },
        "references": "FAO Plant Protection Guide, UC Davis IPM Tomato Bacterial Spot Guidelines."
    },
    "Early_blight": {
        "id": "early_blight",
        "name_en": "Early Blight",
        "name_vi": "Úa sớm (Đốm vòng)",
        "pathogen": "Alternaria solani",
        "color": "#f97316",
        "badge_class": "badge-warning",
        "symptoms": {
            "stage_1": "Đốm nhỏ hình tròn màu nâu sẫm trên các tầng lá già dưới gốc.",
            "stage_2": "Vết bệnh lan rộng 5-15mm xuất hiện các vân tròn đồng tâm đặc trưng (hình bia bắn), bao quanh bởi quầng vàng rõ rệt.",
            "stage_3": "Phiến lá cháy khô hoàn toàn, cuống lá gãy rũ treo trên thân, thân cây xuất hiện vết lõm hình bầu dục sậm màu."
        },
        "conditions": "Thời tiết ấm ẩm xen kẽ các đợt nắng ráo, nhiệt độ 24-29°C, sương đêm đọng kéo dài.",
        "prevention": "Dọn dẹp triệt để tàn dư vụ trước, tỉa cành gốc cách mặt đất 25-30cm, phủ bạt nilon hạn chế bắn đất.",
        "treatment": {
            "cultural": "Tăng cường bón kali và canxi giúp tế bào lá cứng cáp, ngắt bỏ ngay lá chớm xuất hiện vòng tròn đồng tâm.",
            "biological": "Xử lý nấm đối kháng Trichoderma harzianum quanh vùng rễ và phun dịch chiết thảo mộc.",
            "chemical": "Phun luân phiên Mancozeb, Difenoconazole, Chlorothalonil hoặc Azoxystrobin theo liều khuyến cáo."
        },
        "references": "FAO IPM Field Handbook, Cornell University Vegetable MD Online."
    },
    "Late_blight": {
        "id": "late_blight",
        "name_en": "Late Blight",
        "name_vi": "Sương mai (Mốc sương)",
        "pathogen": "Phytophthora infestans",
        "color": "#dc2626",
        "badge_class": "badge-danger",
        "symptoms": {
            "stage_1": "Vết bệnh hình dạng bất định úng nước màu xanh tái xám ở chóp hoặc mép lá non và bánh tẻ.",
            "stage_2": "Vết bệnh mở rộng nhanh chóng chuyển màu nâu sẫm nhạt dầu; mặt dưới lá phủ lớp tơ mốc trắng mịn vào sáng sớm.",
            "stage_3": "Toàn bộ tán lá úa thối nhanh trong 2-4 ngày, thân mềm gãy, bốc mùi tanh ẩm đặc trưng, thất thu mùa màng nếu không chặn đứng."
        },
        "conditions": "Trời âm u nhiều mây, mưa phùn, sương mù dày, nhiệt độ mát 15-22°C, ẩm độ bão hòa >90%.",
        "prevention": "Chọn giống kháng sương mai, mật độ hàng rộng thoáng gió, che phủ vòm mưa, tuyệt đối không đọng ẩm đêm.",
        "treatment": {
            "cultural": "Tiêu hủy ngay bụi cây nhiễm đầu tiên, ngưng tưới nước khi độ ẩm ngoài trời tăng cao.",
            "biological": "Chế phẩm chitosan phối hợp nấm cộng sinh mycorrhiza tăng sức đề kháng biểu bì.",
            "chemical": "Phun chặn tức thì khi có sương lạnh: Metalaxyl-M, Dimethomorph, Cymoxanil hoặc Fosetyl-Aluminium."
        },
        "references": "FAO Late Blight Global Initiative, UC IPM Tomato Pest Management."
    },
    "Septoria_leaf_spot": {
        "id": "septoria_leaf_spot",
        "name_en": "Septoria Leaf Spot",
        "name_vi": "Đốm lá Septoria",
        "pathogen": "Septoria lycopersici",
        "color": "#eab308",
        "badge_class": "badge-warning",
        "symptoms": {
            "stage_1": "Vết đốm nhỏ li ti 1-3mm màu nâu xám viền nâu đậm xuất hiện dày đặc trên lá già.",
            "stage_2": "Tâm vết bệnh sáng màu chuyển sang màu xám tro, xuất hiện các chấm đen nhỏ li ti (ổ bào tử nấm pycnidia).",
            "stage_3": "Hàng trăm vết đốm liên kết khiến lá vàng úa hàng loạt, lá cuộn lại và rụng sớm làm trơ cành và cháy quả do nắng."
        },
        "conditions": "Nhiệt độ 20-26°C kết hợp các đợt mưa kéo dài hoặc tưới nước mạnh làm văng bùn đất lên lá.",
        "prevention": "Bọc cọc chống cà chua sạch sẽ, dọn lá sát đất, dùng lưới che mặt luống giữ ẩm đều.",
        "treatment": {
            "cultural": "Tỉa thông thoáng gốc, bón phân cân đối tránh thừa đạm làm lá non mỏng manh.",
            "biological": "Phun dịch tỏi ớt lên men kết hợp vi sinh vật bản địa (IMO/EM).",
            "chemical": "Phun Chlorothalonil hoặc Copper Oxychloride ngay khi phát hiện những đốm đầu tiên."
        },
        "references": "FAO Plant Health Division, Missouri Botanical Garden IPM."
    },
    "Leaf_mold": {
        "id": "leaf_mold",
        "name_en": "Leaf Mold",
        "name_vi": "Nấm mốc lá",
        "pathogen": "Passalora fulva (Cladosporium fulvum)",
        "color": "#10b981",
        "badge_class": "badge-success",
        "symptoms": {
            "stage_1": "Mặt trên lá xuất hiện các đốm màu vàng xanh nhạt mờ nhạt ranh giới không phân định.",
            "stage_2": "Mặt dưới lá tương ứng xuất hiện thảm nấm mịn màu xanh ô liu chuyển dần sang nâu nhung.",
            "stage_3": "Phiến lá quăn queo, khô cháy và rụng, thường bùng phát nghiêm trọng trong nhà màng, nhà kính kín gió."
        },
        "conditions": "Ẩm độ không khí nhà kính >85%, nhiệt độ ấm 22-26°C, không khí tù đọng kém lưu thông.",
        "prevention": "Tăng cường quạt thông gió đối lưu trong nhà kính, mở lưới mái, tăng nhiệt độ sấy nhẹ nếu trời lạnh ẩm.",
        "treatment": {
            "cultural": "Tỉa lá già định kỳ hàng tuần, không để mật độ cành lá quá dày đặc chen chúc.",
            "biological": "Phun phòng bằng nấm ký sinh đối kháng Trichoderma và dịch chiết quế.",
            "chemical": "Phun luân phiên hợp chất Triazole hoặc Bordeaux pha tỷ lệ chuẩn."
        },
        "references": "FAO Greenhouse Crop Production Handbook, PennState Extension."
    },
    "Powdery_mildew": {
        "id": "powdery_mildew",
        "name_en": "Powdery Mildew",
        "name_vi": "Phấn trắng",
        "pathogen": "Leveillula taurica / Oidium neolycopersici",
        "color": "#06b6d4",
        "badge_class": "badge-info",
        "symptoms": {
            "stage_1": "Các mảng bụi phấn màu trắng xám xuất hiện rải rác trên bề mặt lá như phủ bột mì.",
            "stage_2": "Lớp phấn trắng lan rộng khắp hai mặt lá, cuống hoa và đài hoa, lá gợn sóng biến dạng.",
            "stage_3": "Vùng mô lá bên dưới chuyển vàng rồi khô cháy thành mảng lớn giòn vụn, làm giảm hiệu suất quang hợp nặng nề."
        },
        "conditions": "Khí hậu khô râm mát ban ngày xen kẽ đêm ẩm ướt nhiều sương, nhiệt độ 20-28°C.",
        "prevention": "Tưới đủ ẩm cho gốc cây, tránh để cây chịu sốc hạn rồi ngập ẩm đột ngột, tỉa tán đón nắng.",
        "treatment": {
            "cultural": "Ngắt bỏ lá bị bao phủ phấn nặng cho vào túi kín đem tiêu hủy.",
            "biological": "Phun dung dịch dầu neem nguyên chất (Neem oil) hoặc hỗn hợp Baking soda + xà phòng sinh học hữu cơ.",
            "chemical": "Phun bột lưu huỳnh (Sulfur WG) hoặc Difenoconazole nồng độ nhẹ."
        },
        "references": "FAO Organic Tomato Handbook, UC Davis IPM Powdery Mildew."
    },
    "Healthy": {
        "id": "healthy",
        "name_en": "Healthy Tomato Leaf",
        "name_vi": "Lá khỏe mạnh",
        "pathogen": "None (Không có mầm bệnh)",
        "color": "#22c55e",
        "badge_class": "badge-success",
        "severity": "Khỏe mạnh",
        "symptoms": {
            "stage_1": "Lá có màu xanh lục tự nhiên, phiến lá phẳng phiu, hệ gân lá phát triển đều đặn.",
            "stage_2": "Không có đốm nấm, không vết hoại tử mép lá, không có mốc hay dấu vết chích hút của côn trùng.",
            "stage_3": "Cây sinh trưởng sung mãn, hiệu suất quang hợp tối ưu, chồi non và nụ hoa phát triển khỏe mạnh."
        },
        "conditions": "Nhiệt độ 20-28°C, ánh sáng tán xạ 6-8h/ngày, ẩm độ đất 65-75%, thông gió tốt.",
        "prevention": "Duy trì quy trình canh tác GAP, tưới rãnh hoặc nhỏ giọt, bổ sung hữu cơ vi sinh định kỳ.",
        "treatment": {
            "cultural": "Tiếp tục duy trì chế độ chăm sóc tiêu chuẩn, tỉa cành định kỳ tạo độ thông thoáng gốc.",
            "biological": "Phun phòng định kỳ bằng nấm đối kháng Trichoderma hoặc dịch ngâm tỏi ớt.",
            "chemical": "Không cần sử dụng bất kỳ loại thuốc BVTV hóa học nào."
        },
        "references": "FAO Healthy Tomato Crop Management Guidelines, PlantVillage Benchmark."
    },
    "Target_spot": {
        "id": "target_spot",
        "name_en": "Target Spot",
        "name_vi": "Đốm mắt cua (Target Spot)",
        "pathogen": "Corynespora cassiicola",
        "color": "#d97706",
        "badge_class": "badge-warning",
        "severity": "Trung bình",
        "symptoms": {
            "stage_1": "Đốm nhỏ màu nâu rải rác trên phiến lá, viền xung quanh có quầng vàng nhạt.",
            "stage_2": "Vết bệnh phát triển thành đốm tròn lớn có vân tròn đồng tâm như mắt cua (hình bia bắn).",
            "stage_3": "Vết bệnh liên kết làm cháy lá diện rộng, rụng lá nhanh khiến quả bị phơi nắng."
        },
        "conditions": "Nhiệt độ ấm 25-32°C, độ ẩm cao >80%, thời tiết mưa nắng xen kẽ kéo dài.",
        "prevention": "Luân canh cây trồng khác họ cà, vệ sinh sạch tàn dư vụ trước, khoảng cách trồng thông thoáng.",
        "treatment": {
            "cultural": "Tỉa bỏ lá già sát gốc, tránh làm ướt tán lá khi tưới vào chiều tối.",
            "biological": "Phun chế phẩm vi sinh Bacillus subtilis hoặc Streptomyces spp.",
            "chemical": "Phun Azoxystrobin, Difenoconazole hoặc Chlorothalonil khi chớm xuất hiện đốm."
        },
        "references": "FAO Integrated Pest Management Guidelines for Solanaceous Crops."
    },
    "Tomato_yellow_leaf_curl_virus": {
        "id": "tomato_yellow_leaf_curl_virus",
        "name_en": "Tomato Yellow Leaf Curl Virus (TYLCV)",
        "name_vi": "Xoăn vàng lá virus",
        "pathogen": "Tomato yellow leaf curl begomovirus (Vector: Bọ phấn trắng)",
        "color": "#eab308",
        "badge_class": "badge-danger",
        "severity": "Nghiêm trọng",
        "symptoms": {
            "stage_1": "Lá đọt non nhạt màu, rìa mép lá cong nhẹ lên phía trên dạng lòng thuyền.",
            "stage_2": "Phiến lá co cụm, biến dạng xoăn tít, gân lá dày sần sùi và vàng úa rõ rệt.",
            "stage_3": "Cây còi cọc ngừng sinh trưởng, hoa rụng hàng loạt, không thể đậu quả hoặc quả teo tóp."
        },
        "conditions": "Khí hậu khô nóng tạo điều kiện cho bọ phấn trắng sinh sôi nảy nở và truyền bệnh.",
        "prevention": "Trồng giống kháng TYLCV F1, dùng bẫy dính màu vàng, phủ lưới chắn côn trùng 50 mesh.",
        "treatment": {
            "cultural": "Nhổ bỏ ngay cây nhiễm bệnh và tiêu hủy kín để tránh bọ phấn phát tán virus sang cây khác.",
            "biological": "Phun dầu khoáng, dầu neem hoặc thả bọ xít bắt mồi Nesidiocoris tenuis diệt bọ phấn.",
            "chemical": "Phun trừ bọ phấn bằng Dinotefuran, Thiamethoxam hoặc Spirotetramat luân phiên."
        },
        "references": "FAO Global Tomato Virus Disease Compendium, AVRDC Technical Bulletin."
    },
    "Tomato_mosaic_virus": {
        "id": "tomato_mosaic_virus",
        "name_en": "Tomato Mosaic Virus (ToMV)",
        "name_vi": "Khảm lá virus",
        "pathogen": "Tomato mosaic tobamovirus (ToMV)",
        "color": "#8b5cf6",
        "badge_class": "badge-danger",
        "severity": "Nghiêm trọng",
        "symptoms": {
            "stage_1": "Xuất hiện các vệt loang lổ xanh đậm xen kẽ xanh nhạt hoặc vàng úa dạng khảm trên lá non.",
            "stage_2": "Lá bị nhăn nheo, gồ ghề, phiến lá hẹp lại thành dạng dải ruy băng mỏng manh.",
            "stage_3": "Cây sinh trưởng kém, quả chín loang lổ bên trong có vệt sọc nâu hoại tử làm mất phẩm chất."
        },
        "conditions": "Lây truyền cơ học qua tay người làm vườn, dao kéo cắt tỉa, hoặc tồn dư trong hạt giống.",
        "prevention": "Xử lý nhiệt hạt giống 70°C trong 3 ngày, sát trùng tay và dụng cụ bằng xà phòng chuyên dụng.",
        "treatment": {
            "cultural": "Tiêu hủy cây nhiễm bệnh, không chạm tay vào cây khỏe sau khi chạm vào cây nghi ngờ.",
            "biological": "Tăng cường bón phân hữu cơ vi sinh, bổ sung Chitosan nâng cao sức đề kháng tế bào.",
            "chemical": "Không có thuốc hóa học trị virus, tập trung ngăn chặn đường lây lan cơ giới."
        },
        "references": "FAO Plant Health Directorate, Cornell Vegetable MD."
    },
    "Spider_mites": {
        "id": "spider_mites",
        "name_en": "Spider Mites (Two-spotted)",
        "name_vi": "Nhện đỏ hai chấm",
        "pathogen": "Tetranychus urticae (Arachnida: Tetranychidae)",
        "color": "#f43f5e",
        "badge_class": "badge-warning",
        "severity": "Trung bình",
        "symptoms": {
            "stage_1": "Mặt trên lá xuất hiện các chấm trắng hoặc vàng li ti do nhện chích hút nhựa tế bào biểu bì.",
            "stage_2": "Mặt dưới lá phủ lớp màng tơ nhện mịn mỏng, phiến lá bạc màu đồng thau, mép lá khô cháy.",
            "stage_3": "Lá khô giòn và rụng trơ cành, toàn bộ ngọn cây bị giăng tơ dày đặc, cây kiệt sức nhanh chóng."
        },
        "conditions": "Thời tiết hanh khô, nhiệt độ cao 27-35°C, nhà kính ít gió hoặc bón thừa đạm.",
        "prevention": "Duy trì độ ẩm không khí trong vườn, phun tưới nước mặt dưới lá làm trôi nhện, không bón thừa đạm.",
        "treatment": {
            "cultural": "Cắt tỉa lá già phía dưới bị hại nặng đem chôn lấp hoặc tiêu hủy.",
            "biological": "Thả nhện bắt mồi Phytoseiulus persimilis hoặc phun chế phẩm nấm ký sinh Beauveria bassiana.",
            "chemical": "Phun luân phiên thuốc đặc trị nhện: Abamectin, Diafenthiuron, Propargite hoặc Spiromesifen."
        },
        "references": "FAO IPM Guidelines for Protected Cultivation, UC IPM Tetranychid Mites."
    }
}

CARE_HANDBOOK = {
    "principles_8": [
        {"num": 1, "title": "Chọn giống kháng bệnh", "desc": "Ưu tiên giống F1 có chứng nhận kháng héo vi khuẩn, sương mai, virus xoăn vàng lá."},
        {"num": 2, "title": "Khử trùng đất & giá thể", "desc": "Phơi ải đất, rải vôi bột 50-70kg/sào hoặc xử lý nấm Trichoderma 10 ngày trước khi xuống giống."},
        {"num": 3, "title": "Mật độ & khoảng cách chuẩn", "desc": "Cây cách cây 45-50cm, hàng cách hàng 70-80cm, bố trí luống theo hướng gió và ánh nắng sáng."},
        {"num": 4, "title": "Tưới tiêu khoa học", "desc": "Áp dụng tưới nhỏ giọt quanh gốc rễ; không bao giờ tưới phun mưa lúc chiều muộn làm ướt lá qua đêm."},
        {"num": 5, "title": "Bón phân cân đối N-P-K", "desc": "Không bón thừa đạm làm vách tế bào mỏng; tăng cường Silic, Canxi, Bo tăng độ dai biểu bì lá."},
        {"num": 6, "title": "Cắt tỉa & dọn vệ sinh", "desc": "Tỉa chồi nách vô hiệu lúc trời khô ráo; cắt bỏ toàn bộ lá gốc chạm mặt đất cách mặt luống 25-30cm."},
        {"num": 7, "title": "Che phủ mặt luống", "desc": "Dùng màng phủ nông nghiệp hoặc rơm rạ khô ngăn giọt mưa bắn mang nấm khuẩn từ đất lên phiến lá."},
        {"num": 8, "title": "Tiêu hủy tàn dư cây bệnh", "desc": "Không vứt lá bệnh xuống rãnh nước; thu gom vào bao kín mang ra bãi tiêu hủy hoặc rắc vôi chôn sâu."}
    ],
    "inspection_7": [
        {"step": 1, "title": "Quan sát tổng quan luống cây", "desc": "Đi dọc luống lúc sáng sớm quan sát độ đồng đều, phát hiện các điểm úa vàng hoặc chồi non bất thường."},
        {"step": 2, "title": "Kiểm tra mặt dưới lá bánh tẻ", "desc": "Lật nhẹ mặt dưới các lá gần gốc kiểm tra màng tơ trắng (sương mai) hoặc thảm phấn nhung (mốc lá)."},
        {"step": 3, "title": "Soi ngược ánh sáng mặt trời", "desc": "Đưa phiến lá lên nguồn sáng tự nhiên để nhận diện sớm các chấm úng nước li ti của bệnh đốm vi khuẩn."},
        {"step": 4, "title": "Kiểm tra thân & vết cắt tỉa", "desc": "Soi kỹ phần gốc thân, các vết bấm chồi tìm dấu hiệu thâm đen, chảy nhựa hoặc nứt sùi."},
        {"step": 5, "title": "Đo độ ẩm bầu rễ và rãnh luống", "desc": "Kiểm tra đất dưới màng phủ, đảm bảo đất ẩm xốp nhưng không bị sũng nước đọng lâu sau cữ tưới."},
        {"step": 6, "title": "Giám sát bẫy côn trùng", "desc": "Đếm mật độ bọ trĩ, rầy phấn trắng dính trên bẫy dính vàng để ngăn ngừa nguồn lây truyền virus."},
        {"step": 7, "title": "Ghi chép & phân vùng kịp thời", "desc": "Đánh dấu cọc cờ tại vị trí cây có dấu hiệu nghi ngờ để theo dõi tiến triển trong 24 giờ tới."}
    ],
    "ipm_10": [
        {"step": 1, "title": "Khởi đầu bằng cây giống khỏe mạnh", "desc": "Chỉ trồng cây con ươm khay cứng cáp, rễ trắng, không có đốm bệnh."},
        {"step": 2, "title": "Thăm vườn thường xuyên định kỳ", "desc": "Tối thiểu 2 lần/tuần đi kiểm tra chi tiết theo quy trình 7 bước."},
        {"step": 3, "title": "Bảo vệ & phát triển thiên địch", "desc": "Duy trì bọ rùa, ong ký sinh, nhện bắt mồi bằng cách trồng hoa cúc, hoa vạn thọ ven bờ."},
        {"step": 4, "title": "Nâng cao năng lực tự nhận diện", "desc": "Sử dụng LEAF_AI chẩn đoán ngay khi vết bệnh mới chớm ở giai đoạn 1."},
        {"step": 5, "title": "Chỉ can thiệp khi tới ngưỡng kinh tế", "desc": "Không phun phòng thuốc hóa học bừa bãi khi tỷ lệ hại dưới 5% diện tích lá."},
        {"step": 6, "title": "Biện pháp canh tác làm nền móng", "desc": "Luân canh cây họ đậu/hòa thảo, khử chua đất bằng vôi, lên luống cao thoát thủy."},
        {"step": 7, "title": "Ưu tiên cơ giới & rào chắn vật lý", "desc": "Dùng nhà lưới chống côn trùng, bẫy bả dính màu, bạt phủ cách ly mầm bệnh."},
        {"step": 8, "title": "Ưu tiên giải pháp sinh học vi sinh", "desc": "Sử dụng nấm đối kháng Trichoderma, vi khuẩn Bacillus subtilis, dầu neem sinh học."},
        {"step": 9, "title": "Hóa học là cứu cánh cuối cùng", "desc": "Chỉ phun hóa học chọn lọc khi dịch có nguy cơ bùng phát diện rộng vượt kiểm soát."},
        {"step": 10, "title": "Đánh giá hiệu quả & lưu trữ dữ liệu", "desc": "Ghi chép lịch sử chẩn đoán trên LEAF_AI để rút kinh nghiệm cho các vụ mùa sau."}
    ],
    "safe_pesticide": [
        {"rule": "1. Đúng thuốc", "desc": "Chẩn đoán chính xác bệnh trên LEAF_AI trước khi mua thuốc; tuyệt đối không dùng thuốc trừ sâu trị nấm bệnh."},
        {"rule": "2. Đúng lúc", "desc": "Phun khi vết bệnh ở giai đoạn khởi phát; phun vào sáng sớm (khi ráo sương) hoặc chiều mát lặng gió."},
        {"rule": "3. Đúng liều lượng & nồng độ", "desc": "Đo đong chính xác theo khuyến cáo bao bì; không pha quá đặc gây cháy chồi lá, không pha loãng gây lờn thuốc."},
        {"rule": "4. Đúng cách", "desc": "Phun ướt đều 2 mặt lá, chỉnh béc phun hạt mịn như sương, đặc biệt rà kỹ mặt dưới lá nơi nấm ẩn náu."},
        {"rule": "5. Thời gian cách ly (PHI)", "desc": "Ngừng phun thuốc trước khi thu hoạch quả theo đúng số ngày quy định ghi trên nhãn (thường 7-14 ngày)."},
        {"rule": "6. Bảo hộ an toàn tuyệt đối", "desc": "Mặc quần áo dài, khẩu trang than hoạt tính, găng tay và kính mắt; không ăn uống hút thuốc khi đang phun thuốc."}
    ]
}

FAO_IPM_HANDBOOK = {
    "principles": CARE_HANDBOOK.get("principles_8", []),
    "inspection": CARE_HANDBOOK.get("inspection_7", []),
    "ipm": CARE_HANDBOOK.get("ipm_10", []),
    "safe_pesticide": CARE_HANDBOOK.get("safe_pesticide", []),
}

MODEL_METRICS = {
    "v3": {
        "name": "Model V3 (Production)",
        "badge": "Mặc định",
        "architecture": "YOLOv8n (Object Detection)",
        "file": "model/tomato_v3/best.pt",
        "classes_count": 3,
        "classes": ["Bacterial_spot", "Early_blight", "Late_blight"],
        "map50": "0.768",
        "recall": "80.8% (đốm nhỏ)",
        "input_size": "640x640",
        "confidence_threshold": 0.25,
        "status": "ready"
    },
    "v4": {
        "name": "Model V4 (Experimental)",
        "badge": "Mở rộng",
        "architecture": "YOLOv8n (Object Detection)",
        "file": "model/tomato_v4/best.pt",
        "classes_count": 6,
        "classes": [
            "Bacterial_spot", "Early_blight", "Late_blight",
            "Septoria_leaf_spot", "Leaf_mold", "Powdery_mildew"
        ],
        "input_size": "640x640",
        "epochs": 25,
        "status": "experimental",
        "note": "Hỗ trợ 6 lớp bệnh mở rộng"
    }
}
