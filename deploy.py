#!/usr/bin/env python
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
    deploy()