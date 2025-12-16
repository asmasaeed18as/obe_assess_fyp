# users/views.py
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import User
from .serializers import DashboardDataSerializer, UserSerializer, RegisterSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class RegisterView(generics.CreateAPIView):
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer
    queryset = User.objects.all()

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

# Optional: Admin list of users
class UserListView(generics.ListAPIView):
    permission_classes = (permissions.IsAdminUser,)
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