# crm/models.py - Fixed version
from django.db import models
from django.conf import settings
from django.utils import timezone
from shop.models import Order, Product
import json

class CRMUser(models.Model):
    """CRM Users with specific permissions"""
    ROLE_CHOICES = [
        ('admin', 'CRM Admin'),
        ('manager', 'Order Manager'),
        ('support', 'Customer Support'),
        ('inventory', 'Inventory Manager'),
    ]
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='support')
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.get_role_display()})"

class Customer(models.Model):
    """Enhanced customer model for CRM"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('vip', 'VIP'),
        ('blocked', 'Blocked'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    alternative_phone = models.CharField(max_length=20, blank=True)
    
    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # CRM Fields
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    customer_type = models.CharField(max_length=50, default='retail')
    assigned_agent = models.ForeignKey(CRMUser, null=True, blank=True, on_delete=models.SET_NULL)
    
    # Statistics
    total_orders = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    average_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    last_order_date = models.DateTimeField(null=True, blank=True)
    
    # Engagement
    acquisition_source = models.CharField(max_length=100, blank=True, help_text="How they found us")
    preferred_contact_method = models.CharField(max_length=20, choices=[
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('sms', 'SMS'),
    ], default='email')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def update_statistics(self):
        """Update customer statistics from orders"""
        orders = Order.objects.filter(customer_email=self.email)
        self.total_orders = orders.count()
        if self.total_orders > 0:
            self.total_spent = sum(order.total_amount for order in orders)
            self.average_order_value = self.total_spent / self.total_orders
            self.last_order_date = orders.order_by('-created_at').first().created_at
        self.save()
    
    def __str__(self):
        return f"{self.name} ({self.email})"

class CustomerNote(models.Model):
    """Notes and interactions with customers"""
    NOTE_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('meeting', 'Meeting'),
        ('complaint', 'Complaint'),
        ('feedback', 'Feedback'),
        ('general', 'General Note'),
    ]
    
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='notes')
    created_by = models.ForeignKey(CRMUser, on_delete=models.CASCADE)
    note_type = models.CharField(max_length=20, choices=NOTE_TYPES, default='general')
    subject = models.CharField(max_length=200)
    content = models.TextField()
    is_important = models.BooleanField(default=False)
    follow_up_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.subject}"

class OrderManagement(models.Model):
    """Enhanced order management for CRM"""
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='crm_management')
    assigned_agent = models.ForeignKey(CRMUser, null=True, blank=True, on_delete=models.SET_NULL)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # Processing Info
    processing_notes = models.TextField(blank=True)
    estimated_processing_time = models.IntegerField(null=True, blank=True, help_text="Hours")
    actual_processing_time = models.IntegerField(null=True, blank=True, help_text="Hours")
    
    # Quality Control
    quality_checked = models.BooleanField(default=False)
    quality_checked_by = models.ForeignKey(CRMUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='quality_checks')
    quality_notes = models.TextField(blank=True)
    
    # Courier Integration
    courier_assigned = models.CharField(max_length=50, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    shipping_label_generated = models.BooleanField(default=False)
    
    # Timestamps
    processing_started_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"CRM - {self.order.order_number}"

class CourierAPIConfig(models.Model):
    """Configuration for courier service APIs"""
    COURIER_CHOICES = [
        ('steadfast', 'Steadfast'),
        ('pathao', 'Pathao'),
    ]
    
    courier_name = models.CharField(max_length=20, choices=COURIER_CHOICES, unique=True)
    api_key = models.CharField(max_length=200)
    secret_key = models.CharField(max_length=200, blank=True)
    client_id = models.CharField(max_length=200, blank=True)
    client_secret = models.CharField(max_length=200, blank=True)
    base_url = models.URLField()
    is_active = models.BooleanField(default=True)
    is_test_mode = models.BooleanField(default=True)
    
    # Rate limiting
    requests_per_minute = models.IntegerField(default=60)
    daily_request_limit = models.IntegerField(default=1000)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.get_courier_name_display()} API"

class BulkOrderOperation(models.Model):
    """Track bulk operations on orders"""
    OPERATION_TYPES = [
        ('status_update', 'Status Update'),
        ('courier_assign', 'Courier Assignment'),
        ('label_generate', 'Label Generation'),
        ('notification_send', 'Send Notifications'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    operation_type = models.CharField(max_length=20, choices=OPERATION_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_by = models.ForeignKey(CRMUser, on_delete=models.CASCADE)
    
    # Operation details
    total_orders = models.IntegerField()
    processed_orders = models.IntegerField(default=0)
    failed_orders = models.IntegerField(default=0)
    
    # Parameters (stored as JSON)
    operation_params = models.JSONField(default=dict)
    
    # Results
    results = models.JSONField(default=dict)
    error_log = models.TextField(blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_operation_type_display()} - {self.total_orders} orders"

class InventoryAlert(models.Model):
    """Inventory alerts and notifications"""
    ALERT_TYPES = [
        ('low_stock', 'Low Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('overstock', 'Overstock'),
        ('price_change', 'Price Change'),
        ('supplier_issue', 'Supplier Issue'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('acknowledged', 'Acknowledged'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    message = models.TextField()
    current_stock = models.IntegerField()
    threshold_value = models.IntegerField(null=True, blank=True)
    
    # Actions
    acknowledged_by = models.ForeignKey(CRMUser, null=True, blank=True, on_delete=models.SET_NULL)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.get_alert_type_display()}"

class ManagerIOSync(models.Model):
    """Manager.io synchronization logs"""
    SYNC_TYPES = [
        ('inventory', 'Inventory Update'),
        ('sales', 'Sales Data'),
        ('customers', 'Customer Data'),
        ('products', 'Product Data'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    sync_type = models.CharField(max_length=20, choices=SYNC_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Sync details
    records_to_sync = models.IntegerField(default=0)
    records_synced = models.IntegerField(default=0)
    records_failed = models.IntegerField(default=0)
    
    # API response
    manager_io_response = models.JSONField(default=dict)
    error_details = models.TextField(blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_sync_type_display()} - {self.status}"

class CampaignManagement(models.Model):
    """Email/SMS campaign management"""
    CAMPAIGN_TYPES = [
        ('email', 'Email Campaign'),
        ('sms', 'SMS Campaign'),
        ('both', 'Email + SMS'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    campaign_type = models.CharField(max_length=10, choices=CAMPAIGN_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Content
    subject = models.CharField(max_length=200, blank=True)
    email_content = models.TextField(blank=True)
    sms_content = models.TextField(blank=True)
    
    # Targeting
    target_customers = models.ManyToManyField(Customer, blank=True)
    customer_filter_criteria = models.JSONField(default=dict, help_text="Filter criteria for auto-targeting")
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    total_recipients = models.IntegerField(default=0)
    emails_sent = models.IntegerField(default=0)
    sms_sent = models.IntegerField(default=0)
    emails_opened = models.IntegerField(default=0)
    links_clicked = models.IntegerField(default=0)
    
    # Costs
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_by = models.ForeignKey(CRMUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_campaign_type_display()})"