from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class TimestampedModel(models.Model):
    """Abstract base class with timestamp fields"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True


class Category(TimestampedModel):
    class CategoryStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        ARCHIVED = 'archived', 'Archived'
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=CategoryStatus.choices, default=CategoryStatus.ACTIVE)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Supplier(TimestampedModel):
    class SupplierStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'Inactive'
        BLACKLISTED = 'blacklisted', 'Blacklisted'
    
    name = models.CharField(max_length=150, unique=True)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SupplierStatus.choices, default=SupplierStatus.ACTIVE)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(TimestampedModel):
    class ProductType(models.TextChoices):
        FRESH = 'fresh', 'Fresh Produce'
        FROZEN = 'frozen', 'Frozen'
        DRY_GOODS = 'dry_goods', 'Dry Goods'
        BEVERAGES = 'beverages', 'Beverages'
        CONDIMENTS = 'condiments', 'Condiments & Spices'
        MEAT = 'meat', 'Meat & Poultry'
        SEAFOOD = 'seafood', 'Seafood'
        DAIRY = 'dairy', 'Dairy Products'
        OTHER = 'other', 'Other'
    
    class ProductStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        DISCONTINUED = 'discontinued', 'Discontinued'
        SEASONAL = 'seasonal', 'Seasonal'
        OUT_OF_STOCK = 'out_of_stock', 'Out of Stock'
    
    class UnitOfMeasure(models.TextChoices):
        KG = 'kg', 'Kilograms'
        GRAM = 'g', 'Grams'
        LITER = 'l', 'Liters'
        ML = 'ml', 'Milliliters'
        PIECE = 'piece', 'Pieces'
        DOZEN = 'dozen', 'Dozen'
        PACK = 'pack', 'Pack'
        BOX = 'box', 'Box'
        BAG = 'bag', 'Bag'
        BOTTLE = 'bottle', 'Bottle'
        CAN = 'can', 'Can'
    
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products') 
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    product_type = models.CharField(max_length=20, choices=ProductType.choices, default=ProductType.OTHER)
    unit_of_measure = models.CharField(max_length=20, choices=UnitOfMeasure.choices, default=UnitOfMeasure.PIECE)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    minimum_stock_level = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text="Minimum quantity before reorder alert")
    maximum_stock_level = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Maximum storage capacity")
    shelf_life_days = models.PositiveIntegerField(null=True, blank=True, help_text="Shelf life in days")
    storage_instructions = models.TextField(blank=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=ProductStatus.choices, default=ProductStatus.ACTIVE)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['product_type']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def current_stock(self):
        stock_entries = self.stock_entries.filter(status=StockEntry.StockStatus.AVAILABLE)
        return sum(entry.quantity for entry in stock_entries)
    
    @property
    def is_low_stock(self):
        return self.current_stock < self.minimum_stock_level
    
    @property
    def is_overstocked(self):
        if self.maximum_stock_level:
            return self.current_stock > self.maximum_stock_level
        return False


class StockEntry(TimestampedModel):
    class StockStatus(models.TextChoices):
        AVAILABLE = 'available', 'Available'
        RESERVED = 'reserved', 'Reserved'
        EXPIRED = 'expired', 'Expired'
        DAMAGED = 'damaged', 'Damaged'
        USED = 'used', 'Used'
        RETURNED = 'returned', 'Returned to Supplier'
    
    class EntryType(models.TextChoices):
        PURCHASE = 'purchase', 'Purchase'
        RETURN = 'return', 'Return from Kitchen'
        ADJUSTMENT = 'adjustment', 'Stock Adjustment'
        TRANSFER = 'transfer', 'Transfer'
        WASTE = 'waste', 'Waste/Spoilage'
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_entries')
    batch_number = models.CharField(max_length=100, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    entry_type = models.CharField(max_length=20, choices=EntryType.choices, default=EntryType.PURCHASE)
    status = models.CharField(max_length=20, choices=StockStatus.choices, default=StockStatus.AVAILABLE)
    received_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateField(null=True, blank=True)
    cost_per_unit = models.DecimalField(max_digits=10, decimal_places=2, help_text="Cost per unit for this specific entry")
    reference_number = models.CharField(max_length=100, blank=True, help_text="Invoice number, PO number, etc.")
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name_plural = "Stock Entries"
        ordering = ['-received_date']
        indexes = [
            models.Index(fields=['product', 'status']),
            models.Index(fields=['expiry_date']),
            models.Index(fields=['batch_number']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.quantity} {self.product.unit_of_measure}"
    
    @property
    def total_cost(self):
        if self.quantity is None or self.cost_per_unit is None:
            return Decimal('0.00')
        return self.quantity * self.cost_per_unit
    
    @property
    def is_expired(self):
        if self.expiry_date:
            from django.utils import timezone
            return self.expiry_date < timezone.now().date()
        return False
    
    @property
    def days_until_expiry(self):
        if self.expiry_date:
            from django.utils import timezone
            delta = self.expiry_date - timezone.now().date()
            return delta.days
        return None


class StockMovement(TimestampedModel):
    class MovementType(models.TextChoices):
        IN = 'in', 'Stock In'
        OUT = 'out', 'Stock Out'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        TRANSFER = 'transfer', 'Transfer'
        WASTE = 'waste', 'Waste'
    
    stock_entry = models.ForeignKey(StockEntry, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity_changed = models.DecimalField(max_digits=10, decimal_places=2, help_text="Positive for increases, negative for decreases")
    previous_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    new_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.CharField(max_length=200, blank=True)
    performed_by = models.CharField(max_length=100, blank=True)
    reference_document = models.CharField(max_length=100, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stock_entry', 'movement_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.stock_entry.product.name} - {self.movement_type} - {self.quantity_changed}"
