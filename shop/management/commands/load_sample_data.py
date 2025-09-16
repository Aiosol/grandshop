from django.core.management.base import BaseCommand
from shop.models import *

class Command(BaseCommand):
    help = 'Load sample data for development'

    def handle(self, *args, **options):
        self.stdout.write('Loading sample data...')
        
        # Create vehicle brands
        brands_data = [
            {'name': 'Toyota'},
            {'name': 'Honda'},
            {'name': 'Mitsubishi'},
            {'name': 'Nissan'},
            {'name': 'Mazda'},
            {'name': 'Lexus'},
            {'name': 'Hyundai'},
        ]

        for brand_data in brands_data:
            brand, created = VehicleBrand.objects.get_or_create(
                name=brand_data['name'],
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'Created vehicle brand: {brand.name}')

        # Create sample categories
        categories_data = [
            {'name': 'Engine Parts', 'icon': 'fas fa-cog'},
            {'name': 'Brake System', 'icon': 'fas fa-stop-circle'},
            {'name': 'Suspension', 'icon': 'fas fa-arrows-alt-v'},
            {'name': 'Electrical', 'icon': 'fas fa-bolt'},
            {'name': 'Body Parts', 'icon': 'fas fa-car'},
            {'name': 'Oils & Fluids', 'icon': 'fas fa-oil-can'},
            {'name': 'Filters', 'icon': 'fas fa-filter'},
            {'name': 'Lights', 'icon': 'fas fa-lightbulb'},
        ]

        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults={'icon': cat_data['icon'], 'is_active': True}
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')

        # Create product brands
        product_brands_data = [
            'Motul', 'Castrol', 'Shell', 'Total', 'Mobil 1',
            'Bosch', 'NGK', 'Denso', 'Continental', 'Brembo'
        ]

        for brand_name in product_brands_data:
            brand, created = Brand.objects.get_or_create(
                name=brand_name,
                defaults={'is_active': True}
            )
            if created:
                self.stdout.write(f'Created product brand: {brand.name}')

        # Create courier services
        courier_data = [
            {'name': 'Steadfast', 'delivery_time': '1-2 days', 'is_active': True},
            {'name': 'Pathao', 'delivery_time': 'Same day', 'is_active': True},
            {'name': 'Redx', 'delivery_time': '1-3 days', 'is_active': True},
        ]

        for courier in courier_data:
            service, created = CourierService.objects.get_or_create(
                name=courier['name'],
                defaults=courier
            )
            if created:
                self.stdout.write(f'Created courier service: {service.name}')

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))