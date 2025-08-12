from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from django.core.files.base import ContentFile
import base64
import cv2
import numpy as np
import face_recognition
import dlib
import json
from PIL import Image
import io

from .models import (
    User, School, Department, Class, Student, Teacher, Subject,
    FaceEncoding, AttendanceSession, AttendanceRecord, AttendanceAlert,
    AttendanceReport, SystemConfiguration, AuditLog
)
from .serializers import (
    UserSerializer, LoginSerializer, SchoolSerializer, DepartmentSerializer,
    ClassSerializer, StudentSerializer, TeacherSerializer, SubjectSerializer,
    FaceEncodingSerializer, FaceEncodingCreateSerializer, AttendanceSessionSerializer,
    AttendanceRecordSerializer, AttendanceRecordCreateSerializer, AttendanceAlertSerializer,
    AttendanceReportSerializer, SystemConfigurationSerializer, AuditLogSerializer,
    DashboardStatsSerializer, AttendanceTrendSerializer, FaceRecognitionResultSerializer,
    BulkAttendanceSerializer, ReportGenerationSerializer, AttendanceExportSerializer
)
from .face_recognition_algorithms import FaceRecognitionManager


class UserViewSet(viewsets.ModelViewSet):
    """User management viewset"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = User.objects.all()
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        return queryset

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """Get current user profile"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put'])
    def update_profile(self, request):
        """Update current user profile"""
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SchoolViewSet(viewsets.ModelViewSet):
    """School management viewset"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]


class DepartmentViewSet(viewsets.ModelViewSet):
    """Department management viewset"""
    queryset = Department.objects.all().select_related('school', 'head_of_department')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Department.objects.all().select_related('school', 'head_of_department')
        school_id = self.request.query_params.get('school_id', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        return queryset


class ClassViewSet(viewsets.ModelViewSet):
    """Class management viewset"""
    queryset = Class.objects.all().select_related('department', 'class_teacher')
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Class.objects.all().select_related('department', 'class_teacher')
        department_id = self.request.query_params.get('department_id', None)
        academic_year = self.request.query_params.get('academic_year', None)
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if academic_year:
            queryset = queryset.filter(academic_year=academic_year)
        return queryset

    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        """Get all students in a class"""
        class_obj = self.get_object()
        students = class_obj.students.filter(user__is_active_student=True)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendance_stats(self, request, pk=None):
        """Get attendance statistics for a class"""
        class_obj = self.get_object()
        date_from = request.query_params.get('date_from', timezone.now().replace(day=1).date())
        date_to = request.query_params.get('date_to', timezone.now().date())
        
        sessions = AttendanceSession.objects.filter(
            class_assigned=class_obj,
            session_date__range=[date_from, date_to]
        )
        
        stats = {
            'total_sessions': sessions.count(),
            'total_students': class_obj.students.filter(user__is_active_student=True).count(),
            'average_attendance': sessions.aggregate(avg=Avg('present_count'))['avg'] or 0,
            'attendance_trend': []
        }
        
        # Get daily attendance trend
        for session in sessions.order_by('session_date'):
            stats['attendance_trend'].append({
                'date': session.session_date,
                'present': session.present_count,
                'absent': session.absent_count,
                'rate': (session.present_count / session.total_students * 100) if session.total_students > 0 else 0
            })
        
        return Response(stats)


class SubjectViewSet(viewsets.ModelViewSet):
    """Subject management viewset"""
    queryset = Subject.objects.all().select_related('department')
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Subject.objects.all().select_related('department')
        department_id = self.request.query_params.get('department_id', None)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        return queryset


class StudentViewSet(viewsets.ModelViewSet):
    """Student management viewset"""
    queryset = Student.objects.all().select_related('user', 'class_assigned', 'parent_guardian')
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Student.objects.all().select_related('user', 'class_assigned', 'parent_guardian')
        class_id = self.request.query_params.get('class_id', None)
        active_only = self.request.query_params.get('active_only', 'true').lower() == 'true'
        
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        if active_only:
            queryset = queryset.filter(user__is_active_student=True)
        return queryset

    @action(detail=True, methods=['get'])
    def attendance_history(self, request, pk=None):
        """Get attendance history for a student"""
        student = self.get_object()
        date_from = request.query_params.get('date_from', (timezone.now() - timedelta(days=30)).date())
        date_to = request.query_params.get('date_to', timezone.now().date())
        
        records = AttendanceRecord.objects.filter(
            student=student,
            session__session_date__range=[date_from, date_to]
        ).select_related('session__subject', 'session__class_assigned')
        
        serializer = AttendanceRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_face_images(self, request, pk=None):
        """Upload multiple face images for training"""
        student = self.get_object()
        images = request.FILES.getlist('images')
        algorithms = request.data.getlist('algorithms', [])
        
        if not images:
            return Response({'error': 'No images provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        face_manager = FaceRecognitionManager()
        results = []
        
        for image in images:
            for algorithm in algorithms:
                try:
                    # Process image and create encoding
                    encoding = face_manager.create_face_encoding(image, algorithm)
                    if encoding is not None:
                        face_encoding = FaceEncoding.objects.create(
                            student=student,
                            algorithm=algorithm,
                            encoding_data=json.dumps(encoding.tolist()),
                            face_image_path=f"face_images/{student.student_id}_{algorithm}_{image.name}"
                        )
                        results.append({
                            'algorithm': algorithm,
                            'status': 'success',
                            'encoding_id': face_encoding.id
                        })
                    else:
                        results.append({
                            'algorithm': algorithm,
                            'status': 'failed',
                            'error': 'Could not detect face in image'
                        })
                except Exception as e:
                    results.append({
                        'algorithm': algorithm,
                        'status': 'error',
                        'error': str(e)
                    })
        
        return Response({'results': results})


class TeacherViewSet(viewsets.ModelViewSet):
    """Teacher management viewset"""
    queryset = Teacher.objects.all().select_related('user', 'department').prefetch_related('subjects')
    serializer_class = TeacherSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Teacher.objects.all().select_related('user', 'department').prefetch_related('subjects')
        department_id = self.request.query_params.get('department_id', None)
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        return queryset

    @action(detail=True, methods=['get'])
    def classes_teaching(self, request, pk=None):
        """Get classes taught by teacher"""
        teacher = self.get_object()
        classes = teacher.teaching_classes.all()
        serializer = ClassSerializer(classes, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attendance_sessions(self, request, pk=None):
        """Get attendance sessions conducted by teacher"""
        teacher = self.get_object()
        date_from = request.query_params.get('date_from', timezone.now().date())
        date_to = request.query_params.get('date_to', timezone.now().date())
        
        sessions = AttendanceSession.objects.filter(
            teacher=teacher,
            session_date__range=[date_from, date_to]
        ).select_related('class_assigned', 'subject')
        
        serializer = AttendanceSessionSerializer(sessions, many=True)
        return Response(serializer.data)


class FaceEncodingViewSet(viewsets.ModelViewSet):
    """Face encoding management viewset"""
    queryset = FaceEncoding.objects.all().select_related('student')
    serializer_class = FaceEncodingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = FaceEncoding.objects.all().select_related('student')
        student_id = self.request.query_params.get('student_id', None)
        algorithm = self.request.query_params.get('algorithm', None)
        active_only = self.request.query_params.get('active_only', 'true').lower() == 'true'
        
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        if algorithm:
            queryset = queryset.filter(algorithm=algorithm)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_serializer_class(self):
        if self.action == 'create':
            return FaceEncodingCreateSerializer
        return FaceEncodingSerializer

    @action(detail=False, methods=['post'])
    def bulk_train(self, request):
        """Bulk train face encodings for multiple students"""
        student_ids = request.data.get('student_ids', [])
        algorithms = request.data.get('algorithms', [])
        
        if not student_ids or not algorithms:
            return Response(
                {'error': 'student_ids and algorithms are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        face_manager = FaceRecognitionManager()
        results = []
        
        for student_id in student_ids:
            try:
                student = Student.objects.get(id=student_id)
                for algorithm in algorithms:
                    # Check if encoding already exists
                    existing = FaceEncoding.objects.filter(student=student, algorithm=algorithm).first()
                    if existing:
                        results.append({
                            'student_id': str(student_id),
                            'algorithm': algorithm,
                            'status': 'skipped',
                            'message': 'Encoding already exists'
                        })
                        continue
                    
                    # Create new encoding (requires face images)
                    # This would be implemented based on your specific training process
                    results.append({
                        'student_id': str(student_id),
                        'algorithm': algorithm,
                        'status': 'pending',
                        'message': 'Training scheduled'
                    })
            except Student.DoesNotExist:
                results.append({
                    'student_id': str(student_id),
                    'algorithm': 'all',
                    'status': 'error',
                    'message': 'Student not found'
                })
        
        return Response({'results': results})


class AttendanceSessionViewSet(viewsets.ModelViewSet):
    """Attendance session management viewset"""
    queryset = AttendanceSession.objects.all().select_related('class_assigned', 'subject', 'teacher')
    serializer_class = AttendanceSessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AttendanceSession.objects.all().select_related('class_assigned', 'subject', 'teacher')
        class_id = self.request.query_params.get('class_id', None)
        teacher_id = self.request.query_params.get('teacher_id', None)
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        status = self.request.query_params.get('status', None)
        
        if class_id:
            queryset = queryset.filter(class_assigned_id=class_id)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        if date_from:
            queryset = queryset.filter(session_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(session_date__lte=date_to)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-session_date', '-start_time')

    @action(detail=True, methods=['post'])
    def start_session(self, request, pk=None):
        """Start attendance session"""
        session = self.get_object()
        if session.status != 'active':
            return Response(
                {'error': 'Session is not in active state'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initialize attendance records for all students in class
        students = session.class_assigned.students.filter(user__is_active_student=True)
        session.total_students = students.count()
        session.save()
        
        # Create attendance records with default 'absent' status
        for student in students:
            AttendanceRecord.objects.get_or_create(
                session=session,
                student=student,
                defaults={'status': 'absent'}
            )
        
        return Response({'message': 'Session started successfully'})

    @action(detail=True, methods=['post'])
    def complete_session(self, request, pk=None):
        """Complete attendance session"""
        session = self.get_object()
        session.status = 'completed'
        
        # Update session statistics
        records = session.attendance_records.all()
        session.present_count = records.filter(status__in=['present', 'late']).count()
        session.absent_count = records.filter(status='absent').count()
        session.late_count = records.filter(status='late').count()
        session.save()
        
        # Generate alerts for absent students
        absent_students = records.filter(status='absent')
        for record in absent_students:
            self.create_absence_alert(record.student, session)
        
        return Response({'message': 'Session completed successfully'})

    def create_absence_alert(self, student, session):
        """Create absence alert for student"""
        message = f"{student.user.get_full_name()} was absent from {session.subject.name} class on {session.session_date}"
        
        # Get parent contact info
        recipients = []
        if student.parent_guardian:
            if student.parent_guardian.email:
                recipients.append(student.parent_guardian.email)
            if student.parent_guardian.phone_number:
                recipients.append(student.parent_guardian.phone_number)
        
        AttendanceAlert.objects.create(
            student=student,
            alert_type='absence',
            message=message,
            recipients=recipients,
            notification_channels=['email', 'sms']
        )


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """Attendance record management viewset"""
    queryset = AttendanceRecord.objects.all().select_related('session', 'student', 'marked_by')
    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = AttendanceRecord.objects.all().select_related('session', 'student', 'marked_by')
        session_id = self.request.query_params.get('session_id', None)
    