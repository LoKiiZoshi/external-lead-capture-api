from rest_framework import serializers
from .models import Lead, Inquiry

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
        return inquiry