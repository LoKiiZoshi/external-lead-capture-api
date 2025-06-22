from rest_framework import serializers
from .models import Lead, Inquiry
from django.core.mail import send_mail
from django.conf import settings



class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ['id', 'name', 'email', 'phone', 'created_at']
        
        
        

class InquirySerializer(serializers.ModelSerializer):
    lead = LeadSerializer()

    class Meta:
        model = Inquiry
        fields = ['id', 'lead', 'message', 'submitted_at']
        
        
        

    def create(self, validated_data):
        lead_data = validated_data.pop('lead')
        lead, _ = Lead.objects.get_or_create(
            email=lead_data['email'],
            defaults={
                'name': lead_data.get('name', 'Unknown'),
                'phone': lead_data.get('phone', '')
            }
        )
        inquiry = Inquiry.objects.create(lead=lead, **validated_data)

        # Send Thank You Email
        subject = "Thank You for Your Inquiry"
        message = f"""
Dear {lead.name},

Thank you for reaching out to us. We’ve received your message and our team will get back to you shortly.

Here’s what you sent:
---
{inquiry.message}
---

"Success is best when it's shared." – 

Best regards,  
The [ Echoinnovators Company] Team
"""
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [lead.email],
            fail_silently=False,
        )

        return inquiry
