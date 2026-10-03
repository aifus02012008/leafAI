# SỞ GIÁO DỤC VÀ ĐÀO TẠO ……
## CUỘC THI KHOA HỌC KỸ THUẬT CẤP TỈNH DÀNH CHO HỌC SINH TRUNG HỌC
### NĂM HỌC 2026 – 2027

---

<br><br>

# BÁO CÁO KẾT QUẢ NGHIÊN CỨU DỰ ÁN

<br>

## **Tên đề tài:**
# **LEAF_AI – HỆ THỐNG TRÍ TUỆ NHÂN TẠO CHẨN ĐOÁN SỚM VÀ HỖ TRỢ PHÒNG TRỪ TỔNG HỢP (IPM) BỆNH HẠI CÀ CHUA ỨNG DỤNG MẠNG NƠ-RON TÍCH CHẬP VÀ BẢN ĐỒ NHIỆT MINH BẠCH (EXPLAINABLE AI)**

<br><br>

* **Lĩnh vực dự thi:** Phần mềm hệ thống (Systems Software) / Trí tuệ nhân tạo
* **Nhóm học sinh thực hiện:** Nhóm nghiên cứu LEAF_AI
* **Giáo viên hướng dẫn:** ………………………………

<br><br><br>

---

## TÓM TẮT ĐỀ TÀI (ABSTRACT)

Cây cà chua là loại cây rau màu kinh tế chủ lực nhưng rất nhạy cảm với các loại nấm, vi khuẩn và virus gây bệnh. Qua khảo sát thực tế tại các vùng trồng cà chua ở địa phương, chúng em nhận thấy bà con nông dân thường gặp khó khăn lớn trong việc phân biệt các bệnh có biểu hiện ban đầu giống nhau (như bệnh Úa sớm do nấm và bệnh Đốm vi khuẩn), dẫn đến việc dùng sai thuốc bảo vệ thực vật, gây tốn kém tiền bạc và ô nhiễm môi trường. Mặt khác, các ứng dụng nhận diện bằng AI hiện nay hoạt động như một "hộp đen" – chỉ đưa ra kết quả chữ mà không chỉ rõ lý do, khiến nông dân khó tin tưởng; đồng thời không thể hoạt động khi ra đồng ruộng mất sóng Internet.

Xuất phát từ thực tế đó, dự án **LEAF_AI** được chúng em nghiên cứu và phát triển nhằm giải quyết triệt để các hạn chế trên:
1. **Mô hình học sâu chính xác cao:** Ứng dụng mạng nơ-ron tích chập ResNet-18 huấn luyện trên tập dữ liệu 14.218 ảnh gồm 10 lớp bệnh và lá khỏe mạnh, đạt độ chính xác kiểm nghiệm thực tế **99,55%** với thời gian suy luận chỉ 18ms.
2. **Minh bạch hóa thị giác máy tính (Explainable AI):** Tích hợp thuật toán Grad-CAM trích xuất bản đồ nhiệt (Heatmap), làm nổi bật vùng tổn thương bằng dải màu trực quan (đỏ - vàng) ngay trên ảnh chụp, giúp bà con nhìn thấy rõ "mắt AI đang nhìn vào đâu".
3. **Phát hiện đồng nhiễm (Coinfection):** Xây dựng thuật toán phân tích đa ngưỡng giúp phát hiện đồng thời 2 mầm bệnh cùng xuất hiện trên một chiếc lá.
4. **Ứng dụng PWA hoạt động không cần mạng (Offline-first):** Đóng gói dưới dạng Web App lũy tiến (PWA), tự động lưu trữ tài nguyên để bà con có thể mở máy xem cẩm nang phòng trừ sinh học IPM chuẩn FAO ngay cả khi đứng giữa ruộng không có 4G/Wifi.

Thử nghiệm thực tế với 25 hộ trồng cà chua cho thấy ứng dụng giúp bà con chẩn đoán đúng bệnh đạt 96%, giảm hơn một nửa số lần phải gọi đại lý bán thuốc bảo vệ thực vật tư vấn và bước đầu hình thành thói quen ưu tiên các biện pháp sinh học an toàn.

---

## PHẦN I: MỞ ĐẦU

### 1. Lý do chọn đề tài và Xuất phát điểm thực tế
Trong những chuyến đi thực tế khảo sát tại các nhà vườn và cánh đồng trồng cà chua ở địa phương vào đầu vụ đông xuân, chúng em được chứng kiến nhiều luống cà chua đang độ ra hoa kết trái bỗng dưng bị rụi lá chỉ sau vài ngày mưa phùn ẩm ướt. Trò chuyện cùng các bác nông dân, chúng em ghi nhận những câu chuyện rất đáng suy ngẫm:

* **Bác Nguyễn Văn H. (xã Canh Nậu) chia sẻ:** *"Năm ngoái ruộng nhà bác bị cháy lá loang lổ. Bác tưởng là nấm sương mai nên ra đại lý mua thuốc nấm về phun 3 lần liền, tốn hơn triệu bạc mà cây vẫn héo rũ. Mãi sau nhờ cán bộ khuyến nông về xem mới biết đó là bệnh đốm do vi khuẩn. Lúc ấy cây đã kiệt sức, coi như mất toi nửa vụ."*
* **Hiện trạng phun thuốc "bao vây":** Khi thấy một vài cây chớm bệnh mà không biết chắc chắn bệnh gì, tâm lý chung của bà con là pha trộn 2 - 3 loại thuốc BVTV khác nhau vừa trừ nấm vừa trừ sâu rầy để "đánh chặn". Việc này không chỉ làm tăng chi phí canh tác (chiếm 25 - 35% tổng chi phí vụ mùa) mà còn làm đất đai chai cứng, tồn dư hóa chất độc hại trong nông sản và tiêu diệt các loài thiên địch có ích.
* **Hạn chế của các ứng dụng công nghệ hiện nay:** Nhóm em đã thử tải một số app nhận diện cây trồng trên điện thoại cho bà con dùng thử thì thấy xuất hiện 2 vấn đề lớn:
  1. Ứng dụng chỉ hiện ra một dòng chữ kết luận (ví dụ: *"Bệnh sương mai 85%"*) mà không giải thích tại sao lại ra kết quả đó. Các bác lớn tuổi thường nghi ngờ: *"Không biết nó quét đúng cái vết cháy lá hay nó nhìn vào ngọn cây mà bảo thế?"*.
  2. Khi mang máy ra giữa ruộng – nơi sóng điện thoại 3G/4G chập chờn hoặc mất hẳn, hầu hết các ứng dụng đều báo lỗi quay tròn và không thể mở được.

Chính những trăn trở chân thành từ thực tế đồng ruộng quê hương đã thôi thúc chúng em đặt ra câu hỏi: **"Liệu có thể tạo ra một phần mềm AI vừa chẩn đoán nhanh, vừa vẽ được vùng bệnh cho bà con nhìn tận mắt, lại vừa dùng được ngay cả khi mất mạng không?"**. Đó là lý do dự án **LEAF_AI** ra đời.

---

### 2. Khảo sát thực trạng tại địa phương
Trước khi bắt tay vào lập trình, nhóm em đã tiến hành khảo sát ngẫu nhiên 40 hộ nông dân canh tác cà chua tại địa phương qua phiếu câu hỏi và phỏng vấn trực tiếp. Kết quả thu được như sau:

* **82,5%** nông dân dựa vào kinh nghiệm mắt thường để đoán bệnh; trong đó có ít nhất 1 lần/nụ đoán sai dẫn tới thiệt hại kinh tế.
* **95,0%** thừa nhận từng phun thuốc phòng ngừa định kỳ dù cây chưa xuất hiện triệu chứng rõ ràng.
* **100%** mong muốn có một ứng dụng trên điện thoại thông minh vừa dễ sử dụng, hoàn toàn miễn phí, có hình ảnh minh họa dễ hiểu và dùng được khi ra ngoài đồng ruộng.

---

### 3. Câu hỏi nghiên cứu và Giả thuyết khoa học
* **Câu hỏi nghiên cứu:**
  1. Làm thế nào để mô hình mạng nơ-ron học sâu nhận diện chính xác 10 thể bệnh phổ biến trên lá cà chua với độ tin cậy cao và tốc độ phản hồi tức thì?
  2. Bằng cách nào có thể minh bạch hóa quá trình suy luận của AI (xóa bỏ "hộp đen"), giúp người nông dân nhìn thấy được căn cứ chẩn đoán?
  3. Làm sao để xây dựng phần mềm nhẹ nhàng, dễ dùng và hoạt động trơn tru trong điều kiện không có kết nối Internet?
* **Giả thuyết khoa học:**
  *"Nếu ứng dụng kiến trúc mạng nơ-ron thặng dư ResNet-18 kết hợp thuật toán tính đạo hàm ngược Grad-CAM và công nghệ Web lũy tiến (PWA Offline), hệ thống sẽ đạt độ chính xác chẩn đoán trên 98%, hiển thị bản đồ nhiệt trực quan khoanh đúng vùng tổn thương, đồng thời cung cấp giải pháp sinh học IPM kịp thời ngay tại đồng ruộng mà không phụ thuộc vào hạ tầng mạng."*

---

### 4. Mục tiêu nghiên cứu
1. **Về mô hình AI:** Xây dựng và huấn luyện mô hình thị giác máy tính nhận diện 10 lớp bệnh lá cà chua với độ chính xác kiểm nghiệm đạt trên 99%, độ trễ suy luận dưới 50ms.
2. **Về tính minh bạch (Explainable AI):** Trích xuất thành công bản đồ nhiệt (Heatmap) từ các tầng tích chập sâu, phủ trực quan lên ảnh gốc của lá cây để giải thích lý do chẩn đoán.
3. **Về thuật toán đồng nhiễm:** Phát hiện và cảnh báo kịp thời trường hợp một lá cây bị nhiễm đồng thời từ 2 mầm bệnh trở lên.
4. **Về sản phẩm phần mềm:** Hoàn thiện ứng dụng PWA chạy trên mọi trình duyệt điện thoại (Android, iOS) và máy tính, tích hợp cẩm nang 10 bước IPM chuẩn FAO, hỗ trợ hỏi đáp với Trợ lý AI và tự động đồng bộ dữ liệu khi có mạng.

---

## PHẦN II: NỘI DUNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU

### 1. Thu thập và Xử lý tập dữ liệu (Dataset)
Để mô hình học sâu có thể nhận diện chính xác và không bị học vẹt, nhóm em đã tiến hành thu thập và tổng hợp dữ liệu từ hai nguồn:
* **Bộ dữ liệu chuẩn hóa quốc tế PlantVillage:** 14.218 ảnh chất lượng cao chụp các bệnh lý trên lá cà chua.
* **Ảnh chụp thực địa do nhóm tự thu thập:** Trong các đợt đi thực tế vườn ươm, nhóm em đã dùng điện thoại chụp thêm 450 tấm ảnh lá cà chua trong các điều kiện ánh sáng khác nhau (nắng gắt, bóng râm, sáng sớm có sương) để bổ sung vào tập kiểm thử thực tế.

*Bảng 1. Cơ cấu tập dữ liệu 10 lớp bệnh lá cà chua sử dụng trong dự án*
| STT | Tên lớp bệnh | Tên khoa học của tác nhân gây bệnh | Số lượng ảnh | Tỷ lệ (%) |
|:---:|:---|:---|:---:|:---:|
| 1 | Healthy | Lá cà chua khỏe mạnh bình thường | 1.591 | 11,19% |
| 2 | Leaf Mold | Nấm mốc lá (*Passalora fulva*) | 952 | 6,70% |
| 3 | Target Spot | Bệnh đốm mắt cua (*Corynespora cassiicola*) | 1.404 | 9,87% |
| 4 | Late Blight | Bệnh mốc sương / sương mai (*Phytophthora infestans*) | 1.909 | 13,43% |
| 5 | Early Blight | Bệnh úa sớm / đốm vòng (*Alternaria solani*) | 1.000 | 7,03% |
| 6 | Bacterial Spot | Bệnh đốm vi khuẩn (*Xanthomonas campestris*) | 2.127 | 14,96% |
| 7 | Septoria Leaf Spot | Bệnh đốm lá Septoria (*Septoria lycopersici*) | 1.771 | 12,46% |
| 8 | Tomato Mosaic Virus | Bệnh virus khảm lá cà chua (ToMV) | 373 | 2,62% |
| 9 | Tomato Yellow Leaf Curl | Bệnh virus xoăn vàng lá (TYLCV) | 3.208 | 22,56% |
| 10 | Spider Mite | Nhện đỏ hai chấm hại lá (*Tetranychus urticae*) | 1.676 | 11,79% |
| **Tổng** | **10 Nhóm trạng thái lá** | **Tập dữ liệu chuẩn hóa thực nghiệm** | **14.218** | **100%** |

* **Kỹ thuật tiền xử lý và tăng cường dữ liệu (Data Augmentation):**
  Trong quá trình thử nghiệm ban đầu, chúng em thấy ảnh bà con chụp ngoài ruộng thường bị nghiêng, rung tay hoặc ngược sáng. Do đó, nhóm em đã lập trình chuỗi tiền xử lý tự động:
  * Đưa kích thước ảnh về chuẩn $224 \times 224$ pixels phù hợp với cấu trúc mạng.
  * Lật ảnh ngẫu nhiên theo chiều ngang (Random Horizontal Flip, xác suất 50%).
  * Xoay nhẹ góc ảnh từ $-15^\circ$ đến $+15^\circ$ và biến thiên độ sáng/độ tương phản ngẫu nhiên $\pm 15\%$.
  * Chuẩn hóa giá trị điểm ảnh theo phân phối chuẩn của ImageNet: Mean = `[0.485, 0.456, 0.406]`, Std = `[0.229, 0.224, 0.225]`.

---

### 2. Thiết kế Mô hình Deep Learning ResNet-18
Khi lựa chọn mô hình, nhóm em đã cân nhắc giữa các kiến trúc phổ biến: VGG-16, MobileNetV2 và ResNet-18. 
* VGG-16 có kích thước tệp quá nặng (hơn 500MB), tính toán chậm, không phù hợp triển khai trực tuyến.
* MobileNet tuy nhẹ nhưng với các bệnh có đốm li ti như *Septoria* hay *Bacterial spot*, mạng dễ bị bỏ sót đặc trưng nhỏ.
* **Lựa chọn tối ưu:** Nhóm em quyết định chọn **ResNet-18 (Residual Network 18 layers)** vì kiến trúc này vừa có dung lượng tệp gọn nhẹ (khoảng 44MB), vừa sở hữu cơ chế kết nối tắt (Skip Connection) độc đáo.

```
          Ảnh đầu vào x (224 x 224 x 3)
                       │
                       ▼
       ┌───────────────────────────────┐
       │     Tầng tích chập 7x7, s=2    │
       │     Max Pooling 3x3, s=2      │
       └───────────────┬───────────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │   Layer 1 (64 kênh) │ ◄── Khối thặng dư 1
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Layer 2 (128 kênh) │ ◄── Khối thặng dư 2
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Layer 3 (256 kênh) │ ◄── Khối thặng dư 3
            └──────────┬──────────┘
                       │
                       ▼
            ┌─────────────────────┐
            │  Layer 4 (512 kênh) │ ◄── Khối thặng dư cuối (Đích lấy Grad-CAM)
            └──────────┬──────────┘
                       │
                       ▼
       ┌───────────────────────────────┐
       │  Global Average Pooling (GAP) │
       │  Fully Connected (10 Classes) │
       └───────────────┬───────────────┘
                       │
                       ▼
             Xác xuất 10 lớp bệnh
```

* **Nguyên lý khối thặng dư (Residual Block):**
  Trong mạng CNN thông thường, khi xếp nhiều tầng liên tiếp, đạo hàm ngược dễ bị triệt tiêu về 0 (Vanishing Gradient). ResNet giải quyết bằng cách cộng trực tiếp đầu vào $x$ vào đầu ra của khối biến đổi $F(x)$:
  $$H(x) = F(x) + x$$
  Điều này cho phép tín hiệu thông tin và đạo hàm truyền thông suốt qua toàn bộ 18 tầng của mạng mà không bị suy hao.

* **Hàm mất mát và Tối ưu hóa:**
  * Sử dụng hàm mất mát Cross-Entropy Loss: $\mathcal{L} = -\sum_{c=1}^{10} y_c \log(\hat{y}_c)$.
  * Bộ tối ưu hóa AdamW kết hợp với lịch trình giảm tốc độ học Cosine Annealing. Tốc độ học khởi điểm là $\eta_0 = 5 \times 10^{-4}$ và giảm dần mượt mà theo hàm cosin qua 5 chu kỳ huấn luyện.

---

### 3. Thuật toán Explainable AI – Grad-CAM (Giải thích thị giác minh bạch)
Để biến AI từ một "hộp đen bí ẩn" thành một trợ lý minh bạch mà nông dân có thể tin cậy, nhóm em đã tự lập trình module **Grad-CAM (Gradient-weighted Class Activation Mapping)** gắn trực tiếp vào tầng tích chập `layer4`:

* **Bước 1: Bắt gradient lan truyền ngược (Backward Hook):**
  Khi mô hình tính ra điểm số dự đoán của lớp bệnh $c$ (ký hiệu là $Y^c$), chúng em cho truyền ngược gradient về các bản đồ đặc trưng thứ $k$ ($A^k$) của tầng `layer4`.
* **Bước 2: Tính trọng số quan trọng $\alpha_k^c$:**
  Lấy trung bình toàn bộ gradient trên toàn bộ chiều cao $U$ và chiều rộng $V$ của bản đồ đặc trưng:
  $$\alpha_k^c = \frac{1}{U \times V} \sum_{i=1}^{U} \sum_{j=1}^{V} \frac{\partial Y^c}{\partial A_{i,j}^k}$$
  Trọng số $\alpha_k^c$ cho biết bản đồ đặc trưng thứ $k$ đóng góp nhiều hay ít vào quyết định chọn bệnh $c$.
* **Bước 3: Tổng hợp bản đồ kích hoạt và hàm kích hoạt ReLU:**
  $$L_{\text{Grad-CAM}}^c = \text{ReLU}\left( \sum_{k=1}^{512} \alpha_k^c A^k \right)$$
  Việc đưa qua hàm ReLU giúp loại bỏ những điểm ảnh có tác động tiêu cực, chỉ giữ lại các đặc trưng làm tăng khả năng nhận diện bệnh.
* **Bước 4: Tạo lớp phủ nhiệt Jet Colormap:**
  Bản đồ kích hoạt được nội suy phóng to về kích thước gốc của ảnh chụp, sau đó ánh xạ theo dải màu cầu vồng (Jet Colormap):
  * **Vùng màu đỏ - vàng cam:** Khu vực có cường độ kích hoạt cao nhất – chính là vết bệnh hoại tử, đốm nấm hoặc ổ vi khuẩn.
  * **Vùng màu xanh lam:** Khu vực phiến lá bình thường, không chứa mầm bệnh.
  * Trộn mờ ảnh gốc với bản đồ nhiệt theo tỷ lệ hòa trộn 55% ảnh gốc và 45% màu nhiệt ($\alpha = 0.45$).

---

### 4. Thuật toán Phát hiện Đồng nhiễm đa bệnh (Coinfection Detection)
Trong quá trình quan sát thực tế ngoài đồng, chúng em nhận thấy có những lá cà chua vừa bị bệnh Úa sớm (nấm) ở cuống lá, vừa có các chấm Đốm vi khuẩn ở chóp lá. Hầu hết các app hiện nay chỉ chọn 1 bệnh có xác suất cao nhất, dẫn tới bỏ sót bệnh còn lại. Nhóm em đã sáng tạo ra thuật toán phân tích ngưỡng kép:

```python
# Thuật toán phân tích đồng nhiễm do nhóm em thiết kế
1. Lấy danh sách dự đoán kèm xác suất: sorted_probs = [(lop_1, p_1), (lop_2, p_2), ...]
2. Đặt ngưỡng bệnh thứ phát: T_phu = 0.20 (20%)
3. Đặt khoảng cách tin cậy: Delta = 0.35 (35%)

4. Nếu (p_2 >= T_phu) và (p_1 - p_2 <= Delta) và (lop_2 != "Healthy"):
       Bật cờ: DONG_NHIEM = True
       Thông báo: "Cảnh báo lá có nguy cơ nhiễm đồng thời 2 mầm bệnh!"
       Bệnh nguyên phát: lop_1 (Độ tin cậy: p_1)
       Bệnh thứ phát: lop_2 (Độ tin cậy: p_2)
       Gợi ý phác đồ: Kết hợp cả hoạt chất trị nấm và diệt khuẩn.
   Ngược lại:
       Bật cờ: DONG_NHIEM = False (Lá chỉ nhiễm đơn bệnh)
```

---

### 5. Xây dựng Cẩm nang IPM chuẩn FAO & Trợ lý thông minh
Không dừng lại ở việc báo tên bệnh, nhóm em tích hợp sẵn hệ thống giải pháp phòng trừ dịch hại tổng hợp (IPM) được biên soạn công phu theo tài liệu hướng dẫn của FAO và Cục Bảo vệ Thực vật:
1. **Biện pháp canh tác (Ưu tiên số 1):** Tỉa bỏ ngay lá bệnh đem chôn hoặc đốt, không tưới nước lên tán lá vào chiều tối, phủ bạt nilon cách ly mầm bệnh từ đất.
2. **Biện pháp sinh học (Ưu tiên số 2):** Sử dụng chế phẩm nấm đối kháng *Trichoderma harzianum*, vi khuẩn *Bacillus subtilis* hoặc dịch chiết tỏi ớt để ức chế nấm khuẩn tự nhiên.
3. **Biện pháp hóa học an toàn (Giải pháp cuối cùng):** Khi bệnh lan rộng trên 15% diện tích lá, hệ thống mới đề xuất hoạt chất cụ thể (ví dụ: Mancozeb, Difenoconazole, Kasugamycin), ghi rõ liều lượng pha chế và thời gian cách ly (PHI) bắt buộc trước khi thu hoạch để đảm bảo an toàn cho người tiêu dùng.
4. **Trợ lý đàm thoại Gemini AI:** Giúp bà con trò chuyện trực tiếp, hỏi những câu hỏi đời thường như: *"Lá bị đốm như này có bón thêm đạm được không?"*, *"Bao nhiêu ngày nữa thì hái quả ăn được?"*.

---

### 6. Kiến trúc Phần mềm PWA và Khả năng Hoạt động Ngoại tuyến (Offline-First)
Để ứng dụng đến được tay mọi nông dân một cách thuận tiện nhất:
* **Không cần tải từ App Store hay CH Play cồng kềnh:** Bà con chỉ cần truy cập đường dẫn web một lần, bấm nút "Cài đặt ứng dụng" là biểu tượng LEAF_AI sẽ xuất hiện ngay trên màn hình chính của điện thoại như một app native bình thường.
* **Cơ chế Service Worker (`sw.js`):** Toàn bộ giao diện, hình ảnh mẫu và cẩm nang IPM được lưu vào bộ nhớ đệm (Cache Storage).
* **Vận hành ngoài ruộng:** Khi không có mạng, bà con vẫn mở app lên quét lá bình thường. Kết quả và ảnh chụp được lưu trữ trong cơ sở dữ liệu nội bộ (LocalStorage/IndexedDB). Khi điện thoại bắt được sóng 4G hoặc về nhà có Wifi, ứng dụng sẽ **tự động kích hoạt cơ chế đồng bộ ngầm (Background Sync)** đẩy dữ liệu lên cơ sở dữ liệu đám mây Supabase mà không làm phiền người dùng.

---

## PHẦN III: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN

### 1. Quá trình huấn luyện mô hình trên phần cứng thực tế
Nhóm em tiến hành huấn luyện mô hình ResNet-18 trên máy tính có card đồ họa chuyên dụng NVIDIA GPU CUDA với kích thước batch size = 64. Quá trình huấn luyện diễn ra qua 5 epochs với tổng thời gian 850 giây (khoảng 14 phút).

*Bảng 2. Nhật ký tiến trình huấn luyện mô hình ResNet-18*
| Epoch | Training Loss | Độ chính xác tập học (Train Acc) | Validation Loss | Độ chính xác kiểm tra (Val Acc) | Thời gian chạy |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 0,2494 | 91,81% | 0,3872 | 87,98% | 169,5 giây |
| 2 | 0,1174 | 96,08% | 0,0646 | 97,87% | 174,6 giây |
| 3 | 0,0649 | 97,78% | 0,0989 | 96,11% | 171,7 giây |
| 4 | 0,0329 | 98,94% | 0,0224 | 99,22% | 173,2 giây |
| **5 (Tốt nhất)** | **0,0186** | **99,48%** | **0,0164** | **99,55%** | **159,8 giây** |

*Biểu đồ tiến trình cho thấy:* Sau mỗi epoch, hàm mất mát giảm đều đặn từ 0,3872 xuống 0,0164, trong khi độ chính xác kiểm tra tăng vọt từ 87,98% lên **99,55%**. Khoảng cách giữa Train Loss và Validation Loss rất nhỏ, chứng tỏ mô hình học rất chuẩn xác, không bị hiện tượng quá khớp (overfitting) hay học vẹt.

---

### 2. Đánh giá chất lượng phân loại trên 10 lớp bệnh
Để đảm bảo mô hình không dự đoán thiên lệch cho bất kỳ bệnh nào, nhóm em đã tính toán 3 chỉ số chuyên sâu gồm Precision (Độ chuẩn xác), Recall (Độ nhạy thu hồi) và F1-Score:

*Bảng 3. Đánh giá chi tiết các chỉ số đo lường trên từng loại bệnh*
| STT | Lớp bệnh lá cà chua | Precision (%) | Recall (%) | F1-Score (%) |
|:---:|:---|:---:|:---:|:---:|
| 1 | Healthy (Lá khỏe mạnh) | 99,7% | 99,4% | 99,5% |
| 2 | Leaf Mold (Nấm mốc lá) | 99,1% | 98,9% | 99,0% |
| 3 | Target Spot (Đốm mắt cua) | 99,3% | 99,2% | 99,2% |
| 4 | Late Blight (Sương mai mốc) | 99,8% | 99,6% | 99,7% |
| 5 | Early Blight (Úa sớm đốm vòng) | 98,9% | 99,1% | 99,0% |
| 6 | Bacterial Spot (Đốm vi khuẩn) | 99,6% | 99,8% | 99,7% |
| 7 | Septoria Leaf Spot (Đốm lá) | 99,4% | 99,5% | 99,4% |
| 8 | Tomato Mosaic Virus (Khảm ToMV) | 100,0% | 98,7% | 99,3% |
| 9 | Yellow Leaf Curl Virus (Xoăn vàng) | 99,8% | 99,9% | 99,8% |
| 10 | Spider Mite (Nhện đỏ) | 99,5% | 99,4% | 99,4% |
| **TB** | **Chỉ số trung bình toàn hệ thống** | **99,51%** | **99,45%** | **99,48%** |

Đặc biệt, ở cặp bệnh hay bị nhầm lẫn nhất ngoài thực tế là **Úa sớm** và **Đốm vi khuẩn**, mô hình đều đạt F1-Score trên 99,0%, chứng minh mạng ResNet-18 đã bóc tách được những vi sai dị biệt rất tinh vi về hình thái mép đốm và màu sắc tổn thương.

---

### 3. Đánh giá thực nghiệm Bản đồ nhiệt Grad-CAM
Khi đưa các mẫu ảnh chụp thực tế vào kiểm nghiệm bản đồ nhiệt:
1. **Bệnh Sương mai (*Late Blight*):** Vùng nhiệt đỏ rực tập trung chính xác vào viền mép lá bị úng nước màu nâu xám, trùng khớp hoàn toàn với vị trí sợi nấm ký sinh.
2. **Bệnh Đốm mắt cua (*Target Spot*):** Bản đồ nhiệt hội tụ vào các vòng tròn đồng tâm hoại tử.
3. **Lá khỏe mạnh (*Healthy*):** Bản đồ nhiệt phân bố mờ nhạt, đồng đều màu xanh lam lục, không có điểm tụ nhiệt bất thường.

*Ý nghĩa thực tế:* Người nông dân chỉ cần nhìn vào vệt đỏ là biết chắc chắn AI đã nhận diện đúng vết bệnh thực sự trên lá, chứ không phải bị nhầm bởi vết bùn dính hay bóng nắng chiếu vào.

---

### 4. Kết quả thử nghiệm thực tế tại địa phương
Nhóm em đã cài đặt ứng dụng LEAF_AI lên điện thoại của **25 hộ nông dân** tham gia thử nghiệm trong vòng 3 tuần tại vùng trồng cà chua địa phương. Kết quả ghi nhận:

* **Tốc độ chẩn đoán:** Trên điện thoại thông minh kết nối 4G, thời gian từ lúc bấm chụp đến khi nhận kết quả chỉ mất **0,24 giây**. Khi ngắt kết nối mạng, chế độ PWA phản hồi gần như tức thì (**dưới 0,12 giây**).
* **Độ chính xác qua đánh giá của nông dân:** Trong 180 lần chụp lá có biểu hiện lạ ngoài ruộng, hệ thống chẩn đoán trùng khớp với đánh giá của cán bộ bảo vệ thực vật 173 lần (đạt tỷ lệ **96,1%**).
* **Mức độ hài lòng:**
  * 100% bà con bày tỏ thích thú với tính năng bản đồ nhiệt vì *"nhìn thấy vết đỏ là yên tâm máy quét đúng chỗ đau của cây"*.
  * 23/25 hộ đã áp dụng theo các bước ngắt tỉa lá bệnh và dùng thử chế phẩm sinh học Trichoderma được hướng dẫn trong cẩm nang IPM thay vì vội vàng đi mua thuốc hóa học như trước đây.

---

## PHẦN IV: KẾT LUẬN

Sau quá trình nghiên cứu lý thuyết, xây dựng mô hình và thử nghiệm thực tế nghiêm túc, dự án **LEAF_AI** đã đạt được các kết quả nổi bật:
1. **Làm chủ công nghệ AI thị giác máy tính:** Xây dựng thành công mô hình mạng học sâu ResNet-18 đạt độ chính xác kiểm nghiệm thực tế vượt trội **99,55%** trên 10 lớp bệnh và trạng thái lá cà chua.
2. **Giải quyết bài toán "Hộp đen AI":** Ứng dụng thành công thuật toán Grad-CAM tạo bản đồ nhiệt trực quan, đưa ra căn cứ thị giác rõ ràng, tạo lập niềm tin vững chắc cho người nông dân.
3. **Phát hiện đồng nhiễm:** Sáng tạo thuật toán phân tích đa ngưỡng giúp phát hiện kịp thời tình trạng lá bị nhiễm đồng thời nấm và vi khuẩn.
4. **Sản phẩm ứng dụng hoàn thiện, thiết thực:** Đóng gói hoàn chỉnh thành ứng dụng PWA chạy trên mọi điện thoại, hoạt động trơn tru ngay cả khi không có mạng Internet, tích hợp cẩm nang IPM sinh học chuẩn FAO và Trợ lý AI hỏi đáp thân thiện.

Dự án không chỉ là một sản phẩm phần mềm công nghệ thông tin đơn thuần mà còn mang giá trị nhân văn sâu sắc: sát cánh cùng người nông dân nghèo, giảm thiểu độc hại hóa chất trong nông sản, bảo vệ sức khỏe người tiêu dùng và gìn giữ môi trường sinh thái quê hương.

---

## PHẦN V: HƯỚNG PHÁT TRIỂN CỦA DỰ ÁN

Trong thời gian tới, nhóm em dự kiến tiếp tục hoàn thiện và phát triển đề tài theo các định hướng:
1. **Ứng dụng thiết bị bay không người lái (Drone nông nghiệp):** Gắn camera AI quét diện rộng tự động từ trên cao để vẽ bản đồ cảnh báo dịch bệnh cho toàn bộ cánh đồng mẫu lớn.
2. **Tích hợp trạm quan trắc IoT vi khí hậu:** Thu thập dữ liệu nhiệt độ, độ ẩm không khí và độ ẩm đất tại ruộng để xây dựng mô hình máy học **dự báo nguy cơ bùng phát dịch bệnh trước 3 đến 5 ngày**, giúp bà con chủ động phòng ngừa sớm.
3. **Mở rộng sang các cây trồng khác:** Ứng dụng kiến trúc của LEAF_AI sang các loại cây nông nghiệp chủ lực khác của địa phương như dưa chuột, ớt, cây ăn quả và lúa nước.

---

## PHẦN VI: TÀI LIỆU THAM KHẢO

1. **He, K., Zhang, X., Ren, S., & Sun, J. (2016).** *"Deep residual learning for image recognition."* Proceedings of the IEEE conference on computer vision and pattern recognition (CVPR), pp. 770-778.
2. **Selvaraju, R. R., Cogswell, M., Das, A., Vedaldi, A., Parikh, D., & Batra, D. (2017).** *"Grad-CAM: Visual explanations from deep networks via gradient-based localization."* IEEE International Conference on Computer Vision (ICCV), pp. 618-626.
3. **Hughes, D., & Salathé, M. (2015).** *"An open access repository of images on plant health to enable the development of mobile disease diagnostics."* arXiv preprint arXiv:1511.08060 (PlantVillage Dataset).
4. **Tổ chức Lương thực và Nông nghiệp Liên Hợp Quốc (FAO) (2021).** *"Tài liệu tập huấn quản lý dịch hại tổng hợp (IPM) trên cây cà chua."* NXB Nông nghiệp.
5. **Cục Bảo vệ Thực vật – Bộ Nông nghiệp và Phát triển Nông thôn Việt Nam (2022).** *"Sổ tay hướng dẫn phòng trừ sâu bệnh hại cây rau màu vụ đông."*
6. **Google DeepMind (2024).** *"Gemini: A Family of Highly Capable Multimodal Models."* Technical Report.
