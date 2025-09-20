from django.core.management.base import BaseCommand
from shop.models import Order
from crm.models import OrderManagement

class Command(BaseCommand):
    help = 'Create OrderManagement records for existing orders'

    def handle(self, *args, **options):
        self.stdout.write('Creating OrderManagement records...')
        
        orders_without_mgmt = Order.objects.filter(crm_management__isnull=True)
        created_count = 0
        
        for order in orders_without_mgmt:
            OrderManagement.objects.create(
                order=order,
                priority='normal'
            )
            created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} OrderManagement records'
            )
        )