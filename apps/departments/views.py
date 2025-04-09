from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .serializers import (
    DepartmentHeadCreateSerializer, 
    ProfessorCreateSerializer,
    LoginSerializer,
    UserDetailSerializer
)
from .permissions import IsSuperAdmin, IsDepartmentHead
from .models import Department

User = get_user_model()

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        user_data = UserDetailSerializer(user).data
        
        response_data = {
            'user': user_data,
            'message': 'Login successful'
        }
        
        return Response(response_data)

class UserDetailView(generics.RetrieveAPIView):
    serializer_class = UserDetailSerializer
    authentication_classes = [BasicAuthentication]

    def get_object(self):
        return self.request.user

class DepartmentHeadCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = DepartmentHeadCreateSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsSuperAdmin]

class ProfessorCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = ProfessorCreateSerializer
    authentication_classes = [BasicAuthentication]
    permission_classes = [IsSuperAdmin | IsDepartmentHead]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # If department head is creating, enforce their department
        if not request.user.is_superuser:
            department = Department.objects.filter(head=request.user).first()
            if not department:
                return Response(
                    {"detail": "Department head is not assigned to any department"},
                    status=status.HTTP_403_FORBIDDEN
                )
            if serializer.validated_data['department_code'] != department.code:
                return Response(
                    {"detail": "You can only create professors for your own department"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
