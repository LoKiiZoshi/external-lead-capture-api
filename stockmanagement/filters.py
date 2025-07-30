import django_filters
from django import forms
from .models import Product, StockEntry, Category, Supplier


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains', label='Product Name')
    sku = django_filters.CharFilter(lookup_expr='icontains', label='SKU')
    category = django_filters.ModelChoiceFilter(
        queryset=Category.objects.filter(status=Category.CategoryStatus.ACTIVE),
        empty_label="All Categories"
    )
    supplier = django_filters.ModelChoiceFilter(
        queryset=Supplier.objects.filter(status=Supplier.SupplierStatus.ACTIVE),
        empty_label="All Suppliers"
    )
    cost_per_unit_min = django_filters.NumberFilter(
        field_name='cost_per_unit', 
        lookup_expr='gte',
        label='Min Cost'
    )
    cost_per_unit_max = django_filters.NumberFilter(
        field_name='cost_per_unit', 
        lookup_expr='lte',
        label='Max Cost'
    )
    low_stock = django_filters.BooleanFilter(
        method='filter_low_stock',
        label='Low Stock Only'
    )
    
    class Meta:
        model = Product
        fields = ['product_type', 'status']
    
    def filter_low_stock(self, queryset, name, value):
        if value:
            return [product for product in queryset if product.is_low_stock]
        return queryset


class StockEntryFilter(django_filters.FilterSet):
    product_name = django_filters.CharFilter(
        field_name='product__name',
        lookup_expr='icontains',
        label='Product Name'
    )
    batch_number = django_filters.CharFilter(lookup_expr='icontains')
    received_date_from = django_filters.DateFilter(
        field_name='received_date',
        lookup_expr='gte',
        label='Received From',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    received_date_to = django_filters.DateFilter(
        field_name='received_date',
        lookup_expr='lte',
        label='Received To',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    expiry_date_from = django_filters.DateFilter(
        field_name='expiry_date',
        lookup_expr='gte',
        label='Expires From',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    expiry_date_to = django_filters.DateFilter(
        field_name='expiry_date',
        lookup_expr='lte',
        label='Expires To',
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    
    class Meta:
        model = StockEntry
        fields = ['status', 'entry_type']
