import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
import json


class User(AbstractUser):
    """Extended User model with role-based access"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('parent', 'Parent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number format: '+999999999'")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    emergency_contact = models.CharField(max_length=17, blank=True)
    is_active_student = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['is_active_student']),
        ]


class School(models.Model):
    """School information model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    address = models.TextField()
    phone_number = models.CharField(max_length=17)
    email = models.EmailField()
    established_date = models.DateField()
    principal_name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='school/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'schools'

    def __str__(self):
        return self.name


class Department(models.Model):
    """Department/Faculty model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    head_of_department = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Class(models.Model):
    """Class/Grade model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes')
    name = models.CharField(max_length=50)  # e.g., "Grade 10A", "Class XII-B"
    grade_level = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])
    section = models.CharField(max_length=10)  # A, B, C, etc.
    class_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='teaching_classes')
    room_number = models.CharField(max_length=20, blank=True)
    capacity = models.IntegerField(default=30)
    academic_year = models.CharField(max_length=9)  # e.g., "2024-2025"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'classes'
        unique_together = ['department', 'grade_level', 'section', 'academic_year']

    def __str__(self):
        return f"{self.name} - {self.academic_year}"


class Student(models.Model):
    """Student profile model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='students')
    roll_number = models.CharField(max_length=10)
    admission_date = models.DateField()
    blood_group = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True)
    parent_guardian = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'students'
        unique_together = ['class_assigned', 'roll_number']
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['class_assigned']),
        ]

    def __str__(self):
        return f"{self.student_id} - {self.user.get_full_name()}"


class Teacher(models.Model):
    """Teacher profile model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers')
    subjects = models.ManyToManyField('Subject', related_name='teachers')
    qualification = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    join_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'teachers'

    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"


class Subject(models.Model):
    """Subject model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='subjects')
    credits = models.IntegerField(default=1)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'subjects'

    def __str__(self):
        return f"{self.code} - {self.name}"


class FaceEncoding(models.Model):
    """Face encoding storage for recognition algorithms"""
    ALGORITHM_CHOICES = [
        ('haar_cascade', 'Haar Cascade Classifier'),
        ('hog', 'Histogram of Oriented Gradients'),
        ('lbph', 'Local Binary Pattern Histogram'),
        ('eigenfaces', 'Eigenfaces (PCA)'),
        ('fisherfaces', 'Fisherfaces (LDA)'),
        ('mtcnn', 'Multi-task CNN (MTCNN)'),
        ('facenet', 'DeepFace/FaceNet Embeddings'),
        ('dlib_cnn', 'Dlib CNN-based Recognition'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='face_encodings')
    algorithm = models.CharField(max_length=20, choices=ALGORITHM_CHOICES)
    encoding_data = models.TextField()  # JSON serialized encoding data
    confidence_threshold = models.FloatField(default=0.6)
    face_image_path = models.CharField(max_length=500)  # Path to training image
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'face_encodings'
        unique_together = ['student', 'algorithm']
        indexes = [
            models.Index(fields=['student', 'algorithm']),
            models.Index(fields=['is_active']),
        ]

    def get_encoding_array(self):
        """Convert JSON string back to numpy array"""
        return json.loads(self.encoding_data)

    def set_encoding_array(self, encoding_array):
        """Convert numpy array to JSON string"""
        self.encoding_data = json.dumps(encoding_array.tolist())

    def __str__(self):
        return f"{self.student.student_id} - {self.get_algorithm_display()}"


class AttendanceSession(models.Model):
    """Attendance session model for each class period"""
    SESSION_STATUS_CHOICES = [
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE, related_name='attendance_sessions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='attendance_sessions')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='attendance_sessions')
    session_date = models.DateField(default=timezone.now)
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, choices=SESSION_STATUS_CHOICES, default='active')
    total_students = models.IntegerField(default=0)
    present_count = models.IntegerField(default=0)
    absent_count = models.IntegerField(default=0)
    late_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_sessions'
        indexes = [
            models.Index(fields=['session_date']),
            models.Index(fields=['class_assigned', 'session_date']),
        ]

    def __str__(self):
        return f"{self.class_assigned.name} - {self.subject.name} - {self.session_date}"


class AttendanceRecord(models.Model):
    """Individual attendance record"""
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('excused', 'Excused'),
    ]
    
    DETECTION_METHOD_CHOICES = [
        ('face_recognition', 'Face Recognition'),
        ('manual', 'Manual Entry'),
        ('rfid', 'RFID Card'),
        ('qr_code', 'QR Code'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='attendance_records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='absent')
    detection_method = models.CharField(max_length=20, choices=DETECTION_METHOD_CHOICES, default='face_recognition')
    algorithm_used = models.CharField(max_length=20, choices=FaceEncoding.ALGORITHM_CHOICES, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    check_in_time = models.DateTimeField(null=True, blank=True)
    face_image_captured = models.ImageField(upload_to='attendance_captures/', null=True, blank=True)
    notes = models.TextField(blank=True)
    marked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'attendance_records'
        unique_together = ['session', 'student']
        indexes = [
            models.Index(fields=['session', 'status']),
            models.Index(fields=['student', 'created_at']),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.session.session_date} - {self.status}"


class AttendanceAlert(models.Model):
    """Attendance alerts and notifications"""
    ALERT_TYPE_CHOICES = [
        ('absence', 'Student Absence'),
        ('late', 'Late Arrival'),
        ('consecutive_absence', 'Consecutive Absences'),
        ('low_attendance', 'Low Attendance Rate'),
        ('system_error', 'System Error'),
    ]
    
    NOTIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('acknowledged', 'Acknowledged'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    message = models.TextField()
    recipients = models.JSONField(default=list)  # List of email/phone numbers
    notification_channels = models.JSONField(default=list)  # ['email', 'sms', 'push']
    status = models.CharField(max_length=15, choices=NOTIFICATION_STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_alerts'
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['student', 'alert_type']),
        ]

    def __str__(self):
        return f"{self.student.student_id} - {self.get_alert_type_display()}"


class AttendanceReport(models.Model):
    """Generated attendance reports"""
    REPORT_TYPE_CHOICES = [
        ('daily', 'Daily Report'),
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('semester', 'Semester Report'),
        ('annual', 'Annual Report'),
        ('custom', 'Custom Period Report'),
    ]
    
    REPORT_FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES)
    format = models.CharField(max_length=10, choices=REPORT_FORMAT_CHOICES, default='pdf')
    class_filter = models.ForeignKey(Class, on_delete=models.CASCADE, null=True, blank=True)
    student_filter = models.ForeignKey(Student, on_delete=models.CASCADE, null=True, blank=True)
    date_from = models.DateField()
    date_to = models.DateField()
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_reports')
    file_path = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict)  # Additional filter parameters
    total_records = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_reports'
        indexes = [
            models.Index(fields=['generated_by', 'created_at']),
            models.Index(fields=['report_type', 'date_from']),
        ]

    def __str__(self):
        return f"{self.title} - {self.created_at.date()}"


class SystemConfiguration(models.Model):
    """System configuration and settings"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='general')
    is_active = models.BooleanField(default=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'system_configurations'

    def __str__(self):
        return f"{self.key}: {self.value}"


class AuditLog(models.Model):
    """System audit log for tracking changes"""
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('attendance_mark', 'Attendance Marked'),
        ('report_generate', 'Report Generated'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=50)
    object_id = models.UUIDField(null=True, blank=True)
    changes = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'audit_logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"