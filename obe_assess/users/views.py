from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import DashboardDataSerializer, UserSerializer, RegisterSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

# 🛡️ NEW: Custom Permission to check if the user is an Admin
class IsAdminRole(permissions.BasePermission):
    def has_permission(self, request, view):
        # Only allow access if the user is logged in AND their role is 'admin'
        return bool(request.user and request.user.is_authenticated and request.user.role == 'admin')

# 🛑 UPDATED: This is now Admin-Only! Public signups are completely blocked.
class RegisterView(generics.CreateAPIView):
    permission_classes = (IsAdminRole,) 
    serializer_class = RegisterSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        # Standard DRF creation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Return a nice, clean success message for the React frontend
        return Response({
            "message": f"✅ {user.role.capitalize()} account created successfully!",
            "user_id": user.id,
            "email": user.email
        }, status=status.HTTP_201_CREATED)

class ObtainTokenPairWithUserView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        """
        Expecting: { "refresh": "<refresh_token>" } 
        """
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail":"Refresh token required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user

class ChangePasswordView(APIView):
    permission_classes = (permissions.IsAuthenticated,)
    def post(self, request):
        user = request.user
        old = request.data.get("old_password")
        new = request.data.get("new_password")
        if not user.check_password(old):
            return Response({"old_password": ["Wrong password."]}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new)
        user.save()
        return Response({"detail": "Password updated."}, status=status.HTTP_200_OK)

# Admin list of users
class UserListView(generics.ListAPIView):
    permission_classes = (IsAdminRole,) # Also updated this to use the strict role check!
    serializer_class = UserSerializer
    queryset = User.objects.all()

class DashboardDataView(APIView):
    """
    GET /api/users/dashboard/
    Returns the logged-in user's profile and their courses.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = DashboardDataSerializer(request.user)
        return Response(serializer.data)