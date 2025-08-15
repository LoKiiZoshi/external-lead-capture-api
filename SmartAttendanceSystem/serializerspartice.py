from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import base64
from django.core.files.base import ContentFile
from .models import (
    User, School, Department, Class, Student, Teacher, Subject,
    FaceEncoding, AttendanceSession, AttendanceRecord, AttendanceAlert,
    AttendanceReport, SystemConfiguration, AuditLog
)


class UserSerializer(serializers.ModelSerializer):
    """Base user serializer"""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'role',
            'phone_number', 'profile_image', 'date_of_birth', 'address',
            'emergency_contact', 'is_active_student', 'password', 'confirm_password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError("Passwords don't match")
        attrs.pop('confirm_password', None)
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Login serializer"""
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include username and password')


class SchoolSerializer(serializers.ModelSerializer):
    """School serializer"""
    
    class Meta:
        model = School
        fields = '__all__'


class DepartmentSerializer(serializers.ModelSerializer):
    """Department serializer"""
    head_of_department_name = serializers.CharField(source='head_of_department.get_full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    
    class Meta:
        model = Department
        fields = '__all__'


class ClassSerializer(serializers.ModelSerializer):
    """Class serializer"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    class_teacher_name = serializers.CharField(source='class_teacher.get_full_name', read_only=True)
    student_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Class
        fields = '__all__'
    
    def get_student_count(self, obj):
        return obj.students.filter(user__is_active_student=True).count()


class SubjectSerializer(serializers.ModelSerializer):
    """Subject serializer"""
    department_name = serializers.CharField(source='department.name', read_only=True)
    teacher_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = '__all__'
    
    def get_teacher_count(self, obj):
        return obj.teachers.count()


class StudentSerializer(serializers.ModelSerializer):
    """Student serializer"""
    user = UserSerializer()
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    parent_name = serializers.CharField(source='parent_guardian.get_full_name', read_only=True)
    attendance_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Student
        fields = '__all__'
    
    def get_attendance_percentage(self, obj):
        # Calculate attendance percentage for current month
        from django.utils import timezone
        from datetime import datetime
        from django.db.models import Count
        
        current_month = timezone.now().replace(day=1)
        total_sessions = AttendanceRecord.objects.filter(
            student=obj,
            session__session_date__gte=current_month
        ).count()
        
        if total_sessions == 0:
            return 100.0
            
        present_sessions = AttendanceRecord.objects.filter(
            student=obj,
            session__session_date__gte=current_month,
            status__in=['present', 'late']
        ).count()
        
        return round((present_sessions / total_sessions) * 100, 2)
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user_data['role'] = 'student'
        user = UserSerializer().create(user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        return super().update(instance, validated_data)


class TeacherSerializer(serializers.ModelSerializer):
    """Teacher serializer"""
    user = UserSerializer()
    department_name = serializers.CharField(source='department.name', read_only=True)
    subject_names = serializers.StringRelatedField(source='subjects', many=True, read_only=True)
    classes_teaching = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = '__all__'
    
    def get_classes_teaching(self, obj):
        return [cls.name for cls in obj.teaching_classes.all()]
    
    def create(self, validated_data):
        user_data = validated_data.pop('user')
        subjects_data = validated_data.pop('subjects', [])
        user_data['role'] = 'teacher'
        user = UserSerializer().create(user_data)
        teacher = Teacher.objects.create(user=user, **validated_data)
        teacher.subjects.set(subjects_data)
        return teacher

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        subjects_data = validated_data.pop('subjects', None)
        
        if user_data:
            user_serializer = UserSerializer(instance.user, data=user_data, partial=True)
            user_serializer.is_valid(raise_exception=True)
            user_serializer.save()
        
        if subjects_data is not None:
            instance.subjects.set(subjects_data)
        
        return super().update(instance, validated_data)


class FaceEncodingSerializer(serializers.ModelSerializer):
    """Face encoding serializer"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    algorithm_display = serializers.CharField(source='get_algorithm_display', read_only=True)
    
    class Meta:
        model = FaceEncoding
        fields = '__all__'
        extra_kwargs = {
            'encoding_data': {'write_only': True}
        }


class FaceEncodingCreateSerializer(serializers.ModelSerializer):
    """Face encoding creation with image upload"""
    face_image_base64 = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = FaceEncoding
        fields = [
            'student', 'algorithm', 'confidence_threshold', 
            'face_image_base64', 'encoding_data'
        ]
    
    def create(self, validated_data):
        face_image_base64 = validated_data.pop('face_image_base64', None)
        
        if face_image_base64:
            # Decode base64 image and save
            format, imgstr = face_image_base64.split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(
                base64.b64decode(imgstr),
                name=f"face_{validated_data['student'].student_id}_{validated_data['algorithm']}.{ext}"
            )
            # Save image path
            validated_data['face_image_path'] = f"face_images/{image.name}"
        
        return super().create(validated_data)


class AttendanceSessionSerializer(serializers.ModelSerializer):
    """Attendance session serializer"""
    class_name = serializers.CharField(source='class_assigned.name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    teacher_name = serializers.CharField(source='teacher.user.get_full_name', read_only=True)
    attendance_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = AttendanceSession
        fields = '__all__'
    
    def get_attendance_percentage(self, obj):
        if obj.total_students == 0:
            return 0.0
        return round((obj.present_count / obj.total_students) * 100, 2)


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """Attendance record serializer"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    class_name = serializers.CharField(source='session.class_assigned.name', read_only=True)
    subject_name = serializers.CharField(source='session.subject.name', read_only=True)
    session_date = serializers.DateField(source='session.session_date', read_only=True)
    
    class Meta:
        model = AttendanceRecord
        fields = '__all__'


class AttendanceRecordCreateSerializer(serializers.ModelSerializer):
    """Attendance record creation serializer"""
    face_image_base64 = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = AttendanceRecord
        fields = [
            'session', 'student', 'status', 'detection_method', 'algorithm_used',
            'confidence_score', 'check_in_time', 'notes', 'face_image_base64'
        ]
    
    def create(self, validated_data):
        face_image_base64 = validated_data.pop('face_image_base64', None)
        
        if face_image_base64:
            # Decode base64 image and save
            format, imgstr = face_image_base64.split(';base64,')
            ext = format.split('/')[-1]
            image = ContentFile(
                base64.b64decode(imgstr),
                name=f"attendance_{validated_data['student'].student_id}_{validated_data['session'].session_date}.{ext}"
            )
            validated_data['face_image_captured'] = image
        
        return super().create(validated_data)


class AttendanceAlertSerializer(serializers.ModelSerializer):
    """Attendance alert serializer"""
    student_name = serializers.CharField(source='student.user.get_full_name', read_only=True)
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    
    class Meta:
        model = AttendanceAlert
        fields = '__all__'


class AttendanceReportSerializer(serializers.ModelSerializer):
    """Attendance report serializer"""
    generated_by_name = serializers.CharField(source='generated_by.get_full_name', read_only=True)
    class_name = serializers.CharField(source='class_filter.name', read_only=True)
    student_name = serializers.CharField(source='student_filter.user.get_full_name', read_only=True)
    
    class Meta:
        model = AttendanceReport
        fields = '__all__'


class SystemConfigurationSerializer(serializers.ModelSerializer):
    """System configuration serializer"""
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = SystemConfiguration
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'


# Dashboard and Analytics Serializers

class DashboardStatsSerializer(serializers.Serializer):
    """Dashboard statistics serializer"""
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_classes = serializers.IntegerField()
    total_subjects = serializers.IntegerField()
    today_attendance_rate = serializers.FloatField()
    this_week_attendance_rate = serializers.FloatField()
    this_month_attendance_rate = serializers.FloatField()
    pending_alerts = serializers.IntegerField()
    active_sessions = serializers.IntegerField()
    low_attendance_students = serializers.IntegerField()


class AttendanceTrendSerializer(serializers.Serializer):
    """Attendance trend data serializer"""
    date = serializers.DateField()
    present_count = serializers.IntegerField()
    absent_count = serializers.IntegerField()
    late_count = serializers.IntegerField()
    attendance_rate = serializers.FloatField()


class ClassAttendanceStatsSerializer(serializers.Serializer):
    """Class-wise attendance statistics"""
    class_id = serializers.UUIDField()
    class_name = serializers.CharField()
    total_students = serializers.IntegerField()
    present_today = serializers.IntegerField()
    absent_today = serializers.IntegerField()
    attendance_rate = serializers.FloatField()


class StudentAttendanceSummarySerializer(serializers.Serializer):
    """Student attendance summary"""
    student_id = serializers.CharField()
    student_name = serializers.CharField()
    class_name = serializers.CharField()
    total_sessions = serializers.IntegerField()
    present_sessions = serializers.IntegerField()
    absent_sessions = serializers.IntegerField()
    late_sessions = serializers.IntegerField()
    attendance_percentage = serializers.FloatField()
    last_attendance = serializers.DateTimeField()


class FaceRecognitionResultSerializer(serializers.Serializer):
    """Face recognition result serializer"""
    student_id = serializers.CharField()
    student_name = serializers.CharField()
    algorithm_used = serializers.CharField()
    confidence_score = serializers.FloatField()
    detection_time = serializers.DateTimeField()
    face_coordinates = serializers.JSONField()
    status = serializers.CharField()
    message = serializers.CharField()


class BulkAttendanceSerializer(serializers.Serializer):
    """Bulk attendance upload serializer"""
    session_id = serializers.UUIDField()
    attendance_data = serializers.ListField(
        child=serializers.DictField(),
        allow_empty=False
    )
    
    def validate_attendance_data(self, value):
        required_fields = ['student_id', 'status']
        for record in value:
            if not all(field in record for field in required_fields):
                raise serializers.ValidationError(
                    f"Each record must contain: {', '.join(required_fields)}"
                )
        return value


class ReportGenerationSerializer(serializers.Serializer):
    """Report generation request serializer"""
    report_type = serializers.ChoiceField(choices=AttendanceReport.REPORT_TYPE_CHOICES)
    format = serializers.ChoiceField(choices=AttendanceReport.REPORT_FORMAT_CHOICES)
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    class_filter = serializers.UUIDField(required=False, allow_null=True)
    student_filter = serializers.UUIDField(required=False, allow_null=True)
    include_charts = serializers.BooleanField(default=True)
    include_summary = serializers.BooleanField(default=True)
    
    def validate(self, attrs):
        if attrs['date_from'] > attrs['date_to']:
            raise serializers.ValidationError("Start date must be before end date")
        return attrs


class NotificationSettingsSerializer(serializers.Serializer):
    """Notification settings serializer"""
    email_notifications = serializers.BooleanField(default=True)
    sms_notifications = serializers.BooleanField(default=False)
    push_notifications = serializers.BooleanField(default=True)
    absence_threshold = serializers.IntegerField(min_value=1, max_value=10, default=3)
    low_attendance_threshold = serializers.FloatField(min_value=0.0, max_value=100.0, default=75.0)
    notification_time = serializers.TimeField(default='09:00:00')


class FaceDetectionConfigSerializer(serializers.Serializer):
    """Face detection configuration serializer"""
    algorithm = serializers.ChoiceField(choices=FaceEncoding.ALGORITHM_CHOICES)
    confidence_threshold = serializers.FloatField(min_value=0.1, max_value=1.0, default=0.6)
    detection_interval = serializers.IntegerField(min_value=1, max_value=60, default=5)
    max_faces_per_frame = serializers.IntegerField(min_value=1, max_value=50, default=10)
    face_size_threshold = serializers.IntegerField(min_value=20, max_value=500, default=50)
    is_enabled = serializers.BooleanField(default=True)


class AttendanceExportSerializer(serializers.Serializer):
    """Attendance export serializer"""
    export_format = serializers.ChoiceField(choices=['csv', 'excel', 'pdf'])
    date_range = serializers.ChoiceField(choices=['today', 'week', 'month', 'custom'])
    class_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True
    )
    include_photos = serializers.BooleanField(default=False)
    include_analytics = serializers.BooleanField(default=True)


class ParentDashboardSerializer(serializers.Serializer):
    """Parent dashboard data serializer"""
    children = StudentAttendanceSummarySerializer(many=True)
    recent_alerts = AttendanceAlertSerializer(many=True)
    upcoming_events = serializers.ListField(child=serializers.DictField())
    monthly_summary = serializers.DictField()


class TeacherDashboardSerializer(serializers.Serializer):
    """Teacher dashboard data serializer"""
    classes_today = AttendanceSessionSerializer(many=True)
    attendance_overview = ClassAttendanceStatsSerializer(many=True)
    pending_sessions = AttendanceSessionSerializer(many=True)
    recent_activities = serializers.ListField(child=serializers.DictField())


class AdminDashboardSerializer(serializers.Serializer):
    """Admin dashboard data serializer"""
    system_stats = DashboardStatsSerializer()
    attendance_trends = AttendanceTrendSerializer(many=True)
    class_performance = ClassAttendanceStatsSerializer(many=True)
    recent_alerts = AttendanceAlertSerializer(many=True)
    system_health = serializers.DictField()


# Utility Serializers

class TimeRangeSerializer(serializers.Serializer):
    """Time range serializer for filtering"""
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    start_time = serializers.TimeField(required=False)
    end_time = serializers.TimeField(required=False)


class FilterSerializer(serializers.Serializer):
    """Generic filter serializer"""
    class_id = serializers.UUIDField(required=False, allow_null=True)
    student_id = serializers.UUIDField(required=False, allow_null=True)
    teacher_id = serializers.UUIDField(required=False, allow_null=True)
    subject_id = serializers.UUIDField(required=False, allow_null=True)
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    status = serializers.ChoiceField(
        choices=AttendanceRecord.STATUS_CHOICES,
        required=False
    )
    detection_method = serializers.ChoiceField(
        choices=AttendanceRecord.DETECTION_METHOD_CHOICES,
        required=False
    )


class BatchOperationSerializer(serializers.Serializer):
    """Batch operation serializer"""
    operation = serializers.ChoiceField(choices=['update', 'delete', 'export'])
    ids = serializers.ListField(child=serializers.UUIDField(), allow_empty=False)
    data = serializers.DictField(required=False)


class APIResponseSerializer(serializers.Serializer):
    """Standard API response serializer"""
    success = serializers.BooleanField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False)
    errors = serializers.DictField(required=False)
    meta = serializers.DictField(required=False)