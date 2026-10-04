from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    title = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Leaf_image(models.Model):
    """
    Bản ghi chẩn đoán ảnh lá cây vải thiều Lục Ngạn (Bắc Giang).
    Tích hợp ResNet-18 + Grad-CAM, nhận diện đa bệnh đồng nhiễm (Co-infection),
    lưu trữ cục bộ SQLite và đồng bộ tự động lên Supabase Database.
    """
    image = models.ImageField(upload_to='Leaf_images/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True, blank=True)
    result = models.JSONField(blank=True, null=True)
    heatmap = models.ImageField(upload_to='heatmaps/', blank=True, null=True)
    more = models.TextField(blank=True, default='')
    explain = models.TextField(blank=True, null=True)

    # Legacy fields (Bảo toàn 100% tương thích ngược cho unit tests)
    gender = models.CharField(max_length=10, blank=True, default='')
    age = models.CharField(max_length=10, blank=True, default='')
    symptom = models.TextField(blank=True, default='')
    illness_history = models.TextField(blank=True, default='')
    drug_history = models.TextField(blank=True, default='')

    # Agricultural Leaf AI & Deep Learning Fields
    model_version = models.CharField(max_length=20, default='v3', help_text="Mô hình sử dụng: 'v3' hoặc 'v4'")
    plant_type = models.CharField(max_length=50, default='lychee', help_text="Loại cây: Vải thiều Lục Ngạn (lychee)")
    primary_disease = models.CharField(max_length=100, blank=True, default='', help_text="Mã bệnh chính")
    primary_disease_vi = models.CharField(max_length=150, blank=True, default='', help_text="Tên tiếng Việt")
    confidence = models.FloatField(default=0.0, help_text="Độ tin cậy %")
    severity = models.CharField(max_length=50, default='Nghiêm trọng', help_text="Mức độ nghiêm trọng")
    is_coinfection = models.BooleanField(default=False, help_text="Cảnh báo phát hiện đa bệnh (đồng nhiễm)")
    secondary_diseases = models.JSONField(default=list, blank=True, help_text="Danh sách bệnh phụ phát hiện")
    detections = models.JSONField(default=list, blank=True, help_text="Tọa độ bounding boxes [x, y, w, h]")
    treatment_summary = models.TextField(blank=True, default='', help_text="Tóm tắt phác đồ điều trị 3 cấp độ")

    # Supabase Sync Status
    synced_to_supabase = models.BooleanField(default=False, help_text="Trạng thái đồng bộ Supabase Cloud")
    supabase_id = models.CharField(max_length=100, blank=True, default='', help_text="ID bản ghi trên Supabase")

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Leaf Scan #{self.id} - {self.primary_disease_vi or 'Chẩn đoán'} ({self.confidence}%) at {self.uploaded_at}"


class TomatoDisease(models.Model):
    """
    Thư viện bệnh cây trồng chuẩn hóa FAO & VietGAP cho lá vải thiều Lục Ngạn.
    """
    disease_id = models.CharField(max_length=50, unique=True)
    name_en = models.CharField(max_length=100)
    name_vi = models.CharField(max_length=150)
    pathogen = models.CharField(max_length=200, help_text="Tác nhân gây bệnh (nấm / vi khuẩn)")
    color = models.CharField(max_length=20, default='#ea580c', help_text="Màu nhận diện bounding box")
    severity_default = models.CharField(max_length=50, default='Nghiêm trọng')
    confidence_default = models.FloatField(default=50.0)
    
    # 3 giai đoạn triệu chứng
    symptoms_stage1 = models.TextField(blank=True, default='', help_text="Giai đoạn 1: Khởi phát")
    symptoms_stage2 = models.TextField(blank=True, default='', help_text="Giai đoạn 2: Phát triển")
    symptoms_stage3 = models.TextField(blank=True, default='', help_text="Giai đoạn 3: Bùng phát")

    conditions = models.TextField(blank=True, default='', help_text="Điều kiện nhiệt ẩm thuận lợi phát sinh")
    prevention = models.TextField(blank=True, default='', help_text="Cách phòng ngừa canh tác")

    # Phác đồ điều trị 3 cấp độ
    treatment_cultural = models.TextField(blank=True, default='', help_text="1. Biện pháp canh tác")
    treatment_bio = models.TextField(blank=True, default='', help_text="2. Biện pháp sinh học")
    treatment_chemical = models.TextField(blank=True, default='', help_text="3. Biện pháp hóa học (4 đúng)")
    references = models.TextField(blank=True, default='', help_text="Nguồn tài liệu khoa học FAO, IRRI, v.v.")

    def __str__(self):
        return f"{self.name_vi} ({self.name_en})"


class IPMHandbookItem(models.Model):
    """
    Cẩm nang chăm sóc & phòng bệnh chuẩn FAO:
    8 nguyên tắc, 7 bước kiểm tra đồng ruộng, 10 bước IPM, an toàn BVTV.
    """
    SECTION_CHOICES = [
        ('principles', '8 Nguyên tắc canh tác'),
        ('inspection', '7 Bước kiểm tra đồng ruộng'),
        ('ipm', '10 Bước IPM (FAO)'),
        ('safe', 'An toàn BVTV & 4 Đúng'),
    ]
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    step_num = models.IntegerField(default=1)
    title = models.CharField(max_length=200)
    description = models.TextField()

    class Meta:
        ordering = ['section', 'step_num']

    def __str__(self):
        return f"[{self.section}] #{self.step_num} {self.title}"
