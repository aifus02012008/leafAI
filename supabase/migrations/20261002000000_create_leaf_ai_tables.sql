-- =============================================================================
-- LEAF_AI — SUPABASE DATABASE SCHEMA MIGRATION
-- Nền tảng chẩn đoán bệnh cây trồng (Cà chua) — Chuẩn hóa theo thiết kế Poster
-- Bao gồm: Lịch sử chẩn đoán, Thư viện 6 bệnh cà chua, Cẩm nang chăm sóc IPM FAO
-- =============================================================================

-- Bật extension UUID tự sinh nếu chưa có
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. BẢNG: LỊCH SỬ CHẨN ĐOÁN LÁ CÂY (LEAF DIAGNOSES)
CREATE TABLE IF NOT EXISTS public.leaf_diagnoses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    local_id BIGINT,
    model_version VARCHAR(20) DEFAULT 'v3',
    plant_type VARCHAR(50) DEFAULT 'tomato',
    primary_disease VARCHAR(100) NOT NULL,
    primary_disease_vi VARCHAR(150) NOT NULL,
    confidence NUMERIC(5, 2) DEFAULT 0.0,
    severity VARCHAR(50) DEFAULT 'Nghiêm trọng',
    is_coinfection BOOLEAN DEFAULT FALSE,
    secondary_diseases JSONB DEFAULT '[]'::jsonb,
    detections JSONB DEFAULT '[]'::jsonb,
    treatment_summary TEXT DEFAULT '',
    image_url TEXT,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Chỉ mục tối ưu tốc độ tìm kiếm
CREATE INDEX IF NOT EXISTS idx_leaf_diagnoses_created_at ON public.leaf_diagnoses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leaf_diagnoses_primary ON public.leaf_diagnoses(primary_disease);
CREATE INDEX IF NOT EXISTS idx_leaf_diagnoses_coinfection ON public.leaf_diagnoses(is_coinfection);

-- 2. BẢNG: THƯ VIỆN BỆNH CÂY TRỒNG (TOMATO DISEASES - 6 BỆNH POSTER)
CREATE TABLE IF NOT EXISTS public.tomato_diseases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    disease_id VARCHAR(50) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_vi VARCHAR(150) NOT NULL,
    pathogen VARCHAR(200) NOT NULL,
    color VARCHAR(20) DEFAULT '#ea580c',
    severity_default VARCHAR(50) DEFAULT 'Nghiêm trọng',
    confidence_default NUMERIC(5, 2) DEFAULT 50.0,
    symptoms_stage1 TEXT DEFAULT '',
    symptoms_stage2 TEXT DEFAULT '',
    symptoms_stage3 TEXT DEFAULT '',
    conditions TEXT DEFAULT '',
    prevention TEXT DEFAULT '',
    treatment_cultural TEXT DEFAULT '',
    treatment_bio TEXT DEFAULT '',
    treatment_chemical TEXT DEFAULT '',
    references TEXT DEFAULT '',
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- 3. BẢNG: CẨM NANG CHĂM SÓC & QUẢN LÝ DỊCH HẠI IPM (FAO)
CREATE TABLE IF NOT EXISTS public.ipm_handbook (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    section VARCHAR(30) NOT NULL, -- 'principles', 'inspection', 'ipm', 'safe'
    step_num INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_ipm_handbook_section ON public.ipm_handbook(section, step_num);

-- =============================================================================
-- CẤU HÌNH ROW LEVEL SECURITY (RLS) CHO SUPABASE
-- Cho phép đọc & ghi ẩn danh an toàn từ Web/Mobile Client & Backend
-- =============================================================================

ALTER TABLE public.leaf_diagnoses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tomato_diseases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ipm_handbook ENABLE ROW LEVEL SECURITY;

-- Policy: Cho phép mọi người đọc dữ liệu thư viện & cẩm nang
CREATE POLICY "Public read tomato_diseases" ON public.tomato_diseases
    FOR SELECT USING (true);

CREATE POLICY "Public read ipm_handbook" ON public.ipm_handbook
    FOR SELECT USING (true);

-- Policy: Cho phép thêm và đọc lịch sử chẩn đoán
CREATE POLICY "Public insert leaf_diagnoses" ON public.leaf_diagnoses
    FOR INSERT WITH CHECK (true);

CREATE POLICY "Public read leaf_diagnoses" ON public.leaf_diagnoses
    FOR SELECT USING (true);

CREATE POLICY "Public delete leaf_diagnoses" ON public.leaf_diagnoses
    FOR DELETE USING (true);

-- =============================================================================
-- SEED DATA 6 BỆNH CÀ CHUA CHUẨN POSTER LEAF_AI
-- =============================================================================

INSERT INTO public.tomato_diseases (disease_id, name_en, name_vi, pathogen, color, severity_default, confidence_default, symptoms_stage1, symptoms_stage2, symptoms_stage3, conditions, prevention, treatment_cultural, treatment_bio, treatment_chemical, references)
VALUES 
(
    'bacterial_spot', 
    'Bacterial Spot', 
    'Đốm vi khuẩn', 
    'Xanthomonas campestris pv. vesicatoria', 
    '#ef4444', 
    'Trung bình', 
    42.0, 
    'Các đốm nhỏ 1-2mm úng nước trên lá bánh tẻ và già, mép đốm có quầng vàng nhạt trong suốt.',
    'Vết bệnh mở rộng sẫm màu nâu đen, tâm hoại tử hơi lõm, bề mặt ráp sần sùi.',
    'Nhiều đốm liên kết làm rách phiến lá, lá vàng khô giòn và rụng sớm từ gốc lên ngọn.',
    'Nhiệt độ ấm 24-30°C, ẩm độ cao >85%, giọt bắn mưa lớn hoặc tưới phun mưa đọng nước.',
    'Sử dụng hạt giống đã xử lý nhiệt/hóa chất, luân canh cây khác họ cà ít nhất 2 năm, tưới nhỏ giọt.',
    'Cắt tỉa lá già sát đất, vệ sinh tàn dư vườn, tránh chạm vào cây khi lá còn ướt sương.',
    'Phun chế phẩm sinh học chứa vi khuẩn đối kháng Bacillus subtilis hoặc Streptomyces spp.',
    'Phun gốc đồng (Copper Hydroxide, Copper Oxychloride) phối hợp Kasugamycin luân phiên.',
    'FAO Plant Protection Guide, UC Davis IPM Tomato Bacterial Spot Guidelines.'
),
(
    'early_blight', 
    'Early Blight', 
    'Úa sớm (Đốm vòng)', 
    'Alternaria solani', 
    '#f97316', 
    'Nghiêm trọng', 
    65.0, 
    'Đốm nhỏ hình tròn màu nâu sẫm trên các tầng lá già dưới gốc.',
    'Vết bệnh lan rộng 5-15mm xuất hiện các vân tròn đồng tâm đặc trưng (hình bia bắn), quầng vàng bao quanh.',
    'Phiến lá cháy khô hoàn toàn, cuống lá gãy rũ, thân cây xuất hiện vết lõm hình bầu dục sậm màu.',
    'Thời tiết ấm ẩm xen kẽ các đợt nắng ráo, nhiệt độ 24-29°C, sương đêm đọng kéo dài.',
    'Dọn dẹp tàn dư vụ trước, tỉa cành gốc cách mặt đất 25-30cm, phủ bạt nilon hạn chế bắn đất.',
    'Tăng cường bón kali và canxi giúp tế bào lá cứng cáp, ngắt bỏ ngay lá chớm bệnh.',
    'Xử lý nấm đối kháng Trichoderma harzianum quanh vùng rễ và phun dịch chiết thảo mộc.',
    'Phun luân phiên Mancozeb, Difenoconazole, Chlorothalonil hoặc Azoxystrobin.',
    'FAO IPM Field Handbook, Cornell University Vegetable MD Online.'
),
(
    'late_blight', 
    'Late Blight', 
    'Sương mai (Mốc sương)', 
    'Phytophthora infestans', 
    '#dc2626', 
    'Nghiêm trọng', 
    75.0, 
    'Vết bệnh hình dạng bất định úng nước màu xanh tái xám ở chóp hoặc mép lá non.',
    'Vết bệnh lan rộng nhanh chuyển màu nâu sẫm nhạt dầu; mặt dưới lá phủ lớp tơ mốc trắng mịn.',
    'Toàn bộ tán lá úa thối nhanh trong 2-4 ngày, thân mềm gãy, mùi tanh ẩm đặc trưng.',
    'Trời âm u mưa phùn, sương mù dày, nhiệt độ mát 15-22°C, ẩm độ bão hòa >90%.',
    'Chọn giống kháng sương mai, mật độ hàng rộng thoáng gió, che phủ vòm mưa.',
    'Tiêu hủy ngay bụi cây nhiễm đầu tiên, ngưng tưới nước khi ẩm độ ngoài trời cao.',
    'Chế phẩm chitosan phối hợp nấm cộng sinh mycorrhiza tăng sức đề kháng biểu bì.',
    'Phun chặn tức thì khi có sương lạnh: Metalaxyl-M, Dimethomorph, Cymoxanil hoặc Fosetyl-Aluminium.',
    'FAO Late Blight Global Initiative, UC IPM Tomato Pest Management.'
),
(
    'septoria_leaf_spot', 
    'Septoria Leaf Spot', 
    'Đốm lá Septoria', 
    'Septoria lycopersici', 
    '#eab308', 
    'Trung bình', 
    31.0, 
    'Vết đốm nhỏ li ti 1-3mm màu nâu xám viền nâu đậm xuất hiện dày đặc trên lá già.',
    'Tâm vết bệnh sáng màu chuyển sang màu xám tro, xuất hiện các chấm đen nhỏ li ti (ổ bào tử nấm).',
    'Hàng trăm vết đốm liên kết khiến lá vàng úa hàng loạt, lá cuộn lại và rụng sớm làm trơ cành.',
    'Nhiệt độ 20-26°C kết hợp các đợt mưa kéo dài hoặc tưới nước mạnh làm văng bùn đất lên lá.',
    'Bọc cọc chống cà chua sạch sẽ, dọn lá sát đất, dùng lưới che mặt luống giữ ẩm đều.',
    'Tỉa thông thoáng gốc, bón phân cân đối tránh thừa đạm làm lá non mỏng manh.',
    'Phun dịch tỏi ớt lên men kết hợp vi sinh vật bản địa (IMO/EM).',
    'Phun Chlorothalonil hoặc Copper Oxychloride ngay khi phát hiện những đốm đầu tiên.',
    'FAO Plant Health Division, Missouri Botanical Garden IPM.'
),
(
    'leaf_mold', 
    'Leaf Mold', 
    'Nấm mốc lá', 
    'Passalora fulva', 
    '#10b981', 
    'Nhẹ', 
    28.0, 
    'Mặt trên lá xuất hiện các đốm màu vàng xanh nhạt mờ nhạt ranh giới không phân định.',
    'Mặt dưới lá tương ứng xuất hiện thảm nấm mịn màu xanh ô liu chuyển dần sang nâu nhung.',
    'Phiến lá quăn queo, khô cháy và rụng, thường bùng phát nghiêm trọng trong nhà màng kín gió.',
    'Ẩm độ không khí nhà kính >85%, nhiệt độ ấm 22-26°C, không khí tù đọng kém lưu thông.',
    'Tăng cường quạt thông gió đối lưu trong nhà kính, mở lưới mái, tăng nhiệt độ sấy nhẹ.',
    'Tỉa lá già định kỳ hàng tuần, không để mật độ cành lá quá dày đặc chen chúc.',
    'Phun phòng bằng nấm ký sinh đối kháng Trichoderma và dịch chiết quế.',
    'Phun luân phiên hợp chất Triazole hoặc Bordeaux pha tỷ lệ chuẩn.',
    'FAO Greenhouse Crop Production Handbook, PennState Extension.'
),
(
    'powdery_mildew', 
    'Powdery Mildew', 
    'Phấn trắng', 
    'Leveillula taurica', 
    '#06b6d4', 
    'Nhẹ', 
    25.0, 
    'Các mảng bụi phấn màu trắng xám xuất hiện rải rác trên bề mặt lá như phủ bột mì.',
    'Lớp phấn trắng lan rộng khắp hai mặt lá, cuống hoa và đài hoa, lá gợn sóng biến dạng.',
    'Vùng mô lá bên dưới chuyển vàng rồi khô cháy thành mảng lớn giòn vụn, làm giảm quang hợp nặng.',
    'Khí hậu khô râm mát ban ngày xen kẽ đêm ẩm ướt nhiều sương, nhiệt độ 20-28°C.',
    'Tưới đủ ẩm cho gốc cây, tránh để cây chịu sốc hạn rồi ngập ẩm đột ngột, tỉa tán đón nắng.',
    'Ngắt bỏ lá bị bao phủ phấn nặng cho vào túi kín đem tiêu hủy.',
    'Phun dung dịch dầu neem nguyên chất (Neem oil) hoặc hỗn hợp Baking soda + xà phòng hữu cơ.',
    'Phun bột lưu huỳnh (Sulfur WG) hoặc Difenoconazole nồng độ nhẹ.',
    'FAO Organic Tomato Handbook, UC Davis IPM Powdery Mildew.'
)
ON CONFLICT (disease_id) DO NOTHING;

-- SEED 8 NGUYÊN TẮC CANH TÁC IPM
INSERT INTO public.ipm_handbook (section, step_num, title, description) VALUES
('principles', 1, 'Chọn giống kháng bệnh', 'Ưu tiên giống F1 có chứng nhận kháng héo vi khuẩn, sương mai, virus xoăn vàng lá.'),
('principles', 2, 'Khử trùng đất & giá thể', 'Phơi ải đất, rải vôi bột 50-70kg/sào hoặc xử lý nấm Trichoderma 10 ngày trước khi xuống giống.'),
('principles', 3, 'Mật độ & khoảng cách chuẩn', 'Cây cách cây 45-50cm, hàng cách hàng 70-80cm, bố trí luống theo hướng gió và ánh nắng sáng.'),
('principles', 4, 'Tưới tiêu khoa học', 'Áp dụng tưới nhỏ giọt quanh gốc rễ; không bao giờ tưới phun mưa lúc chiều muộn làm ướt lá qua đêm.'),
('principles', 5, 'Bón phân cân đối N-P-K', 'Không bón thừa đạm làm vách tế bào mỏng; tăng cường Silic, Canxi, Bo tăng độ dai biểu bì lá.'),
('principles', 6, 'Cắt tỉa & dọn vệ sinh', 'Tỉa chồi nách vô hiệu lúc trời khô ráo; cắt bỏ toàn bộ lá gốc chạm mặt đất cách mặt luống 25-30cm.'),
('principles', 7, 'Che phủ mặt luống', 'Dùng màng phủ nông nghiệp hoặc rơm rạ khô ngăn giọt mưa bắn mang nấm khuẩn từ đất lên phiến lá.'),
('principles', 8, 'Tiêu hủy tàn dư cây bệnh', 'Không vứt lá bệnh xuống rãnh nước; thu gom vào bao kín mang ra bãi tiêu hủy hoặc rắc vôi chôn sâu.')
ON CONFLICT DO NOTHING;
