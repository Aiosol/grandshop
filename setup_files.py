# setup_files.py - Run this script to create all necessary files
import os

# File contents dictionary
files_content = {
    # Requirements
    "requirements.txt": """Django==4.2.7
djangorestframework==3.14.0
Pillow==10.1.0
celery==5.3.4
redis==5.0.1
requests==2.31.0
python-decouple==3.8

# For production
# mysqlclient==2.2.0
# gunicorn==21.2.0
# whitenoise==6.6.0""",

    # Environment file
    ".env": """DEBUG=True
SECRET_KEY=django-insecure-change-this-in-production
DATABASE_URL=sqlite:///db.sqlite3
REDIS_URL=redis://localhost:6379/1
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password""",

    # Main URLs
    "grandshopbd/urls.py": """from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('shop.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)""",

    # Shop URLs
    "shop/urls.py": """from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.HomeView.as_view(), name='home'),
    
    # Vehicle Filter AJAX
    path('ajax/vehicle-models/', views.get_vehicle_models, name='get_vehicle_models'),
    path('ajax/vehicle-years/', views.get_vehicle_years, name='get_vehicle_years'),
    path('ajax/chassis-codes/', views.get_chassis_codes, name='get_chassis_codes'),
    
    # Products
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('product/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('category/<slug:slug>/', views.CategoryProductsView.as_view(), name='category_products'),
    path('brand/<slug:slug>/', views.BrandProductsView.as_view(), name='brand_products'),
    
    # Search
    path('search/', views.search_view, name='search'),
    path('ajax/search/', views.ajax_search, name='ajax_search'),
    
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path('update-cart/', views.update_cart_item, name='update_cart_item'),
    path('remove-cart-item/', views.remove_cart_item, name='remove_cart_item'),
    
    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('process-order/', views.process_order, name='process_order'),
    
    # Buy Now (Direct Purchase)
    path('buy-now/', views.buy_now, name='buy_now'),
    path('buy-now/checkout/', views.buy_now_checkout, name='buy_now_checkout'),
    path('buy-now/process/', views.process_buy_now_order, name='process_buy_now_order'),
    
    # Orders
    path('order/<str:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('my-orders/', views.order_history, name='order_history'),
    
    # Pages
    path('page/<slug:slug>/', views.PageDetailView.as_view(), name='page_detail'),
]""",

    # Shop Apps
    "shop/apps.py": """from django.apps import AppConfig

class ShopConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shop'""",

    # Load Sample Data Command
    "shop/management/commands/load_sample_data.py": """from django.core.management.base import BaseCommand
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

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))""",

    # Deploy Script
    "deploy.py": """#!/usr/bin/env python
import os
import sys
import django
from django.core.management import execute_from_command_line

def deploy():
    print("🚀 Deploying GrandShopBD E-commerce Platform...")
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'grandshopbd.settings')
    django.setup()
    
    # Run migrations
    print("🗄️ Setting up database...")
    execute_from_command_line(['manage.py', 'makemigrations'])
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Create superuser
    print("👤 Creating superuser...")
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@grandshopbd.com', 'admin123')
        print('Superuser created: admin/admin123')
    
    # Load sample data
    print("📊 Loading sample data...")
    execute_from_command_line(['manage.py', 'load_sample_data'])
    
    # Collect static files
    print("📁 Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    print("🎉 Deployment complete!")
    print("")
    print("🔗 Access your application:")
    print("   Admin Panel: http://localhost:8000/admin")
    print("   Username: admin")
    print("   Password: admin123")

if __name__ == '__main__':
    deploy()""",

    # README
    "README.md": """# GrandShopBD - Automotive Parts E-commerce Platform

A comprehensive Django-based e-commerce platform specialized for automotive parts in Bangladesh.

## Features

- Advanced vehicle-based filtering system
- Mobile-first responsive design
- Dual purchase options (Add to Cart & Buy Now)
- Complete order management
- Vehicle compatibility system
- Multiple courier integration
- Admin panel for complete control

## Quick Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\\Scripts\\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run deployment:
```bash
python deploy.py
```

4. Start development server:
```bash
python manage.py runserver
```

## Admin Access

- URL: http://localhost:8000/admin
- Username: admin
- Password: admin123

## Project Structure

- `shop/` - Main application
- `templates/` - HTML templates
- `static/` - CSS, JS, images
- `media/` - User uploads

## Production Deployment

1. Update settings for production
2. Configure MySQL database
3. Set up Redis cache
4. Configure email settings
5. Set up SSL certificate

For detailed documentation, see the admin panel after setup.
""",

    # Static CSS
    "static/css/style.css": """/* GrandShopBD Custom Styles */
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --danger-color: #ef4444;
    --warning-color: #f59e0b;
}

/* Custom Bootstrap overrides */
.btn-primary {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-primary:hover {
    background-color: #1d4ed8;
    border-color: #1d4ed8;
}

/* Product cards */
.product-card {
    transition: transform 0.2s;
    border: 1px solid #e5e7eb;
}

.product-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

/* Price styling */
.price-old {
    text-decoration: line-through;
    color: #6b7280;
}

.price-new {
    color: var(--danger-color);
    font-weight: bold;
}

/* Discount badge */
.discount-badge {
    position: absolute;
    top: 10px;
    right: 10px;
    background: var(--danger-color);
    color: white;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
}

/* Search suggestions */
.search-suggestions {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: white;
    border: 1px solid #e5e7eb;
    border-top: none;
    max-height: 300px;
    overflow-y: auto;
    z-index: 1000;
}

.suggestion-item {
    padding: 10px;
    border-bottom: 1px solid #f3f4f6;
    cursor: pointer;
}

.suggestion-item:hover {
    background-color: #f9fafb;
}

/* Vehicle filter modal */
.vehicle-filter-modal .modal-dialog {
    max-width: 600px;
}

.vehicle-brand-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    gap: 15px;
}

.vehicle-brand-item {
    text-align: center;
    padding: 15px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.vehicle-brand-item:hover,
.vehicle-brand-item.selected {
    border-color: var(--primary-color);
    background-color: #eff6ff;
}

.vehicle-model-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 15px;
}

.vehicle-model-item {
    text-align: center;
    padding: 15px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s;
}

.vehicle-model-item:hover,
.vehicle-model-item.selected {
    border-color: var(--primary-color);
    background-color: #eff6ff;
}

/* Category icons */
.category-icon {
    font-size: 2rem;
    color: var(--primary-color);
    margin-bottom: 10px;
}

/* Footer */
.footer {
    background-color: #1f2937;
    color: #d1d5db;
    padding: 40px 0 20px;
}

.footer h5 {
    color: white;
    margin-bottom: 20px;
}

.footer a {
    color: #d1d5db;
    text-decoration: none;
}

.footer a:hover {
    color: white;
}

/* Timeline styles */
.timeline {
    position: relative;
    padding-left: 30px;
}

.timeline::before {
    content: '';
    position: absolute;
    left: 15px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #dee2e6;
}

.timeline-item {
    position: relative;
    margin-bottom: 20px;
}

.timeline-marker {
    position: absolute;
    left: -23px;
    width: 16px;
    height: 16px;
    border-radius: 50%;
    border: 2px solid white;
    box-shadow: 0 0 0 3px #dee2e6;
}

.timeline-item.completed .timeline-marker {
    box-shadow: 0 0 0 3px #28a745;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .vehicle-brand-grid {
        grid-template-columns: repeat(2, 1fr);
    }
    
    .vehicle-model-grid {
        grid-template-columns: repeat(2, 1fr);
    }
}

/* Loading spinner */
.spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid var(--primary-color);
    border-radius: 50%;
    width: 40px;
    height: 40px;
    animation: spin 2s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}""",

    # Static JavaScript
    "static/js/main.js": """// GrandShopBD Main JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initializeSearch();
    initializeTooltips();
    
    // Load vehicle brands for modal
    loadVehicleBrands();
});

// Global variables
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
let selectedBrand = null;
let selectedModel = null;
let selectedYear = null;
let selectedChassis = null;

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;
    
    const suggestionsDiv = document.getElementById('searchSuggestions');
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                fetchSearchSuggestions(query);
            }, 300);
        } else {
            if (suggestionsDiv) {
                suggestionsDiv.style.display = 'none';
            }
        }
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (suggestionsDiv && !searchInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.style.display = 'none';
        }
    });
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Utility functions
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    const toast = createToastElement(message, type);
    toastContainer.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 3000);
}

function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
        document.body.appendChild(container);
    }
    return container;
}

function createToastElement(message, type) {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    toast.style.cssText = 'margin-bottom: 10px; min-width: 300px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    return toast;
}

// Cart functions (defined globally for template access)
window.addToCart = function(productId, quantity = 1) {
    fetch('/add-to-cart/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken
        },
        body: `product_id=${productId}&quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCount(data.cart_count);
            showToast('Product added to cart!', 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error adding product to cart', 'error');
    });
};

window.buyNow = function(productId, quantity = 1) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/buy-now/';
    
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = csrfToken;
    
    const productInput = document.createElement('input');
    productInput.type = 'hidden';
    productInput.name = 'product_id';
    productInput.value = productId;
    
    const quantityInput = document.createElement('input');
    quantityInput.type = 'hidden';
    quantityInput.name = 'quantity';
    quantityInput.value = quantity;
    
    form.appendChild(csrfInput);
    form.appendChild(productInput);
    form.appendChild(quantityInput);
    
    document.body.appendChild(form);
    form.submit();
};

function updateCartCount(count) {
    const cartBadge = document.querySelector('.navbar .badge');
    if (cartBadge) {
        cartBadge.textContent = count;
        cartBadge.style.display = count > 0 ? 'inline' : 'none';
    }
}

// Vehicle filter functions
function loadVehicleBrands() {
    // This will be populated from backend or hardcoded for demo
    const brands = [
        {id: 1, name: 'TOYOTA', logo: '/static/images/brands/toyota.png'},
        {id: 2, name: 'HONDA', logo: '/static/images/brands/honda.png'},
        {id: 3, name: 'MITSUBISHI', logo: '/static/images/brands/mitsubishi.png'},
        {id: 4, name: 'NISSAN', logo: '/static/images/brands/nissan.png'},
        {id: 5, name: 'MAZDA', logo: '/static/images/brands/mazda.png'},
        {id: 6, name: 'LEXUS', logo: '/static/images/brands/lexus.png'},
    ];
    
    const brandGrid = document.getElementById('brandGrid');
    if (!brandGrid) return;
    
    let html = '';
    brands.forEach(brand => {
        html += `
            <div class="vehicle-brand-item" onclick="selectBrand(${brand.id}, '${brand.name}')">
                <img src="${brand.logo}" alt="${brand.name}" class="mb-2" style="max-height: 40px;" onerror="this.style.display='none'">
                <div class="fw-medium">${brand.name}</div>
            </div>
        `;
    });
    
    brandGrid.innerHTML = html;
}

console.log('GrandShopBD JavaScript loaded successfully!');"""
}

def create_file(file_path, content):
    """Create a file with the given content"""
    # Create directory if it doesn't exist
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
    
    # Write content to file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {file_path}")

def main():
    print("🚀 Setting up GrandShopBD project files...")
    
    # Create all files
    for file_path, content in files_content.items():
        create_file(file_path, content)
    
    print("\n🎉 All files created successfully!")
    print("\n📋 Next steps:")
    print("1. Run: pip install -r requirements.txt")
    print("2. Run: python deploy.py")
    print("3. Run: python manage.py runserver")
    print("\n🔗 Access admin: http://localhost:8000/admin")
    print("   Username: admin")
    print("   Password: admin123")

if __name__ == "__main__":
    main()