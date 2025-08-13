from django.contrib import admin
from .models import (
    User, School, Department, Class, Student, Teacher, Subject,
    FaceEncoding, AttendanceSession, AttendanceRecord, AttendanceAlert,
    AttendanceReport, SystemConfiguration, AuditLog
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_active_student', 'created_at')
    search_fields = ('username', 'email', 'role')
    list_filter = ('role', 'is_active_student', 'created_at')
    ordering = ('-created_at',)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('name', 'principal_name', 'established_date')
    search_fields = ('name', 'principal_name')


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'school', 'head_of_department')
    search_fields = ('name', 'code')
    list_filter = ('school',)


@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ('name', 'grade_level', 'section', 'academic_year', 'department')
    list_filter = ('grade_level', 'academic_year', 'department')
    search_fields = ('name',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'class_assigned', 'roll_number')
    list_filter = ('class_assigned',)
    search_fields = ('student_id', 'user__username', 'user__first_name', 'user__last_name')


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'user', 'department', 'join_date')
    search_fields = ('employee_id', 'user__username')
    list_filter = ('department',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'credits')
    search_fields = ('code', 'name')
    list_filter = ('department',)


@admin.register(FaceEncoding)
class FaceEncodingAdmin(admin.ModelAdmin):
    list_display = ('student', 'algorithm', 'is_active')
    list_filter = ('algorithm', 'is_active')
    search_fields = ('student__student_id',)


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('class_assigned', 'subject', 'teacher', 'session_date', 'status')
    list_filter = ('status', 'session_date')
    search_fields = ('class_assigned__name', 'subject__name')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'status', 'detection_method', 'confidence_score')
    list_filter = ('status', 'detection_method')
    search_fields = ('student__student_id',)


@admin.register(AttendanceAlert)
class AttendanceAlertAdmin(admin.ModelAdmin):
    list_display = ('student', 'alert_type', 'status', 'created_at')
    list_filter = ('alert_type', 'status')
    search_fields = ('student__student_id',)


@admin.register(AttendanceReport)
class AttendanceReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'report_type', 'format', 'date_from', 'date_to', 'generated_by')
    list_filter = ('report_type', 'format')
    search_fields = ('title',)


@admin.register(SystemConfiguration)
class SystemConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('key',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'model_name', 'timestamp')
    list_filter = ('action', 'model_name')
    search_fields = ('user__username', 'model_name')
    readonly_fields = ('changes',)
