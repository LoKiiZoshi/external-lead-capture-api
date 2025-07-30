from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Category, Supplier, Product, StockEntry, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'products_count', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    def products_count(self, obj):
        count = obj.products.filter(status=Product.ProductStatus.ACTIVE).count()
        url = reverse('admin:stockmanagement_product_changelist') + f'?category__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    products_count.short_description = 'Active Products'


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_person', 'email', 'phone', 'status', 'products_count']
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'contact_person', 'email']
    readonly_fields = ['created_at', 'updated_at']

    def products_count(self, obj):
        count = obj.products.filter(status=Product.ProductStatus.ACTIVE).count()
        url = reverse('admin:stockmanagement_product_changelist') + f'?supplier__id__exact={obj.id}'
        return format_html('<a href="{}">{} products</a>', url, count)
    products_count.short_description = 'Active Products'


class StockEntryInline(admin.TabularInline):
    model = StockEntry
    extra = 0
    fields = ['batch_number', 'quantity', 'status', 'expiry_date', 'cost_per_unit']
    readonly_fields = ['received_date']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'supplier', 'current_stock_display',
        'stock_status', 'product_type', 'status'
    ]
    list_filter = ['category', 'supplier', 'product_type', 'status', 'created_at']
    search_fields = ['name', 'sku', 'description']
    readonly_fields = ['created_at', 'updated_at', 'current_stock', 'is_low_stock', 'is_overstocked']
    inlines = [StockEntryInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'category', 'supplier', 'description')
        }),
        ('Product Details', {
            'fields': ('product_type', 'unit_of_measure', 'cost_per_unit')
        }),
        ('Stock Management', {
            'fields': ('minimum_stock_level', 'maximum_stock_level', 'current_stock', 'is_low_stock', 'is_overstocked')
        }),
        ('Storage & Expiry', {
            'fields': ('shelf_life_days', 'storage_instructions')
        }),
        ('Status & Timestamps', {
            'fields': ('status', 'created_at', 'updated_at')
        })
    )

    def current_stock_display(self, obj):
        stock = obj.current_stock
        return f"{stock} {obj.unit_of_measure}"
    current_stock_display.short_description = 'Current Stock'

    def stock_status(self, obj):
        if obj.is_low_stock:
            return format_html('<span style="color: red;">⚠️ Low Stock</span>')
        elif obj.is_overstocked:
            return format_html('<span style="color: orange;">📦 Overstocked</span>')
        else:
            return format_html('<span style="color: green;">✅ Normal</span>')
    stock_status.short_description = 'Stock Status'


@admin.register(StockEntry)
class StockEntryAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'quantity_display', 'status', 'entry_type',
        'expiry_status', 'received_date', 'total_cost_display'
    ]
    list_filter = ['status', 'entry_type', 'received_date', 'expiry_date']
    search_fields = ['product__name', 'product__sku', 'batch_number', 'reference_number']

    readonly_fields = [
        'created_at', 'updated_at', 'total_cost_display',
        'is_expired', 'days_until_expiry', 'received_date'
    ]

    fieldsets = (
        ('Product Information', {
            'fields': ('product', 'batch_number', 'reference_number')
        }),
        ('Quantity & Pricing', {
            'fields': ('quantity', 'cost_per_unit', 'total_cost_display')
        }),
        ('Entry Details', {
            'fields': ('entry_type', 'status', 'received_date', 'expiry_date')
        }),
        ('Expiry Information', {
            'fields': ('is_expired', 'days_until_expiry')
        }),
        ('Additional Information', {
            'fields': ('notes', 'created_at', 'updated_at')
        })
    )

    def quantity_display(self, obj):
        return f"{obj.quantity} {obj.product.unit_of_measure}"
    quantity_display.short_description = 'Quantity'

    def expiry_status(self, obj):
        if obj.expiry_date:
            if obj.is_expired:
                return format_html('<span style="color: red;">❌ Expired</span>')
            elif obj.days_until_expiry is not None and obj.days_until_expiry <= 7:
                return format_html('<span style="color: orange;">⚠️ Expires Soon</span>')
            else:
                return format_html('<span style="color: green;">✅ Fresh</span>')
        return '-'
    expiry_status.short_description = 'Expiry Status'

    def total_cost_display(self, obj):
        if obj.quantity is None or obj.cost_per_unit is None:
            return "—"
        total = obj.quantity * obj.cost_per_unit
        return f"{total:.2f}"
    total_cost_display.short_description = 'Total Cost'


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = [
        'stock_entry', 'product_name', 'movement_type', 'quantity_changed',
        'performed_by', 'created_at'
    ]
    list_filter = ['movement_type', 'created_at']
    search_fields = ['stock_entry__product__name', 'reason', 'performed_by']
    readonly_fields = ['created_at']

    def product_name(self, obj):
        return obj.stock_entry.product.name
    product_name.short_description = 'Product'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
