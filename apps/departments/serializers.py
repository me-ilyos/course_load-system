from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from .models import Department, Professor

User = get_user_model()

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        
        # Add user type specific information
        data['user'] = user
        data['user_type'] = user.user_type
        data['is_superuser'] = user.is_superuser
        
        # Add department information for department heads
        if user.user_type == User.UserType.DEPARTMENT_HEAD:
            department = Department.objects.filter(head=user).first()
            if department:
                data['department'] = {
                    'code': department.code,
                    'title': department.title
                }
        
        # Add department and professor information for professors
        elif user.user_type == User.UserType.PROFESSOR:
            professor = Professor.objects.filter(user=user).select_related('department').first()
            if professor:
                data['professor_info'] = {
                    'full_name': professor.full_name,
                    'department': {
                        'code': professor.department.code,
                        'title': professor.department.title
                    },
                    'experience_level': professor.experience_level,
                    'has_phd': professor.has_phd
                }
        
        return data

class UserDetailSerializer(serializers.ModelSerializer):
    department_info = serializers.SerializerMethodField()
    professor_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'user_type', 'is_superuser', 'department_info', 'professor_info')

    def get_department_info(self, obj):
        if obj.user_type == User.UserType.DEPARTMENT_HEAD:
            department = Department.objects.filter(head=obj).first()
            if department:
                return {
                    'code': department.code,
                    'title': department.title
                }
        return None

    def get_professor_info(self, obj):
        if obj.user_type == User.UserType.PROFESSOR:
            professor = Professor.objects.filter(user=obj).select_related('department').first()
            if professor:
                return {
                    'full_name': professor.full_name,
                    'department': {
                        'code': professor.department.code,
                        'title': professor.department.title
                    },
                    'experience_level': professor.experience_level,
                    'has_phd': professor.has_phd
                }
        return None

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'password', 'user_type')
        extra_kwargs = {
            'password': {'write_only': True},
            'user_type': {'read_only': True}  # User type will be set based on the endpoint
        }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class DepartmentHeadCreateSerializer(UserSerializer):
    department_code = serializers.CharField(write_only=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('department_code',)

    def create(self, validated_data):
        department_code = validated_data.pop('department_code')
        # Set user type to department head
        validated_data['user_type'] = User.UserType.DEPARTMENT_HEAD
        user = super().create(validated_data)
        
        # Assign user as department head
        try:
            department = Department.objects.get(code=department_code)
            department.head = user
            department.save()
        except Department.DoesNotExist:
            user.delete()
            raise serializers.ValidationError({"department_code": "Invalid department code"})
        
        return user

class ProfessorCreateSerializer(UserSerializer):
    department_code = serializers.CharField(write_only=True)
    years_of_experience = serializers.IntegerField(required=True)
    has_phd = serializers.BooleanField(required=True)
    phone_number = serializers.CharField(required=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'department_code', 'years_of_experience', 'has_phd', 'phone_number'
        )

    def create(self, validated_data):
        department_code = validated_data.pop('department_code')
        years_of_experience = validated_data.pop('years_of_experience')
        has_phd = validated_data.pop('has_phd')
        phone_number = validated_data.pop('phone_number')

        # Set user type to professor
        validated_data['user_type'] = User.UserType.PROFESSOR
        user = super().create(validated_data)

        try:
            department = Department.objects.get(code=department_code)
            # Create professor profile
            Professor.objects.create(
                user=user,
                department=department,
                full_name=f"{user.first_name} {user.last_name}".strip(),
                email=user.email,
                phone_number=phone_number,
                years_of_experience=years_of_experience,
                has_phd=has_phd
            )
        except Department.DoesNotExist:
            user.delete()
            raise serializers.ValidationError({"department_code": "Invalid department code"})

        return user 