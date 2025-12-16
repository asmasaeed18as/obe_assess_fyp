# users/urls.py
from django.urls import path
from .views import DashboardDataView, RegisterView, ObtainTokenPairWithUserView, LogoutView, ProfileView, ChangePasswordView, UserListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path('login/', ObtainTokenPairWithUserView.as_view(), name='login'),
    path("token/", ObtainTokenPairWithUserView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", ProfileView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("", UserListView.as_view(), name="user-list"),  # admin only
    # ✅ NEW: Dashboard Data Endpoint
    path('dashboard/', DashboardDataView.as_view(), name='dashboard_data'),
]
