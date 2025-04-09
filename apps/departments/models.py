from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError

class User(AbstractUser):
    class UserType(models.TextChoices):
        SUPERADMIN = 'SA', 'Superadmin'
        DEPARTMENT_HEAD = 'DH', 'Department Head'
        PROFESSOR = 'PR', 'Professor/Teacher'
    
    user_type = models.CharField(
        max_length=2,
        choices=UserType.choices,
        default=UserType.PROFESSOR
    )
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

class Department(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    head = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='headed_department',
        limit_choices_to={'user_type': User.UserType.DEPARTMENT_HEAD}
    )

    def clean(self):
        if self.head and self.head.user_type != User.UserType.DEPARTMENT_HEAD:
            raise ValidationError("Department head must be a user with Department Head role.")

    def __str__(self):
        return f"{self.code} - {self.title}"

    class Meta:
        ordering = ['code']

class Professor(models.Model):
    class ExperienceLevel(models.TextChoices):
        BEGINNER = 'BG', 'Beginner'
        INTERMEDIATE = 'IN', 'Intermediate'
        EXPERIENCED = 'EX', 'Experienced'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': User.UserType.PROFESSOR}
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        related_name='professors'
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    years_of_experience = models.PositiveIntegerField(
        validators=[MinValueValidator(0)]
    )
    has_phd = models.BooleanField(default=False)
    experience_level = models.CharField(
        max_length=2,
        choices=ExperienceLevel.choices,
        editable=False
    )

    def save(self, *args, **kwargs):
        # Automatically set experience level based on years of experience
        if self.years_of_experience < 1:
            self.experience_level = self.ExperienceLevel.BEGINNER
        elif self.years_of_experience < 4:
            self.experience_level = self.ExperienceLevel.INTERMEDIATE
        elif self.years_of_experience >= 5:
            self.experience_level = self.ExperienceLevel.EXPERIENCED
        else:  # 4 years
            self.experience_level = self.ExperienceLevel.INTERMEDIATE
        
        super().save(*args, **kwargs)

    def clean(self):
        if self.user and self.user.user_type != User.UserType.PROFESSOR:
            raise ValidationError("User must have Professor/Teacher role.")

    def __str__(self):
        return f"{self.full_name} ({self.get_experience_level_display()})"

    class Meta:
        ordering = ['full_name']
