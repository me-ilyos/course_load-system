from rest_framework import permissions
from django.contrib.auth import get_user_model

User = get_user_model()

class IsSuperAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser

class IsDepartmentHead(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == User.UserType.DEPARTMENT_HEAD
        )

    def has_object_permission(self, request, view, obj):
        # For professor objects, check if the department head manages their department
        if hasattr(obj, 'department'):
            return obj.department.head == request.user
        return False 