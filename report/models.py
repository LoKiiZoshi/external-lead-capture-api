from django.db import models

class ReportCategory(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Report(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(ReportCategory, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class ReportComment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class ReportAttachment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class ReportStatus(models.Model):
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class ReportProgress(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    status = models.ForeignKey(ReportStatus, on_delete=models.CASCADE)
    progress_date = models.DateTimeField(auto_now_add=True)