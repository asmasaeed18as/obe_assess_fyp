# users/urls.py
from django.urls import path
from .views import DashboardDataView, RegisterView, AdminRegisterView, ObtainTokenPairWithUserView, LogoutView, ProfileView, ChangePasswordView, UserListView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register-admin/", AdminRegisterView.as_view(), name="register-admin"),
    path('login/', ObtainTokenPairWithUserView.as_view(), name='login'),
    path("token/", ObtainTokenPairWithUserView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", ProfileView.as_view(), name="me"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("", UserListView.as_view(), name="user-list"),  # admin only
    # ✅ FIXED: Changed 'dashboard/' to 'dashboard-data/' to match React
    path('dashboard-data/', DashboardDataView.as_view(), name='dashboard_data'),
]
