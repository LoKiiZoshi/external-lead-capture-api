from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from stockmanagement.models import Product, StockEntry
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'Send stock alerts for low stock and expiring items'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email address to send alerts to',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days ahead to check for expiring items',
        )
    
    def handle(self, *args, **options):
        email = options.get('email')
        days_ahead = options.get('days')
        
        if not email:
            self.stdout.write(
                self.style.ERROR('Please provide an email address using --email')
            )
            return
        
        # Check for low stock products
        low_stock_products = []
        for product in Product.objects.filter(status=Product.ProductStatus.ACTIVE):
            if product.is_low_stock:
                low_stock_products.append(product)
        
        # Check for expiring items
        expiry_threshold = datetime.now().date() + timedelta(days=days_ahead)
        expiring_entries = StockEntry.objects.filter(
            status=StockEntry.StockStatus.AVAILABLE,
            expiry_date__lte=expiry_threshold,
            expiry_date__gte=datetime.now().date()
        )
        
        if low_stock_products or expiring_entries:
            subject = 'Restaurant Inventory Alert'
            message = self._build_alert_message(low_stock_products, expiring_entries, days_ahead)
            
            try:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Alert email sent successfully to {email}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to send email: {str(e)}')
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('No alerts needed - all stock levels are healthy')
            )
    
    def _build_alert_message(self, low_stock_products, expiring_entries, days_ahead):
        message = "Restaurant Inventory Alert Report\n"
        message += "=" * 40 + "\n\n"
        
        if low_stock_products:
            message += f"LOW STOCK ALERT ({len(low_stock_products)} items):\n"
            message += "-" * 30 + "\n"
            for product in low_stock_products:
                message += f"• {product.name} ({product.sku})\n"
                message += f"  Current: {product.current_stock} {product.unit_of_measure}\n"
                message += f"  Minimum: {product.minimum_stock_level} {product.unit_of_measure}\n\n"
        
        if expiring_entries:
            message += f"EXPIRING ITEMS ({len(expiring_entries)} entries expiring within {days_ahead} days):\n"
            message += "-" * 50 + "\n"
            for entry in expiring_entries:
                days_left = (entry.expiry_date - datetime.now().date()).days
                message += f"• {entry.product.name} - Batch: {entry.batch_number or 'N/A'}\n"
                message += f"  Quantity: {entry.quantity} {entry.product.unit_of_measure}\n"
                message += f"  Expires: {entry.expiry_date} ({days_left} days)\n\n"
        
        message += "Please take appropriate action to maintain optimal inventory levels.\n"
        return message
