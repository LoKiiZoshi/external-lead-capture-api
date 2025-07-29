from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import StockEntry, StockMovement, Product


@receiver(pre_save, sender=StockEntry)
def create_stock_movement(sender, instance, **kwargs):
    """Create stock movement record when stock entry is modified"""
    if instance.pk:  # Only for updates, not new entries
        try:
            old_instance = StockEntry.objects.get(pk=instance.pk)
            if old_instance.quantity != instance.quantity:
                # Create movement record for quantity change
                StockMovement.objects.create(
                    stock_entry=instance,
                    movement_type=StockMovement.MovementType.ADJUSTMENT,
                    quantity_changed=instance.quantity - old_instance.quantity,
                    previous_quantity=old_instance.quantity,
                    new_quantity=instance.quantity,
                    reason="Stock quantity adjusted"
                )
        except StockEntry.DoesNotExist:
            pass


@receiver(post_save, sender=StockEntry)
def create_initial_stock_movement(sender, instance, created, **kwargs):
    """Create initial stock movement when new stock entry is created"""
    if created:
        movement_type = StockMovement.MovementType.IN
        if instance.entry_type == StockEntry.EntryType.WASTE:
            movement_type = StockMovement.MovementType.WASTE
        elif instance.entry_type == StockEntry.EntryType.TRANSFER:
            movement_type = StockMovement.MovementType.TRANSFER
        
        StockMovement.objects.create(
            stock_entry=instance,
            movement_type=movement_type,
            quantity_changed=instance.quantity,
            previous_quantity=0,
            new_quantity=instance.quantity,
            reason=f"Initial stock entry - {instance.get_entry_type_display()}"
        )


@receiver(post_save, sender=StockEntry)
def update_product_status(sender, instance, **kwargs):
    """Update product status based on current stock levels"""
    product = instance.product
    current_stock = product.current_stock
    
    # Update product status if out of stock
    if current_stock == 0 and product.status == Product.ProductStatus.ACTIVE:
        product.status = Product.ProductStatus.OUT_OF_STOCK
        product.save(update_fields=['status'])
    elif current_stock > 0 and product.status == Product.ProductStatus.OUT_OF_STOCK:
        product.status = Product.ProductStatus.ACTIVE
        product.save(update_fields=['status'])

