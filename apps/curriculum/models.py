from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from apps.departments.models import Department
import json
from typing import Dict, List
import pandas as pd
from django.conf import settings
import os

class Curriculum(models.Model):
    class DegreeType(models.TextChoices):
        BACHELORS = 'BSC', 'Bachelors'
        MASTERS = 'MSC', 'Masters'

    major_code = models.CharField(max_length=10, help_text="Major code (e.g., CS2024)")
    classification = models.CharField(max_length=100, help_text="e.g., ICT Engineer")
    curriculum_code = models.CharField(
        max_length=8,
        unique=True,
        help_text="Unique curriculum code (e.g., 60610800)"
    )
    degree_type = models.CharField(
        max_length=3,
        choices=DegreeType.choices,
        default=DegreeType.BACHELORS
    )
    total_credits = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Total credits required for graduation"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='curricula'
    )
    courses_data = models.JSONField(
        default=dict,
        help_text="JSON structure containing all course information"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Curriculum"
        verbose_name_plural = "Curricula"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.major_code} - {self.classification} ({self.get_degree_type_display()})"

    @staticmethod
    def validate_course_structure(course_data: Dict) -> bool:
        """Validate the structure of a single course entry"""
        required_fields = {
            'code': str,
            'name': str,
            'type': str,  # 'mandatory' or 'selective'
            'credits': int,
            'hours': {
                'lecture': int,
                'lab': int,
                'practice': int,
                'seminar': int,
                'individual': int
            },
            'semester': int
        }

        def validate_structure(data, schema):
            if not isinstance(data, type(schema)):
                return False
            if isinstance(schema, dict):
                return all(
                    k in data and validate_structure(data[k], v)
                    for k, v in schema.items()
                )
            return True

        return validate_structure(course_data, required_fields)

    def clean(self):
        super().clean()
        # Validate minimum credits based on degree type
        if self.degree_type == self.DegreeType.BACHELORS and self.total_credits < 120:
            raise ValidationError("Bachelor's degree must have at least 120 credits")
        elif self.degree_type == self.DegreeType.MASTERS and self.total_credits < 30:
            raise ValidationError("Master's degree must have at least 30 credits")

        # Validate courses data structure
        if not isinstance(self.courses_data, dict):
            raise ValidationError("Courses data must be a dictionary")

        # Validate each course in the courses_data
        for course_code, course_data in self.courses_data.items():
            if not self.validate_course_structure(course_data):
                raise ValidationError(f"Invalid course structure for course {course_code}")
            
            # Validate credit hours calculation
            total_hours = sum(course_data['hours'].values())
            expected_hours = course_data['credits'] * 30
            if total_hours != expected_hours:
                raise ValidationError(
                    f"Course {course_code}: Total hours ({total_hours}) must equal "
                    f"credits × 30 ({expected_hours})"
                )

    def calculate_total_credits(self) -> int:
        """Calculate total credits from courses data"""
        return sum(
            course['credits']
            for course in self.courses_data.values()
        )

    def update_course(self, course_code: str, course_data: Dict) -> None:
        """Update a specific course in the curriculum"""
        if not self.validate_course_structure(course_data):
            raise ValidationError(f"Invalid course structure for course {course_code}")

        courses = self.courses_data.copy()
        courses[course_code] = course_data
        self.courses_data = courses
        self.full_clean()
        self.save()

    def export_to_excel(self, filepath: str) -> None:
        """Export curriculum data to Excel"""
        courses_list = []
        for code, data in self.courses_data.items():
            course_dict = {
                'Course Code': code,
                'Course Name': data['name'],
                'Type': data['type'],
                'Credits': data['credits'],
                'Semester': data['semester'],
                'Lecture Hours': data['hours']['lecture'],
                'Lab Hours': data['hours']['lab'],
                'Practice Hours': data['hours']['practice'],
                'Seminar Hours': data['hours']['seminar'],
                'Individual Hours': data['hours']['individual'],
                'Total Hours': sum(data['hours'].values())
            }
            courses_list.append(course_dict)

        df = pd.DataFrame(courses_list)
        df.to_excel(filepath, index=False)

    @classmethod
    def import_from_excel(cls, filepath: str, curriculum_instance=None):
        """Import curriculum data from Excel"""
        df = pd.read_excel(filepath)
        courses_data = {}

        for _, row in df.iterrows():
            course_code = row['Course Code']
            courses_data[course_code] = {
                'name': row['Course Name'],
                'type': row['Type'],
                'credits': int(row['Credits']),
                'semester': int(row['Semester']),
                'hours': {
                    'lecture': int(row['Lecture Hours']),
                    'lab': int(row['Lab Hours']),
                    'practice': int(row['Practice Hours']),
                    'seminar': int(row['Seminar Hours']),
                    'individual': int(row['Individual Hours'])
                }
            }

        if curriculum_instance:
            curriculum_instance.courses_data = courses_data
            curriculum_instance.full_clean()
            curriculum_instance.save()
            return curriculum_instance
        
        return courses_data

    def get_semester_courses(self, semester: int) -> List[Dict]:
        """Get all courses for a specific semester"""
        return [
            {'code': code, **data}
            for code, data in self.courses_data.items()
            if data['semester'] == semester
        ]

    def get_course_professors(self, course_code: str, academic_year: int = None):
        """Get professors assigned to a specific course"""
        from apps.departments.models import Professor
        course_data = self.courses_data.get(course_code)
        if not course_data:
            return []
        
        professors = Professor.objects.filter(
            course_assignments__course_code=course_code
        )
        if academic_year:
            professors = professors.filter(
                course_assignments__academic_year=academic_year
            )
        return professors.distinct()
