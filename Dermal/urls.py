from .views import *
from django.urls import path

urlpatterns = [
    path('', home_view, name='home'),
    path('upload/', upload_image, name='upload_image'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signup/', signup_view, name='signup'),
    path('chatbot/', chatbot_view, name='chatbot'),
    path('chatbot/api/', chatbot_api, name='chatbot_api'),
    path('result/<int:image_id>/', result_view, name='result'),
    path('profile/', your_profile, name='your_profile'),
    path('upload/file/', upload_file, name='upload_file'),
    path('predict/<int:id>/', predict, name="predict"),
    path('pharmacy/', pharmacy_view, name='pharmacy'),
    path('history/<int:image_id>/delete/', delete_classification, name='delete_classification'),
    path('health/', health, name="health")
]
