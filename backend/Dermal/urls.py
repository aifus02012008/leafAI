from .views import *
from .api_views import (
    api_diseases,
    api_handbook,
    api_models_info,
    api_stats,
    api_diagnose,
    api_history,
    api_history_delete,
    api_history_clear,
    api_supabase_status,
    api_supabase_sync,
    api_chat_consult,
    api_auth_login,
    api_auth_signup,
    api_auth_user,
    api_auth_logout,
    spa_app_view,
    spa_manifest_view,
    spa_sw_view,
    spa_asset_view,
    spa_page_view,
)
from django.urls import path

urlpatterns = [
    # Giao diện và API cũ (bảo toàn 100% chức năng)
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
    path('health/', health, name="health"),

    # REST API LEAF_AI (Poster Standard)
    path('api/diseases/', api_diseases, name='api_diseases'),
    path('api/handbook/', api_handbook, name='api_handbook'),
    path('api/models/', api_models_info, name='api_models_info'),
    path('api/stats/', api_stats, name='api_stats'),
    path('api/diagnose/', api_diagnose, name='api_diagnose'),
    path('api/history/', api_history, name='api_history'),
    path('api/history/<int:record_id>/delete/', api_history_delete, name='api_history_delete'),
    path('api/history/clear/', api_history_clear, name='api_history_clear'),
    path('api/chat/', api_chat_consult, name='api_chat_consult'),
    path('api/auth/login/', api_auth_login, name='api_auth_login'),
    path('api/auth/signup/', api_auth_signup, name='api_auth_signup'),
    path('api/auth/user/', api_auth_user, name='api_auth_user'),
    path('api/auth/logout/', api_auth_logout, name='api_auth_logout'),

    # Supabase Integration Endpoints
    path('api/supabase/status/', api_supabase_status, name='api_supabase_status'),
    path('api/supabase/sync/', api_supabase_sync, name='api_supabase_sync'),

    # SPA Web & PWA Mobile App Route
    path('app/', spa_app_view, name='spa_app'),
    # Frontend đa trang v2: /app/scan.html, /app/library.html, ...
    path('app/<slug:page>.html', spa_page_view, name='spa_page'),
    path('app/manifest.json', spa_manifest_view, name='spa_manifest_app'),
    path('app/sw.js', spa_sw_view, name='spa_sw_app'),
    path('app/assets/<path:path>', spa_asset_view, name='spa_asset_app'),
    path('manifest.json', spa_manifest_view, name='spa_manifest'),
    path('sw.js', spa_sw_view, name='spa_sw'),
    path('assets/<path:path>', spa_asset_view, name='spa_asset'),
]
