from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Sum, Count
from django.utils import timezone
from .models import Category, Supplier, Product, StockEntry, StockMovement
from .serializers import (
    CategorySerializer, SupplierSerializer, ProductListSerializer,
    ProductDetailSerializer, StockEntrySerializer, StockMovementSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active categories"""
        active_categories = self.queryset.filter(status=Category.CategoryStatus.ACTIVE)
        serializer = self.get_serializer(active_categories, many=True)
        return Response(serializer.data)


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'contact_person', 'email']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active suppliers"""
        active_suppliers = self.queryset.filter(status=Supplier.SupplierStatus.ACTIVE)
        serializer = self.get_serializer(active_suppliers, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related('category', 'supplier')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'supplier', 'product_type', 'status']
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'sku', 'created_at', 'cost_per_unit']
    ordering = ['name']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get products with low stock levels"""
        products = []
        for product in self.queryset.filter(status=Product.ProductStatus.ACTIVE):
            if product.is_low_stock:
                products.append(product)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overstocked(self, request):
        """Get products that are overstocked"""
        products = []
        for product in self.queryset.filter(status=Product.ProductStatus.ACTIVE):
            if product.is_overstocked:
                products.append(product)
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stock_summary(self, request):
        """Get overall stock summary statistics"""
        total_products = self.queryset.filter(status=Product.ProductStatus.ACTIVE).count()
        low_stock_count = sum(1 for product in self.queryset.filter(status=Product.ProductStatus.ACTIVE) if product.is_low_stock)
        overstocked_count = sum(1 for product in self.queryset.filter(status=Product.ProductStatus.ACTIVE) if product.is_overstocked)
        out_of_stock_count = self.queryset.filter(status=Product.ProductStatus.OUT_OF_STOCK).count()
        
        return Response({
            'total_products': total_products,
            'low_stock_count': low_stock_count,
            'overstocked_count': overstocked_count,
            'out_of_stock_count': out_of_stock_count,
            'healthy_stock_count': total_products - low_stock_count - overstocked_count
        })


class StockEntryViewSet(viewsets.ModelViewSet):
    queryset = StockEntry.objects.select_related('product', 'product__category')
    serializer_class = StockEntrySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['product', 'status', 'entry_type']
    search_fields = ['product__name', 'product__sku', 'batch_number', 'reference_number']
    ordering_fields = ['received_date', 'expiry_date', 'quantity', 'created_at']
    ordering = ['-received_date']
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get stock entries expiring within 7 days"""
        from datetime import timedelta
        expiry_threshold = timezone.now().date() + timedelta(days=7)
        
        expiring_entries = self.queryset.filter(
            status=StockEntry.StockStatus.AVAILABLE,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=timezone.now().date()
        )
        
        page = self.paginate_queryset(expiring_entries)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(expiring_entries, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired stock entries"""
        expired_entries = self.queryset.filter(
            expiry_date__lt=timezone.now().date()
        )
        
        page = self.paginate_queryset(expired_entries)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(expired_entries, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = StockMovement.objects.select_related('stock_entry', 'stock_entry__product')
    serializer_class = StockMovementSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['movement_type', 'stock_entry__product']
    search_fields = ['stock_entry__product__name', 'reason', 'performed_by']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
