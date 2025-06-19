from django.db import models

class Lead(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Inquiry(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='inquiries')
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inquiry by {self.lead.name}"