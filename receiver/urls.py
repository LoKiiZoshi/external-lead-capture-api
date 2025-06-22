from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import InquiryViewSet, receiver_list

router = DefaultRouter()
router.register(r'inquiries', InquiryViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('receiver-list/', receiver_list, name='receiver_list'),
]




