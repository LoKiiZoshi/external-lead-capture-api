from rest_framework import viewsets, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Report, ReportCategory, ReportComment, ReportAttachment, ReportStatus, ReportProgress
from .serializers import ReportSerializer, ReportCategorySerializer, ReportCommentSerializer, ReportAttachmentSerializer, ReportStatusSerializer, ReportProgressSerializer

class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer

class ReportCategoryViewSet(viewsets.ModelViewSet):
    queryset = ReportCategory.objects.all()
    serializer_class = ReportCategorySerializer

class ReportCommentViewSet(viewsets.ModelViewSet):
    queryset = ReportComment.objects.all()
    serializer_class = ReportCommentSerializer

class ReportAttachmentViewSet(viewsets.ModelViewSet):
    queryset = ReportAttachment.objects.all()
    serializer_class = ReportAttachmentSerializer

class ReportStatusViewSet(viewsets.ModelViewSet):
    queryset = ReportStatus.objects.all()
    serializer_class = ReportStatusSerializer

class ReportProgressViewSet(viewsets.ModelViewSet):
    queryset = ReportProgress.objects.all()
    serializer_class = ReportProgressSerializer

@api_view(['GET'])
def report_summary(request):
    total_reports = Report.objects.count()
    return Response({"total_reports": total_reports})

@api_view(['GET'])
def category_report_count(request, category_id):
    count = Report.objects.filter(category_id=category_id).count()
    return Response({"category_id": category_id, "report_count": count})

@api_view(['GET'])
def recent_comments(request):
    comments = ReportComment.objects.order_by('-created_at')[:5]
    serializer = ReportCommentSerializer(comments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def recent_attachments(request):
    attachments = ReportAttachment.objects.order_by('-uploaded_at')[:5]
    serializer = ReportAttachmentSerializer(attachments, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def status_progress(request, status_id):
    progress = ReportProgress.objects.filter(status_id=status_id)
    serializer = ReportProgressSerializer(progress, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def report_details(request, report_id):
    try:
        report = Report.objects.get(id=report_id)
        serializer = ReportSerializer(report)
        return Response(serializer.data)
    except Report.DoesNotExist:
        return Response({"error": "Report not found"}, status=404)