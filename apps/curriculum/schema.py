from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import json
from enum import Enum
from django.core.exceptions import ValidationError

class CourseType(str, Enum):
    MANDATORY = "mandatory"
    SELECTIVE = "selective"

@dataclass
class HourDistribution:
    lecture: int = 0
    lab: int = 0
    practice: int = 0
    seminar: int = 0
    individual: int = 0

    def total_hours(self) -> int:
        return (self.lecture + self.lab + self.practice + 
                self.seminar + self.individual)

    def instructional_hours(self) -> int:
        return (self.lecture + self.lab + self.practice + 
                self.seminar)

    def to_dict(self) -> Dict:
        return {
            "lecture": self.lecture,
            "lab": self.lab,
            "practice": self.practice,
            "seminar": self.seminar,
            "individual": self.individual
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'HourDistribution':
        return cls(
            lecture=data.get('lecture', 0),
            lab=data.get('lab', 0),
            practice=data.get('practice', 0),
            seminar=data.get('seminar', 0),
            individual=data.get('individual', 0)
        )

@dataclass
class SemesterData:
    semester: int
    credits: int
    hours: HourDistribution

    def validate(self) -> None:
        """Validate semester data"""
        if self.credits <= 0:
            raise ValidationError("Credits must be positive")
        
        expected_hours = self.credits * 30
        total_hours = self.hours.total_hours()
        
        if total_hours != expected_hours:
            raise ValidationError(
                f"Total hours ({total_hours}) must equal credits × 30 ({expected_hours})"
            )

        if self.hours.individual <= 0:
            raise ValidationError("Individual hours must be present")

        if self.hours.instructional_hours() <= 0:
            raise ValidationError("At least one type of instructional hour must be present")

    def to_dict(self) -> Dict:
        return {
            "semester": self.semester,
            "credits": self.credits,
            "hours": self.hours.to_dict()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'SemesterData':
        return cls(
            semester=data['semester'],
            credits=data['credits'],
            hours=HourDistribution.from_dict(data['hours'])
        )

@dataclass
class CourseData:
    code: str
    name: str
    type: CourseType
    semesters: List[SemesterData]
    prerequisites: List[str] = None

    def validate(self) -> None:
        """Validate course data"""
        if not self.code or not self.name:
            raise ValidationError("Course code and name are required")

        if not isinstance(self.type, CourseType):
            raise ValidationError("Invalid course type")

        if not self.semesters:
            raise ValidationError("At least one semester is required")

        # Validate each semester
        semester_numbers = set()
        for semester_data in self.semesters:
            if semester_data.semester in semester_numbers:
                raise ValidationError(f"Duplicate semester number: {semester_data.semester}")
            semester_numbers.add(semester_data.semester)
            semester_data.validate()

    def to_dict(self) -> Dict:
        return {
            "code": self.code,
            "name": self.name,
            "type": self.type.value,
            "semesters": [sem.to_dict() for sem in self.semesters],
            "prerequisites": self.prerequisites or []
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CourseData':
        return cls(
            code=data['code'],
            name=data['name'],
            type=CourseType(data['type']),
            semesters=[SemesterData.from_dict(sem) for sem in data['semesters']],
            prerequisites=data.get('prerequisites', [])
        )

class CurriculumSchema:
    """Utility class for managing curriculum course data"""

    @staticmethod
    def validate_course(course_data: Dict) -> None:
        """Validate a course entry"""
        try:
            course = CourseData.from_dict(course_data)
            course.validate()
        except (KeyError, ValueError) as e:
            raise ValidationError(f"Invalid course data structure: {str(e)}")
        except ValidationError as e:
            raise ValidationError(f"Course validation failed: {str(e)}")

    @staticmethod
    def validate_curriculum(curriculum_data: Dict) -> None:
        """Validate entire curriculum data"""
        if not isinstance(curriculum_data, dict):
            raise ValidationError("Curriculum data must be a dictionary")

        # Validate each course
        for course_code, course_data in curriculum_data.items():
            if course_code != course_data.get('code'):
                raise ValidationError(
                    f"Course code mismatch: {course_code} vs {course_data.get('code')}"
                )
            CurriculumSchema.validate_course(course_data)

        # Validate prerequisites
        all_codes = set(curriculum_data.keys())
        for course_data in curriculum_data.values():
            prerequisites = course_data.get('prerequisites', [])
            invalid_prereqs = set(prerequisites) - all_codes
            if invalid_prereqs:
                raise ValidationError(
                    f"Invalid prerequisites for {course_data['code']}: {invalid_prereqs}"
                )

    @staticmethod
    def example_single_semester_course() -> Dict:
        """Example of a single-semester course"""
        return {
            "code": "CS101",
            "name": "Introduction to Programming",
            "type": "mandatory",
            "semesters": [{
                "semester": 1,
                "credits": 3,
                "hours": {
                    "lecture": 30,
                    "lab": 30,
                    "practice": 0,
                    "seminar": 0,
                    "individual": 30
                }
            }],
            "prerequisites": []
        }

    @staticmethod
    def example_multi_semester_course() -> Dict:
        """Example of a multi-semester course"""
        return {
            "code": "CS201",
            "name": "Advanced Programming",
            "type": "mandatory",
            "semesters": [
                {
                    "semester": 2,
                    "credits": 2,
                    "hours": {
                        "lecture": 15,
                        "lab": 15,
                        "practice": 15,
                        "seminar": 0,
                        "individual": 15
                    }
                },
                {
                    "semester": 3,
                    "credits": 3,
                    "hours": {
                        "lecture": 30,
                        "lab": 30,
                        "practice": 15,
                        "seminar": 0,
                        "individual": 15
                    }
                }
            ],
            "prerequisites": ["CS101"]
        }

    @staticmethod
    def example_complete_curriculum() -> Dict:
        """Example of a complete curriculum"""
        return {
            "CS101": CurriculumSchema.example_single_semester_course(),
            "CS201": CurriculumSchema.example_multi_semester_course()
        }

class CurriculumManager:
    """Utility class for managing curriculum data"""

    def __init__(self, curriculum_data: Dict):
        self.data = curriculum_data
        CurriculumSchema.validate_curriculum(self.data)

    def add_course(self, course_data: Dict) -> None:
        """Add a new course to the curriculum"""
        CurriculumSchema.validate_course(course_data)
        code = course_data['code']
        if code in self.data:
            raise ValidationError(f"Course {code} already exists")
        self.data[code] = course_data

    def update_course(self, course_data: Dict) -> None:
        """Update an existing course"""
        code = course_data['code']
        if code not in self.data:
            raise ValidationError(f"Course {code} does not exist")
        CurriculumSchema.validate_course(course_data)
        self.data[code] = course_data

    def remove_course(self, course_code: str) -> None:
        """Remove a course from the curriculum"""
        if course_code not in self.data:
            raise ValidationError(f"Course {course_code} does not exist")
        
        # Check if this course is a prerequisite for any other course
        for course in self.data.values():
            if course_code in course.get('prerequisites', []):
                raise ValidationError(
                    f"Cannot remove {course_code}: it is a prerequisite for {course['code']}"
                )
        
        del self.data[course_code]

    def get_courses_by_semester(self, semester: int) -> List[Dict]:
        """Get all courses for a specific semester"""
        courses = []
        for course in self.data.values():
            if any(sem['semester'] == semester for sem in course['semesters']):
                courses.append(course)
        return courses

    def get_courses_by_type(self, course_type: str) -> List[Dict]:
        """Get all courses of a specific type"""
        return [
            course for course in self.data.values()
            if course['type'] == course_type
        ]

    def get_prerequisites_tree(self, course_code: str) -> Dict:
        """Get prerequisite tree for a course"""
        if course_code not in self.data:
            raise ValidationError(f"Course {course_code} does not exist")

        def build_tree(code: str, visited: set) -> Dict:
            if code in visited:
                return None  # Prevent circular dependencies
            visited.add(code)
            course = self.data[code]
            prereqs = {}
            for prereq_code in course.get('prerequisites', []):
                prereq_tree = build_tree(prereq_code, visited.copy())
                if prereq_tree is not None:
                    prereqs[prereq_code] = prereq_tree
            return {
                'code': code,
                'name': course['name'],
                'prerequisites': prereqs
            }

        return build_tree(course_code, set()) 