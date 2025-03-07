from django.urls import path
from .views import RegisterView,protected_view,FaceUploadView,FaceLoginView,FaceLoginStatusView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),  
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  
    path('protected/', protected_view, name='protected'),
    path('upload_face/', FaceUploadView.as_view(), name='upload_face'),
    path('face_login/', FaceLoginView.as_view(), name='face_login'),
    path('face_login_status/<str:task_id>/', FaceLoginStatusView.as_view(), name='face_login_status'),
    
]
