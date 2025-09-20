# crm/management/commands/sync_customers.py
from django.core.management.base import BaseCommand
from shop.models import Order
from crm.models import Customer

class Command(BaseCommand):
    help = 'Sync customers from orders to CRM'

    def handle(self, *args, **options):
        self.stdout.write('Syncing customers from orders...')
        
        orders = Order.objects.all()
        created_count = 0
        updated_count = 0
        
        for order in orders:
            customer, created = Customer.objects.get_or_create(
                email=order.customer_email,
                defaults={
                    'name': order.customer_name,
                    'phone': order.customer_phone,
                    'address': order.shipping_address,
                    'city': order.shipping_city,
                    'postal_code': order.shipping_postal_code,
                }
            )
            
            if created:
                created_count += 1
            else:
                # Update customer info if changed
                if customer.name != order.customer_name:
                    customer.name = order.customer_name
                if customer.phone != order.customer_phone:
                    customer.phone = order.customer_phone
                if customer.address != order.shipping_address:
                    customer.address = order.shipping_address
                if customer.city != order.shipping_city:
                    customer.city = order.shipping_city
                customer.save()
                updated_count += 1
            
            # Update customer statistics
            customer.update_statistics()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully synced customers: {created_count} created, {updated_count} updated'
            )
        )