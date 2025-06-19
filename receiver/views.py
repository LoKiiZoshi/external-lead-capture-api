from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from .models import Inquiry
from .serializers import InquirySerializer
from django.shortcuts import render

class InquiryViewSet(viewsets.ModelViewSet):
    queryset = Inquiry.objects.all()
    serializer_class = InquirySerializer
    permission_classes = [AllowAny]  # Restrict in production
    http_method_names = ['get', 'post']  # Only allow GET and POST

def receiver_list(request):
    inquiries = Inquiry.objects.all()
    return render(request, 'receiver_list.html', {'inquiries': inquiries})