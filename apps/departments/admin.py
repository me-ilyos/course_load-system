from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from .models import Department, Professor

User = get_user_model()

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'user_type', 'is_active', 'is_staff')
    list_filter = ('user_type', 'is_active', 'is_staff')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'head', 'professor_count')
    list_display_links = ('code', 'title')
    search_fields = ('code', 'title', 'head__username')
    
    def professor_count(self, obj):
        return obj.professors.count()
    professor_count.short_description = 'Number of Professors'

@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'experience_level', 'years_of_experience', 'has_phd', 'email')
    list_filter = ('department', 'has_phd', 'experience_level')
    search_fields = ('full_name', 'email', 'user__username')
    list_select_related = ('department', 'user')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'full_name', 'email', 'phone_number')
        }),
        ('Department Information', {
            'fields': ('department',)
        }),
        ('Qualifications', {
            'fields': ('years_of_experience', 'has_phd', 'experience_level')
        }),
    )
    
    readonly_fields = ('experience_level',)  # This is calculated automatically
