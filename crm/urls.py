# Updated CRM URLs with additional endpoints - crm/urls.py
from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Dashboard
    path('', views.crm_dashboard, name='dashboard'),
    
    # Order Management
    path('orders/', views.order_management, name='order_management'),
    path('orders/bulk-operations/', views.bulk_order_operations, name='bulk_order_operations'),
    
    # Customer Management
    path('customers/', views.customer_management, name='customer_management'),
    path('customers/<int:customer_id>/', views.customer_detail, name='customer_detail'),
    
    # Inventory Management
    path('inventory/', views.inventory_management, name='inventory_management'),
    path('inventory/sync/', views.trigger_inventory_sync, name='trigger_inventory_sync'),
    path('inventory/alerts/<int:alert_id>/acknowledge/', views.acknowledge_alert, name='acknowledge_alert'),
    
    # Campaign Management
    path('campaigns/', views.campaign_management, name='campaign_management'),
    path('campaigns/<int:campaign_id>/start/', views.start_campaign, name='start_campaign'),
    path('campaigns/<int:campaign_id>/pause/', views.pause_campaign, name='pause_campaign'),
    path('sms/balance/', views.check_sms_balance, name='check_sms_balance'),
    path('email/test/', views.test_email_connection, name='test_email_connection'),
]