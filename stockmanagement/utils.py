from decimal import Decimal
from django.db.models import Sum, Avg
from django.utils import timezone
from datetime import timedelta
from .models import Product, StockEntry, StockMovement


class InventoryAnalytics:
    """Utility class for inventory analytics and reporting"""
    
    @staticmethod
    def get_inventory_value():
        """Calculate total inventory value"""
        total_value = Decimal('0.00')
        
        for product in Product.objects.filter(status=Product.ProductStatus.ACTIVE):
            available_entries = product.stock_entries.filter(
                status=StockEntry.StockStatus.AVAILABLE
            )
            for entry in available_entries:
                total_value += entry.total_cost
        
        return total_value
    
    @staticmethod
    def get_category_breakdown():
        """Get inventory breakdown by category"""
        from .models import Category
        
        breakdown = []
        for category in Category.objects.filter(status=Category.CategoryStatus.ACTIVE):
            products = category.products.filter(status=Product.ProductStatus.ACTIVE)
            total_products = products.count()
            total_value = Decimal('0.00')
            
            for product in products:
                available_entries = product.stock_entries.filter(
                    status=StockEntry.StockStatus.AVAILABLE
                )
                for entry in available_entries:
                    total_value += entry.total_cost
            
            breakdown.append({
                'category': category.name,
                'total_products': total_products,
                'total_value': total_value
            })
        
        return breakdown
    
    @staticmethod
    def get_expiry_report(days_ahead=30):
        """Get report of items expiring within specified days"""
        expiry_threshold = timezone.now().date() + timedelta(days=days_ahead)
        
        expiring_entries = StockEntry.objects.filter(
            status=StockEntry.StockStatus.AVAILABLE,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=timezone.now().date()
        ).order_by('expiry_date')
        
        report = []
        for entry in expiring_entries:
            days_until_expiry = (entry.expiry_date - timezone.now().date()).days
            report.append({
                'product': entry.product.name,
                'sku': entry.product.sku,
                'quantity': entry.quantity,
                'unit': entry.product.unit_of_measure,
                'expiry_date': entry.expiry_date,
                'days_until_expiry': days_until_expiry,
                'batch_number': entry.batch_number,
                'total_value': entry.total_cost
            })
        
        return report
    
    @staticmethod
    def get_stock_movement_summary(days=30):
        """Get stock movement summary for the past N days"""
        start_date = timezone.now() - timedelta(days=days)
        
        movements = StockMovement.objects.filter(created_at__gte=start_date)
        
        summary = {
            'total_movements': movements.count(),
            'stock_in': movements.filter(movement_type=StockMovement.MovementType.IN).count(),
            'stock_out': movements.filter(movement_type=StockMovement.MovementType.OUT).count(),
            'adjustments': movements.filter(movement_type=StockMovement.MovementType.ADJUSTMENT).count(),
            'waste': movements.filter(movement_type=StockMovement.MovementType.WASTE).count(),
        }
        
        return summary

