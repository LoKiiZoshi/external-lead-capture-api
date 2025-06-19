from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, ReportCategoryViewSet, ReportCommentViewSet, ReportAttachmentViewSet, ReportStatusViewSet, ReportProgressViewSet, report_summary, category_report_count, recent_comments, recent_attachments, status_progress, report_details

router = DefaultRouter()
router.register(r'reports', ReportViewSet)
router.register(r'categories', ReportCategoryViewSet)
router.register(r'comments', ReportCommentViewSet)
router.register(r'attachments', ReportAttachmentViewSet)
router.register(r'statuses', ReportStatusViewSet)
router.register(r'progress', ReportProgressViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('summary/', report_summary, name='report_summary'),
    path('category-count/<int:category_id>/', category_report_count, name='category_report_count'),
    path('recent-comments/', recent_comments, name='recent_comments'),
    path('recent-attachments/', recent_attachments, name='recent_attachments'),
    path('status-progress/<int:status_id>/', status_progress, name='status_progress'),
    path('report/<int:report_id>/', report_details, name='report_details'),
] 