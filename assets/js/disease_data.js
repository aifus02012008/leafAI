/**
 * LEAF_AI - Kho tri thức bệnh hại trên lá vải thiều (Litchi chinensis) và cẩm nang IPM vườn vải.
 * Khóa của mỗi bệnh trùng với tên lớp mô hình trả về; `aliases` gom các cách đặt tên lớp khác.
 */
const LEAF_DATA = {
  crop: {
    name_vi: 'vải thiều',
    region: 'Lục Ngạn',
    latin: 'Litchi chinensis Sonn.'
  },

  diseases: {
    "Anthracnose": {
      id: "anthracnose",
      name_en: "Anthracnose",
      name_vi: "Thán thư",
      pathogen: "Colletotrichum gloeosporioides",
      kind: "Nấm",
      aliases: ["anthracnose", "than_thu", "colletotrichum"],
      color: "#c2410c",
      severity_default: "Nghiêm trọng",
      thumb: "assets/images/anthracnose.svg",
      symptoms: {
        stage_1: "Chấm nhỏ màu nâu nhạt xuất hiện ở chóp hoặc mép lá non, lá bánh tẻ; quanh chấm có quầng vàng mờ.",
        stage_2: "Vết bệnh lan thành mảng nâu hình tròn hoặc bất định, viền nâu sẫm; khi trời ẩm trên vết có các chấm đen nhỏ xếp thành vòng.",
        stage_3: "Nhiều vết liên kết làm cháy khô cả đoạn lá, lộc non quăn đen và rụng; bệnh lan sang chùm hoa, làm hoa thâm đen và quả non rụng."
      },
      conditions: "Nhiệt độ 25–30°C, ẩm độ cao, mưa nhiều kéo dài trong các đợt ra lộc, ra hoa; vườn rậm rạp, thiếu ánh sáng.",
      prevention: "Tỉa cành tạo tán thông thoáng sau thu hoạch, thu gom lá và cành bệnh đem tiêu hủy, bón cân đối và không để thừa đạm khi cây ra lộc.",
      treatment: {
        cultural: "Cắt bỏ lộc, lá và chùm hoa bị bệnh nặng, mang ra khỏi vườn tiêu hủy; khơi thông rãnh thoát nước, tỉa cành trong tán cho thoáng.",
        biological: "Phun chế phẩm vi khuẩn đối kháng Bacillus subtilis lên lộc non; bón nấm Trichoderma cùng phân hữu cơ hoai mục quanh gốc.",
        chemical: "Khi bệnh vượt ngưỡng, phun luân phiên thuốc gốc Azoxystrobin, Difenoconazole, Propineb hoặc Mancozeb theo danh mục được phép, không phun khi hoa nở rộ."
      },
      references: "FAO, The Lychee Crop in Asia and the Pacific (Menzel, 2002); khuyến cáo của ngành bảo vệ thực vật"
    },
    "Downy_blight": {
      id: "downy_blight",
      name_en: "Downy Blight",
      name_vi: "Sương mai",
      pathogen: "Peronophythora litchii",
      kind: "Nấm noãn",
      aliases: ["downy_blight", "downy", "suong_mai", "peronophythora"],
      color: "#dc2626",
      severity_default: "Nghiêm trọng",
      thumb: "assets/images/downy_blight.svg",
      symptoms: {
        stage_1: "Trên lá non xuất hiện vết úng nước màu xanh xám, hình dạng bất định, thường bắt đầu từ mép lá.",
        stage_2: "Vết bệnh chuyển nâu sẫm và lan nhanh; khi trời ẩm, mặt vết bệnh phủ lớp mốc trắng mịn.",
        stage_3: "Lá non thối khô, chùm hoa và quả bị thối nâu, phủ mốc trắng rồi rụng hàng loạt sau vài ngày mưa phùn."
      },
      conditions: "Mưa phùn, nồm ẩm kéo dài, ẩm độ không khí trên 85–90%, nhiệt độ khoảng 22–25°C, thường gặp từ giai đoạn ra hoa đến quả chín.",
      prevention: "Giữ tán thông thoáng, thoát nước tốt; theo dõi sát thời tiết nồm ẩm để xử lý sớm; thu gom lá, quả rụng không để lại trong vườn.",
      treatment: {
        cultural: "Cắt bỏ phần lá, chùm hoa bị bệnh và quả rụng, đem tiêu hủy xa vườn; tránh tưới phun lên tán vào chiều tối.",
        biological: "Phun chế phẩm Bacillus subtilis hoặc Trichoderma lên tán ngay khi dự báo có đợt mưa ẩm kéo dài.",
        chemical: "Khi có đợt mưa phùn kéo dài và đã thấy vết bệnh, phun thuốc gốc Metalaxyl + Mancozeb, Cymoxanil + Mancozeb hoặc Dimethomorph theo danh mục được phép."
      },
      references: "FAO, The Lychee Crop in Asia and the Pacific (Menzel, 2002); khuyến cáo của ngành bảo vệ thực vật"
    },
    "Leaf_blight": {
      id: "leaf_blight",
      name_en: "Leaf Blight",
      name_vi: "Cháy lá",
      pathogen: "Pestalotiopsis spp.",
      kind: "Nấm",
      aliases: ["leaf_blight", "chay_la", "pestalotiopsis", "leaf_spot", "dom_la"],
      color: "#a16207",
      severity_default: "Trung bình",
      thumb: "assets/images/leaf_blight.svg",
      symptoms: {
        stage_1: "Chóp lá hoặc mép lá chuyển màu nâu nhạt, ranh giới với phần lá xanh có viền nâu sẫm gợn sóng.",
        stage_2: "Vết cháy lan dần từ chóp và mép vào phía gân chính, chuyển màu xám nâu; trên vết có nhiều chấm đen nhỏ.",
        stage_3: "Nửa lá hoặc cả lá chét khô cháy, giòn và rụng sớm, cây suy yếu, ảnh hưởng đến đợt lộc sau."
      },
      conditions: "Thời tiết nóng ẩm, mưa nhiều; cây suy yếu do thiếu dinh dưỡng, rễ bị úng hoặc lá có vết thương do côn trùng, gió bão.",
      prevention: "Chăm sóc cho cây khỏe: bón phân cân đối, bổ sung kali; thoát nước tốt mùa mưa; hạn chế vết thương trên lá.",
      treatment: {
        cultural: "Cắt bỏ các lá chét bị cháy nặng, thu gom lá rụng đem tiêu hủy; bổ sung phân hữu cơ và kali để cây phục hồi.",
        biological: "Bón Trichoderma cùng phân hữu cơ quanh gốc, phun chế phẩm Bacillus subtilis lên tán.",
        chemical: "Khi bệnh lan rộng, phun thuốc gốc đồng (Copper Oxychloride), Propineb hoặc Difenoconazole theo danh mục được phép."
      },
      references: "FAO, The Lychee Crop in Asia and the Pacific (Menzel, 2002); khuyến cáo của ngành bảo vệ thực vật"
    },
    "Algal_spot": {
      id: "algal_spot",
      name_en: "Algal Spot (Red Rust)",
      name_vi: "Đốm rong",
      pathogen: "Cephaleuros virescens",
      kind: "Tảo",
      aliases: ["algal_spot", "algal_leaf_spot", "red_rust", "dom_rong", "cephaleuros"],
      color: "#0e7490",
      severity_default: "Nhẹ",
      thumb: "assets/images/algal_spot.svg",
      symptoms: {
        stage_1: "Mặt trên lá xuất hiện đốm tròn nhỏ 2–5 mm, hơi nổi, màu xám xanh.",
        stage_2: "Đốm chuyển màu đỏ gạch hoặc cam như lớp nhung, nhiều đốm mọc thành cụm trên lá già trong tán.",
        stage_3: "Lá bị phủ nhiều đốm, giảm khả năng quang hợp, lá vàng và rụng sớm; tảo có thể lan sang cành non."
      },
      conditions: "Vườn rậm rạp, ẩm ướt, thiếu ánh sáng; mưa nhiều; cây già, chăm sóc kém.",
      prevention: "Tỉa cành tạo tán thông thoáng cho ánh sáng lọt vào trong tán, làm cỏ quanh gốc, bón phân đầy đủ cho cây.",
      treatment: {
        cultural: "Tỉa bỏ cành lá bị nặng trong tán, phát quang vườn để giảm ẩm độ.",
        biological: "Chưa có chế phẩm sinh học đặc hiệu; ưu tiên biện pháp canh tác để giảm ẩm trong tán.",
        chemical: "Khi mật độ đốm cao, phun thuốc gốc đồng (Copper Hydroxide, Copper Oxychloride) hoặc hỗn hợp Bordeaux theo khuyến cáo."
      },
      references: "FAO, The Lychee Crop in Asia and the Pacific (Menzel, 2002); khuyến cáo của ngành bảo vệ thực vật"
    },
    "Erinose": {
      id: "erinose",
      name_en: "Erinose Mite",
      name_vi: "Nhện lông nhung",
      pathogen: "Aceria litchii",
      kind: "Nhện hại",
      aliases: ["erinose", "erinose_mite", "leaf_mite", "leaf_mites", "mite", "nhen_long_nhung", "aceria"],
      color: "#7e22ce",
      severity_default: "Trung bình",
      thumb: "assets/images/erinose.svg",
      symptoms: {
        stage_1: "Mặt dưới lá non xuất hiện các mảng lông tơ màu trắng bạc; mặt trên tương ứng hơi phồng lên.",
        stage_2: "Lớp lông chuyển sang màu vàng nâu rồi nâu đỏ như nhung; lá phồng rộp, xoăn mép, biến dạng.",
        stage_3: "Lá chuyển nâu sẫm, khô và rụng; lộc non, chùm hoa bị hại làm cây ra hoa kém, đậu quả ít."
      },
      conditions: "Phát sinh mạnh trên các đợt lộc xuân và lộc thu; lây lan theo gió, côn trùng và qua cành chiết, cây giống mang nhện.",
      prevention: "Dùng cây giống sạch nhện; cắt bỏ cành lá bị nhện sau thu hoạch; nuôi các đợt lộc ra đồng loạt để dễ phòng trừ.",
      treatment: {
        cultural: "Cắt bỏ toàn bộ lá, cành bị lông nhung và đem tiêu hủy, không để lại trong vườn.",
        biological: "Phun dầu khoáng hoặc chế phẩm thảo mộc khi lộc non dài 3–5 cm; bảo vệ nhện bắt mồi và các loài thiên địch trong vườn.",
        chemical: "Khi mật độ nhện cao, phun thuốc gốc Abamectin hoặc lưu huỳnh lên lộc non theo danh mục được phép. Đây là nhện hại, thuốc trừ nấm không có tác dụng."
      },
      references: "FAO, The Lychee Crop in Asia and the Pacific (Menzel, 2002); khuyến cáo của ngành bảo vệ thực vật"
    }
  },

  /** Lá khỏe: không đưa vào thư viện bệnh nhưng dùng để nhận diện nhãn của mô hình */
  healthy_aliases: ["healthy", "la_khoe", "normal", "healthy_leaf"],

  model: {
    name: "ResNet-18 + Grad-CAM",
    arch: "ResNet-18 (PyTorch), tinh chỉnh từ ImageNet",
    input: "224 × 224",
    classes: ["Healthy", "Anthracnose", "Downy_blight", "Leaf_blight", "Algal_spot", "Erinose"],
    explain: "Grad-CAM tại tầng tích chập cuối (layer4)",
    desc: "Phân loại 5 bệnh, dịch hại thường gặp trên lá vải và lá khỏe; bản đồ nhiệt cho biết vùng ảnh mô hình dựa vào."
  },

  handbook: {
    principles: [
      { num: 1, title: "Cây giống sạch bệnh", desc: "Nhân giống từ cây mẹ khỏe, không mang nhện lông nhung; dùng cành chiết, cây ghép có nguồn gốc rõ ràng." },
      { num: 2, title: "Cắt tỉa sau thu hoạch", desc: "Tỉa cành tăm, cành sâu bệnh, cành bị lông nhung ngay sau thu hoạch để tán thông thoáng, đón nắng." },
      { num: 3, title: "Tạo tán, giữ khoảng cách", desc: "Tạo tán gọn, không để tán các cây giao nhau; vườn thoáng giúp lá nhanh khô sau mưa, hạn chế nấm và tảo." },
      { num: 4, title: "Quản lý các đợt lộc", desc: "Nuôi các đợt lộc thu ra đồng loạt, khỏe; hạn chế lộc đông để cây phân hóa mầm hoa thuận lợi." },
      { num: 5, title: "Bón phân cân đối", desc: "Ưu tiên phân hữu cơ hoai mục, cân đối N-P-K, bổ sung kali, canxi, bo; thừa đạm làm lộc non mềm, dễ nhiễm bệnh." },
      { num: 6, title: "Tưới và thoát nước", desc: "Giữ ẩm vừa đủ mùa khô, khơi rãnh thoát nước mùa mưa; tránh tưới phun lên tán vào chiều tối." },
      { num: 7, title: "Vệ sinh vườn", desc: "Thu gom lá, quả rụng và cành bệnh đem tiêu hủy xa vườn; làm sạch cỏ dại quanh gốc." },
      { num: 8, title: "Bảo vệ ong và thiên địch", desc: "Không phun thuốc khi hoa nở rộ; ong mật thụ phấn giúp tăng tỷ lệ đậu quả, thiên địch giữ dịch hại ở mức thấp." }
    ],
    inspection: [
      { step: 1, title: "Quan sát tán theo bốn hướng", desc: "Đi quanh tán vào buổi sáng, quan sát độ đồng đều của đợt lộc, chùm hoa và những chỗ lá đổi màu." },
      { step: 2, title: "Kiểm tra lộc non", desc: "Lộc dài 3–5 cm là lúc nhện lông nhung và thán thư dễ tấn công nhất; kiểm tra kỹ các đợt lộc xuân, lộc thu." },
      { step: 3, title: "Lật mặt dưới lá", desc: "Tìm mảng lông tơ trắng hoặc nâu đỏ (nhện lông nhung) và lớp mốc trắng (sương mai)." },
      { step: 4, title: "Xem chóp và mép lá", desc: "Vết cháy nâu có viền sẫm, chấm đen nhỏ trên vết là dấu hiệu của thán thư hoặc cháy lá." },
      { step: 5, title: "Kiểm tra lá trong tán", desc: "Ở chỗ rậm, ẩm, tìm các đốm tròn đỏ gạch như nhung của bệnh đốm rong trên lá già." },
      { step: 6, title: "Theo dõi thời tiết", desc: "Mưa phùn, nồm ẩm kéo dài là lúc nguy cơ sương mai và thán thư tăng cao, cần thăm vườn dày hơn." },
      { step: 7, title: "Ghi chép và đánh dấu cây", desc: "Buộc dây đánh dấu cây nghi bệnh, chụp ảnh và lưu vào nhật ký LEAF_AI để theo dõi diễn biến." }
    ],
    ipm: [
      { step: 1, title: "Cây khỏe từ gốc", desc: "Cây giống sạch bệnh, chăm sóc phục hồi cây ngay sau thu hoạch." },
      { step: 2, title: "Thăm vườn định kỳ", desc: "Ít nhất 1–2 lần mỗi tuần, dày hơn khi cây ra lộc, ra hoa hoặc gặp đợt mưa ẩm." },
      { step: 3, title: "Bảo vệ thiên địch", desc: "Giữ nhện bắt mồi, ong ký sinh, kiến vàng; không phun thuốc phổ rộng tràn lan." },
      { step: 4, title: "Nhận diện đúng tác nhân", desc: "Dùng LEAF_AI để phân biệt bệnh do nấm, tảo hay nhện hại trước khi chọn biện pháp." },
      { step: 5, title: "Chỉ can thiệp khi vượt ngưỡng", desc: "Không phun định kỳ theo lịch; chỉ xử lý khi tỷ lệ lộc, lá bị hại tăng nhanh." },
      { step: 6, title: "Biện pháp canh tác làm nền", desc: "Tỉa cành, vệ sinh vườn, bón phân cân đối, thoát nước tốt." },
      { step: 7, title: "Biện pháp cơ giới", desc: "Cắt bỏ và tiêu hủy cành lá bị bệnh, bị nhện lông nhung." },
      { step: 8, title: "Ưu tiên biện pháp sinh học", desc: "Trichoderma, Bacillus subtilis, dầu khoáng, chế phẩm thảo mộc." },
      { step: 9, title: "Hóa học là bước cuối cùng", desc: "Chỉ dùng thuốc trong danh mục được phép, đúng 4 đúng, không phun khi hoa nở rộ." },
      { step: 10, title: "Ghi chép và truy xuất", desc: "Lưu nhật ký chẩn đoán và phun thuốc; vải xuất khẩu cần nhật ký canh tác đầy đủ để truy xuất nguồn gốc." }
    ],
    safe_pesticide: [
      { rule: "1. Đúng thuốc", desc: "Xác định đúng tác nhân trước khi mua thuốc: thuốc trừ nấm không trị được nhện lông nhung và ngược lại." },
      { rule: "2. Đúng lúc", desc: "Phun khi bệnh mới chớm hoặc khi lộc non dài 3–5 cm; phun lúc sáng sớm hoặc chiều mát, không phun khi hoa nở rộ." },
      { rule: "3. Đúng liều lượng, nồng độ", desc: "Pha đúng liều ghi trên nhãn; pha đặc gây cháy lộc, pha loãng làm dịch hại nhờn thuốc." },
      { rule: "4. Đúng cách", desc: "Phun ướt đều hai mặt lá, chú ý mặt dưới lá và lộc non; không pha trộn nhiều loại thuốc tùy tiện." },
      { rule: "5. Thời gian cách ly (PHI)", desc: "Ngừng phun trước thu hoạch đúng số ngày ghi trên nhãn; vải xuất khẩu còn phải tuân thủ danh mục hoạt chất và mức dư lượng (MRL) của nước nhập khẩu." },
      { rule: "6. Bảo hộ khi phun", desc: "Mặc quần áo dài, đeo khẩu trang, găng tay, kính; không ăn uống, hút thuốc khi đang pha và phun thuốc." }
    ]
  }
};
