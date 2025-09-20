# Management Command to Create Inventory Alerts - crm/management/commands/check_inventory.py
from django.core.management.base import BaseCommand
from shop.models import Product
from crm.models import InventoryAlert

class Command(BaseCommand):
    help = 'Check inventory levels and create alerts'

    def handle(self, *args, **options):
        self.stdout.write('Checking inventory levels...')
        
        alerts_created = 0
        
        # Check for low stock products
        low_stock_products = Product.objects.filter(
            stock_status='low_stock',
            is_active=True
        )
        
        for product in low_stock_products:
            # Check if alert already exists
            if not InventoryAlert.objects.filter(
                product=product,
                alert_type='low_stock',
                status='active'
            ).exists():
                InventoryAlert.objects.create(
                    product=product,
                    alert_type='low_stock',
                    message=f'{product.name} is running low on stock',
                    current_stock=product.stock_quantity,
                    threshold_value=product.low_stock_threshold
                )
                alerts_created += 1
        
        # Check for out of stock products
        out_of_stock_products = Product.objects.filter(
            stock_status='out_of_stock',
            is_active=True
        )
        
        for product in out_of_stock_products:
            if not InventoryAlert.objects.filter(
                product=product,
                alert_type='out_of_stock',
                status='active'
            ).exists():
                InventoryAlert.objects.create(
                    product=product,
                    alert_type='out_of_stock',
                    message=f'{product.name} is out of stock',
                    current_stock=0,
                    threshold_value=0
                )
                alerts_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {alerts_created} new inventory alerts')
        )