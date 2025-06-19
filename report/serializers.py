from rest_framework import serializers
from .models import Report, ReportCategory, ReportComment, ReportAttachment, ReportStatus, ReportProgress

class ReportCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportCategory
        fields = '__all__'

class ReportCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportComment
        fields = '__all__'

class ReportAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportAttachment
        fields = '__all__'

class ReportStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportStatus
        fields = '__all__'

class ReportProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportProgress
        fields = '__all__'

class ReportSerializer(serializers.ModelSerializer):
    comments = ReportCommentSerializer(many=True, read_only=True)
    attachments = ReportAttachmentSerializer(many=True, read_only=True)
    progress = ReportProgressSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = '__all__'