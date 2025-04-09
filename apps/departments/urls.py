from django.urls import path
from .views import (
    DepartmentHeadCreateView, 
    ProfessorCreateView,
    LoginView,
    UserDetailView
)

app_name = 'departments'

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('me/', UserDetailView.as_view(), name='user-detail'),
    path('create-department-head/', DepartmentHeadCreateView.as_view(), name='create-department-head'),
    path('create-professor/', ProfessorCreateView.as_view(), name='create-professor'),
] 