from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, SupplierViewSet, ProductViewSet,
    StockEntryViewSet, StockMovementViewSet
)

# Create router and register viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'products', ProductViewSet)
router.register(r'stock-entries', StockEntryViewSet)
router.register(r'stock-movements', StockMovementViewSet)



urlpatterns = [
    path('api/v1/', include(router.urls)),
]