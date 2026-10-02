from django.db import models
from django.contrib.auth.models import User
# from cloudinary_storage.storage import

# Create your models here.


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(blank=True)
    title = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    # avatar = CloudinaryField('image', blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    birth_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s profile"


class Leaf_image(models.Model):
    image = models.ImageField(
        upload_to='Leaf_images/', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE)
    result = models.JSONField(blank=True, null=True)
    heatmap = models.ImageField(upload_to='heatmaps/', blank=True, null=True)
    more = models.TextField(blank=True, default='')
    explain = models.TextField(blank=True, null=True)
    # Thông tin bổ sung do người dùng cung cấp ở bước "chẩn đoán nâng cao"
    gender = models.CharField(max_length=10, blank=True, default='')
    age = models.CharField(max_length=10, blank=True, default='')
    symptom = models.TextField(blank=True, default='')
    illness_history = models.TextField(blank=True, default='')
    drug_history = models.TextField(blank=True, default='')

    def __str__(self):
        return f"Image {self.id} uploaded at {self.uploaded_at}"

