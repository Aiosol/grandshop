# crm/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import *

@admin.register(CRMUser)
class CRMUserAdmin(admin.ModelAdmin):
    list_display = ['user', 'role', 'department', 'is_active', 'last_login']
    list_filter = ['role', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'department']
    list_editable = ['role', 'is_active']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone', 'status', 'total_orders', 'total_spent', 'last_order_date']
    list_filter = ['status', 'customer_type', 'city', 'assigned_agent']
    search_fields = ['name', 'email', 'phone']
    list_editable = ['status']
    readonly_fields = ['total_orders', 'total_spent', 'average_order_value', 'last_order_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'email', 'phone', 'alternative_phone')
        }),
        ('Address', {
            'fields': ('address', 'city', 'postal_code')
        }),
        ('CRM Management', {
            'fields': ('status', 'customer_type', 'assigned_agent', 'preferred_contact_method')
        }),
        ('Statistics', {
            'fields': ('total_orders', 'total_spent', 'average_order_value', 'last_order_date'),
            'classes': ('collapse',)
        }),
        ('Acquisition', {
            'fields': ('acquisition_source',),
            'classes': ('collapse',)
        })
    )
    
    actions = ['update_customer_statistics']
    
    def update_customer_statistics(self, request, queryset):
        for customer in queryset:
            customer.update_statistics()
        self.message_user(request, f"Updated statistics for {queryset.count()} customers")
    update_customer_statistics.short_description = "Update customer statistics"

class CustomerNoteInline(admin.TabularInline):
    model = CustomerNote
    extra = 1
    fields = ['note_type', 'subject', 'content', 'is_important', 'follow_up_date']

@admin.register(OrderManagement)
class OrderManagementAdmin(admin.ModelAdmin):
    list_display = ['order', 'assigned_agent', 'priority', 'quality_checked', 'courier_assigned', 'tracking_number']
    list_filter = ['priority', 'quality_checked', 'courier_assigned', 'shipping_label_generated']
    search_fields = ['order__order_number', 'tracking_number']
    list_editable = ['priority', 'assigned_agent']
    
    fieldsets = (
        ('Order Assignment', {
            'fields': ('order', 'assigned_agent', 'priority')
        }),
        ('Processing', {
            'fields': ('processing_notes', 'estimated_processing_time', 'actual_processing_time', 'processing_started_at')
        }),
        ('Quality Control', {
            'fields': ('quality_checked', 'quality_checked_by', 'quality_notes')
        }),
        ('Shipping', {
            'fields': ('courier_assigned', 'tracking_number', 'shipping_label_generated', 'shipped_at', 'delivered_at')
        })
    )

@admin.register(CourierAPIConfig)
class CourierAPIConfigAdmin(admin.ModelAdmin):
    list_display = ['courier_name', 'is_active', 'is_test_mode', 'requests_per_minute']
    list_filter = ['courier_name', 'is_active', 'is_test_mode']
    list_editable = ['is_active', 'is_test_mode']
    
    fieldsets = (
        ('Basic Configuration', {
            'fields': ('courier_name', 'base_url', 'is_active', 'is_test_mode')
        }),
        ('Steadfast API', {
            'fields': ('api_key', 'secret_key'),
            'description': 'For Steadfast courier service'
        }),
        ('Pathao API', {
            'fields': ('client_id', 'client_secret'),
            'description': 'For Pathao courier service'
        }),
        ('Rate Limiting', {
            'fields': ('requests_per_minute', 'daily_request_limit'),
            'classes': ('collapse',)
        })
    )

@admin.register(BulkOrderOperation)
class BulkOrderOperationAdmin(admin.ModelAdmin):
    list_display = ['operation_type', 'status', 'total_orders', 'processed_orders', 'failed_orders', 'created_by', 'created_at']
    list_filter = ['operation_type', 'status', 'created_at']
    readonly_fields = ['total_orders', 'processed_orders', 'failed_orders', 'started_at', 'completed_at']
    
    fieldsets = (
        ('Operation Details', {
            'fields': ('operation_type', 'status', 'created_by')
        }),
        ('Progress', {
            'fields': ('total_orders', 'processed_orders', 'failed_orders')
        }),
        ('Parameters', {
            'fields': ('operation_params',),
            'classes': ('collapse',)
        }),
        ('Results', {
            'fields': ('results', 'error_log'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(InventoryAlert)
class InventoryAlertAdmin(admin.ModelAdmin):
    list_display = ['product', 'alert_type', 'status', 'current_stock', 'acknowledged_by', 'created_at']
    list_filter = ['alert_type', 'status', 'created_at']
    search_fields = ['product__name', 'product__sku']
    list_editable = ['status']
    
    actions = ['mark_acknowledged', 'mark_resolved']
    
    def mark_acknowledged(self, request, queryset):
        queryset.update(status='acknowledged', acknowledged_by=request.user.crmuser, acknowledged_at=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} alerts as acknowledged")
    mark_acknowledged.short_description = "Mark as acknowledged"
    
    def mark_resolved(self, request, queryset):
        queryset.update(status='resolved', resolved_at=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} alerts as resolved")
    mark_resolved.short_description = "Mark as resolved"

@admin.register(ManagerIOSync)
class ManagerIOSyncAdmin(admin.ModelAdmin):
    list_display = ['sync_type', 'status', 'records_to_sync', 'records_synced', 'records_failed', 'created_at']
    list_filter = ['sync_type', 'status', 'created_at']
    readonly_fields = ['records_synced', 'records_failed', 'started_at', 'completed_at']

@admin.register(CampaignManagement)
class CampaignManagementAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_type', 'status', 'total_recipients', 'emails_sent', 'sms_sent', 'created_at']
    list_filter = ['campaign_type', 'status', 'created_at']
    search_fields = ['name', 'subject']
    list_editable = ['status']
    
    fieldsets = (
        ('Campaign Details', {
            'fields': ('name', 'campaign_type', 'status', 'created_by')
        }),
        ('Content', {
            'fields': ('subject', 'email_content', 'sms_content')
        }),
        ('Targeting', {
            'fields': ('target_customers', 'customer_filter_criteria')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at',)
        }),
        ('Results', {
            'fields': ('total_recipients', 'emails_sent', 'sms_sent', 'emails_opened', 'links_clicked'),
            'classes': ('collapse',)
        }),
        ('Costs', {
            'fields': ('estimated_cost', 'actual_cost'),
            'classes': ('collapse',)
        })
    )