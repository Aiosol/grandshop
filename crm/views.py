# crm/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse, HttpResponse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Sum, Avg
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import *
from shop.models import Order, Product
from .services import SteadfastAPI, PathaoAPI, ManagerIOAPI

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

@staff_member_required
def crm_dashboard(request):
    """CRM Dashboard with key metrics"""
    # Date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Order statistics
    total_orders = Order.objects.count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_this_week = Order.objects.filter(created_at__date__gte=week_ago).count()
    orders_this_month = Order.objects.filter(created_at__date__gte=month_ago).count()
    
    # Revenue statistics
    total_revenue = Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    revenue_today = Order.objects.filter(created_at__date=today).aggregate(total=Sum('total_amount'))['total'] or 0
    revenue_this_month = Order.objects.filter(created_at__date__gte=month_ago).aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Customer statistics
    total_customers = Customer.objects.count()
    new_customers_today = Customer.objects.filter(created_at__date=today).count()
    active_customers = Customer.objects.filter(status='active').count()
    
    # Inventory alerts
    active_alerts = InventoryAlert.objects.filter(status='active').count()
    low_stock_products = Product.objects.filter(stock_status='low_stock').count()
    out_of_stock_products = Product.objects.filter(stock_status='out_of_stock').count()
    
    # Pending operations
    pending_orders = OrderManagement.objects.filter(
        order__status__in=['pending', 'confirmed']
    ).count()
    
    # Recent activities
    recent_orders = OrderManagement.objects.select_related('order').order_by('-created_at')[:10]
    recent_alerts = InventoryAlert.objects.select_related('product').filter(status='active')[:5]
    
    context = {
        'total_orders': total_orders,
        'orders_today': orders_today,
        'orders_this_week': orders_this_week,
        'orders_this_month': orders_this_month,
        'total_revenue': total_revenue,
        'revenue_today': revenue_today,
        'revenue_this_month': revenue_this_month,
        'total_customers': total_customers,
        'new_customers_today': new_customers_today,
        'active_customers': active_customers,
        'active_alerts': active_alerts,
        'low_stock_products': low_stock_products,
        'out_of_stock_products': out_of_stock_products,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'recent_alerts': recent_alerts,
    }
    
    return render(request, 'crm/dashboard.html', context)

@staff_member_required
def order_management(request):
    """Order management with bulk operations"""
    # Filters
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    agent_filter = request.GET.get('agent', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    # Base queryset
    orders = OrderManagement.objects.select_related(
        'order', 'assigned_agent__user'
    ).order_by('-created_at')
    
    # Apply filters
    if status_filter:
        orders = orders.filter(order__status=status_filter)
    if priority_filter:
        orders = orders.filter(priority=priority_filter)
    if agent_filter:
        orders = orders.filter(assigned_agent_id=agent_filter)
    if date_from:
        orders = orders.filter(order__created_at__date__gte=date_from)
    if date_to:
        orders = orders.filter(order__created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(orders, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    agents = CRMUser.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'agents': agents,
        'current_filters': request.GET,
    }
    
    return render(request, 'crm/order_management.html', context)

@staff_member_required
def bulk_order_operations(request):
    """Handle bulk operations on orders"""
    if request.method == 'POST':
        operation_type = request.POST.get('operation_type')
        order_ids = request.POST.getlist('order_ids')
        
        if not order_ids:
            messages.error(request, 'No orders selected')
            return redirect('crm:order_management')
        
        # Create bulk operation record
        bulk_op = BulkOrderOperation.objects.create(
            operation_type=operation_type,
            created_by=request.user.crmuser,
            total_orders=len(order_ids),
            operation_params={
                'order_ids': order_ids,
                'operation_data': dict(request.POST)
            }
        )
        
        # Process based on operation type
        try:
            if operation_type == 'courier_assign':
                courier_service = request.POST.get('courier_service')
                result = process_courier_assignment(order_ids, courier_service, bulk_op)
            elif operation_type == 'status_update':
                new_status = request.POST.get('new_status')
                result = process_status_update(order_ids, new_status, bulk_op)
            elif operation_type == 'label_generate':
                result = process_label_generation(order_ids, bulk_op)
            
            messages.success(request, f'Bulk operation completed: {result["message"]}')
            
        except Exception as e:
            bulk_op.status = 'failed'
            bulk_op.error_log = str(e)
            bulk_op.save()
             

            messages.error(request, f'Bulk operation failed: {str(e)}')
        
        return redirect('crm:order_management')
    
    return redirect('crm:order_management')

def process_courier_assignment(order_ids, courier_service, bulk_op):
    """Process courier assignment for multiple orders"""
    bulk_op.status = 'processing'
    bulk_op.started_at = timezone.now()
    bulk_op.save()
    
    processed = 0
    failed = 0
    
    for order_id in order_ids:
        try:
            order_mgmt = OrderManagement.objects.get(order_id=order_id)
            order_mgmt.courier_assigned = courier_service
            order_mgmt.save()
            processed += 1
        except Exception as e:
            failed += 1
            bulk_op.error_log += f"Order {order_id}: {str(e)}\n"
    
    bulk_op.processed_orders = processed
    bulk_op.failed_orders = failed
    bulk_op.status = 'completed'
    bulk_op.completed_at = timezone.now()
    bulk_op.save()
    
    return {
        'message': f'Assigned {courier_service} to {processed} orders. {failed} failed.',
        'processed': processed,
        'failed': failed
    }

def process_status_update(order_ids, new_status, bulk_op):
    """Process status update for multiple orders"""
    bulk_op.status = 'processing'
    bulk_op.started_at = timezone.now()
    bulk_op.save()
    
    processed = 0
    failed = 0
    
    for order_id in order_ids:
        try:
            order = Order.objects.get(id=order_id)
            order.status = new_status
            order.save()
            processed += 1
        except Exception as e:
            failed += 1
            bulk_op.error_log += f"Order {order_id}: {str(e)}\n"
    
    bulk_op.processed_orders = processed
    bulk_op.failed_orders = failed
    bulk_op.status = 'completed'
    bulk_op.completed_at = timezone.now()
    bulk_op.save()
    
    return {
        'message': f'Updated status for {processed} orders. {failed} failed.',
        'processed': processed,
        'failed': failed
    }

@staff_member_required
def customer_management(request):
    """Customer management and CRM"""
    # Filters
    status_filter = request.GET.get('status', '')
    city_filter = request.GET.get('city', '')
    agent_filter = request.GET.get('agent', '')
    search_query = request.GET.get('search', '')
    
    # Base queryset
    customers = Customer.objects.select_related('assigned_agent__user').order_by('-created_at')
    
    # Apply filters
    if status_filter:
        customers = customers.filter(status=status_filter)
    if city_filter:
        customers = customers.filter(city=city_filter)
    if agent_filter:
        customers = customers.filter(assigned_agent_id=agent_filter)
    if search_query:
        customers = customers.filter(
            Q(name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(customers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    agents = CRMUser.objects.filter(is_active=True)
    cities = Customer.objects.values_list('city', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'customers': page_obj.object_list,
        'agents': agents,
        'cities': cities,
        'current_filters': request.GET,
    }
    
    return render(request, 'crm/customer_management.html', context)

@staff_member_required
def customer_detail(request, customer_id):
    """Detailed customer view with notes and history"""
    customer = get_object_or_404(Customer, id=customer_id)
    
    # Customer orders
    orders = Order.objects.filter(customer_email=customer.email).order_by('-created_at')
    
    # Customer notes
    notes = customer.notes.select_related('created_by__user').order_by('-created_at')
    
    # Add note handling
    if request.method == 'POST':
        note_type = request.POST.get('note_type')
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        is_important = request.POST.get('is_important') == 'on'
        follow_up_date = request.POST.get('follow_up_date') or None
        
        CustomerNote.objects.create(
            customer=customer,
            created_by=request.user.crmuser,
            note_type=note_type,
            subject=subject,
            content=content,
            is_important=is_important,
            follow_up_date=follow_up_date
        )
        
        messages.success(request, 'Note added successfully')
        return redirect('crm:customer_detail', customer_id=customer.id)
    
    context = {
        'customer': customer,
        'orders': orders[:10],  # Last 10 orders
        'notes': notes[:20],    # Last 20 notes
        'total_orders': orders.count(),
    }
    
    return render(request, 'crm/customer_detail.html', context)

@staff_member_required
def inventory_management(request):
    """Inventory management and alerts"""
    # Active alerts
    alerts = InventoryAlert.objects.filter(
        status='active'
    ).select_related('product').order_by('-created_at')
    
    # Low stock products
    low_stock_products = Product.objects.filter(
        stock_status='low_stock'
    ).order_by('stock_quantity')
    
    # Out of stock products
    out_of_stock_products = Product.objects.filter(
        stock_status='out_of_stock'
    ).order_by('-updated_at')
    
    # Manager.io sync status
    recent_syncs = ManagerIOSync.objects.order_by('-created_at')[:5]
    
    context = {
        'alerts': alerts,
        'low_stock_products': low_stock_products[:20],
        'out_of_stock_products': out_of_stock_products[:20],
        'recent_syncs': recent_syncs,
    }
    
    return render(request, 'crm/inventory_management.html', context)

@staff_member_required
def campaign_management(request):
    """Email/SMS campaign management"""
    campaigns = CampaignManagement.objects.order_by('-created_at')
    
    # Campaign statistics
    total_campaigns = campaigns.count()
    active_campaigns = campaigns.filter(status__in=['running', 'scheduled']).count()
    total_emails_sent = campaigns.aggregate(total=Sum('emails_sent'))['total'] or 0
    total_sms_sent = campaigns.aggregate(total=Sum('sms_sent'))['total'] or 0
    
    context = {
        'campaigns': campaigns,
        'total_campaigns': total_campaigns,
        'active_campaigns': active_campaigns,
        'total_emails_sent': total_emails_sent,
        'total_sms_sent': total_sms_sent,
    }
    
    return render(request, 'crm/campaign_management.html', context)



@staff_member_required
@require_http_methods(["POST"])
def trigger_inventory_sync(request):
    """Trigger inventory sync with Manager.io"""
    try:
        sync_record = ManagerIOSync.objects.create(
            sync_type='inventory',
            status='pending'
        )
        
        # Here you would implement the actual sync with Manager.io API
        # For now, we'll simulate it
        sync_record.status = 'running'
        sync_record.started_at = timezone.now()
        sync_record.save()
        
        # TODO: Implement actual Manager.io API integration
        # manager_api = ManagerIOAPI()
        # result = manager_api.sync_inventory()
        
        # Simulate completion
        sync_record.status = 'completed'
        sync_record.completed_at = timezone.now()
        sync_record.records_synced = 50  # Example
        sync_record.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Inventory sync completed successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Sync failed: {str(e)}'
        })

@staff_member_required
@require_http_methods(["POST"])
def acknowledge_alert(request, alert_id):
    """Acknowledge an inventory alert"""
    try:
        alert = InventoryAlert.objects.get(id=alert_id)
        alert.status = 'acknowledged'
        alert.acknowledged_by = request.user.crmuser
        alert.acknowledged_at = timezone.now()
        alert.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Alert acknowledged'
        })
    except InventoryAlert.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Alert not found'
        })

@staff_member_required
@require_http_methods(["POST"])
def start_campaign(request, campaign_id):
    """Start a campaign"""
    try:
        campaign = CampaignManagement.objects.get(id=campaign_id)
        campaign.status = 'running'
        campaign.save()
        
        # TODO: Implement actual campaign sending logic
        # send_campaign(campaign)
        
        return JsonResponse({
            'success': True,
            'message': f'Campaign "{campaign.name}" started successfully'
        })
    except CampaignManagement.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Campaign not found'
        })

@staff_member_required
@require_http_methods(["POST"])
def pause_campaign(request, campaign_id):
    """Pause a running campaign"""
    try:
        campaign = CampaignManagement.objects.get(id=campaign_id)
        campaign.status = 'paused'
        campaign.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Campaign "{campaign.name}" paused'
        })
    except CampaignManagement.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Campaign not found'
        })

@staff_member_required
def check_sms_balance(request):
    """Check SMS balance from SSLCommerz"""
    try:
        # TODO: Implement actual SMS balance check
        # balance = sslcommerz_sms_api.check_balance()
        balance = "1,250"  # Simulated balance
        
        return JsonResponse({
            'success': True,
            'balance': balance
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })

@staff_member_required
@require_http_methods(["POST"])
def test_email_connection(request):
    """Test email SMTP connection"""
    try:
        from django.core.mail import send_mail
        
        send_mail(
            'CRM Email Test',
            'This is a test email from your CRM system.',
            settings.DEFAULT_FROM_EMAIL,
            [request.user.email],
            fail_silently=False,
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Test email sent successfully'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Email test failed: {str(e)}'
        })