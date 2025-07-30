from rest_framework import serializers
from .models import Category, Supplier, Product, StockEntry, StockMovement


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'description', 'status', 'products_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(status=Product.ProductStatus.ACTIVE).count()


class SupplierSerializer(serializers.ModelSerializer):
    products_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Supplier
        fields = [
            'id', 'name', 'contact_person', 'email', 'phone', 'address',
            'status', 'products_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_products_count(self, obj):
        return obj.products.filter(status=Product.ProductStatus.ACTIVE).count()


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    current_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_overstocked = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category_name', 'supplier_name',
            'product_type', 'unit_of_measure', 'cost_per_unit',
            'current_stock', 'minimum_stock_level', 'is_low_stock',
            'is_overstocked', 'status', 'created_at', 'updated_at'
        ]


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    supplier_name = serializers.CharField(source='supplier.name', read_only=True)
    current_stock = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_overstocked = serializers.ReadOnlyField()
    recent_stock_entries = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'supplier',
            'supplier_name', 'product_type', 'unit_of_measure', 'cost_per_unit',
            'minimum_stock_level', 'maximum_stock_level', 'shelf_life_days',
            'storage_instructions', 'description', 'status', 'current_stock',
            'is_low_stock', 'is_overstocked', 'recent_stock_entries',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_recent_stock_entries(self, obj):
        recent_entries = obj.stock_entries.filter(
            status=StockEntry.StockStatus.AVAILABLE
        )[:5]
        return StockEntrySerializer(recent_entries, many=True).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            'name', 'sku', 'category', 'supplier',
            'product_type', 'unit_of_measure', 'cost_per_unit',
            'minimum_stock_level', 'maximum_stock_level', 'shelf_life_days',
            'storage_instructions', 'description', 'status'
        ]


class StockEntrySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    unit_of_measure = serializers.CharField(source='product.unit_of_measure', read_only=True)
    total_cost = serializers.ReadOnlyField()
    is_expired = serializers.ReadOnlyField()
    days_until_expiry = serializers.ReadOnlyField()
    
    class Meta:
        model = StockEntry
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'batch_number',
            'quantity', 'unit_of_measure', 'entry_type', 'status',
            'received_date', 'expiry_date', 'cost_per_unit', 'total_cost',
            'reference_number', 'notes', 'is_expired', 'days_until_expiry',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class StockMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='stock_entry.product.name', read_only=True)
    product_sku = serializers.CharField(source='stock_entry.product.sku', read_only=True)
    
    class Meta:
        model = StockMovement
        fields = [
            'id', 'stock_entry', 'product_name', 'product_sku',
            'movement_type', 'quantity_changed', 'previous_quantity',
            'new_quantity', 'reason', 'performed_by', 'reference_document',
            'created_at'
        ]
        read_only_fields = ['created_at']
