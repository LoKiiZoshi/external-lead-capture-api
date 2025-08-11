from django.shortcuts import render

# Create your views here.

from rest_framework import viewsets,status,permissions
from rest_framework.decorators import action,api_view,permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate,login,logout
from django.db.models import Q, Count, Avg , Sum
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

from .models import(User , School, Department,Class,Student,Teacher,Subject,FaceEncoding,
                    AttendanceSession,AttendanceRecord,AttendanceAlert,
                    AttendanceReport,SystemConfiguration, AuditLog)


from .serializers import(
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
        role = self.request.query_params.get('role',None)
        if role:
            queryset = queryset.filter(role=role)
            return queryset
        
@action(detail = False,methods=['get'])
def profile(self, request):
    """Get current user prfile"""
    serializer = self.get_serializer(request.user)
    return Response(serializer.data)

@action(detail= False,methods=['put'])
def update_profile(self,request):
    """Update current user profile"""
    serializer = self.get_serializer(request.user,data = request.data,partial = True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errrors,status= status.HTTP_400_BAD_REQUEST)

class SchoolViewSet(viewsets.ModelViewSet):
    """School management viewset"""
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
    
class DepartmentViewSet(viewsets.ModelViewSet):
    """Department management viewset"""
    queryset = Department.objects.all().select_related('school','head_of_department')
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    
   
    def get_queryset(self):
        queryset = Department.objects.all().select_related('school', 'head_of_department')
        school_id = self.request.query_params.get('school_id', None)
        if school_id:
            queryset = queryset.filter(school_id=school_id)
        return queryset
    
    
class ClassViewSet(viewsets.ModelViewSet):
    """class management viewset"""
    queryset = Class.objects.all().select_related('department','class_teacher')
    serializer_class = ClassSerializer
    permission_classes = [IsAuthenticated]
    
def get_queryset(self):
    queryset = Class.objects.all().select_related('department','class_teacher')
    department_id = self.request.query_params.get('department_id',None)
    academic_year = self.request.query_params.get('academic_year',None)
    
    if department_id:
        queryset = queryset.filter(department_id= department_id)
    if academic_year:queryset = queryset.filter(academic_year= academic_year)
    return queryset

@action(detail=True,methods=['get'])
def students(self,request,pk=None):
    """Get all student in a class"""
    class_obj = self.get_object()
    students = class_obj.student.filter(user_is_active_student = True)
    serializer = StudentSerializer(students,many=True)
    return Response(serializer.data)


@action(detail=True,methods=['get'])
def attendance_stats(self,request,pk = None):
    """Get attendance statistics for a class"""
    class_obj = self.get_object()
    date_from = request.query_params.get('date_from',timezone.now().replace(day=1).date())
    date_to = request.query_params.get('date_to',timezone.now().date())
    
    sessions = AttendanceSession.objects.filter(
        class_assigned = class_obj,
        session_date_range=[date_from,date_to]
        
    )
    
    stats = {
        'total_sessions':sessions.count(),
        'total_student':class_obj.student.filter(user_is_active_student=True).count(),
        'average_attendance': sessions.aggregate(avg = Avg('present_count'))
    }
    
    

    