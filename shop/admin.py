# shop/admin.py - Fixed version with proper imports
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from django.utils.safestring import mark_safe

# Import all models from the shop app
from .models import (
    CustomUser, VehicleBrand, VehicleModel, VehicleYear, VehicleChassis,
    Category, Brand, Product, ProductImage, ProductVehicle,
    Cart, CartItem, Order, OrderItem, CourierService, Shipment,
    Page, MenuItem, HeroBanner, SiteSetting
)

# Register User Model
admin.site.register(CustomUser, UserAdmin)

# Vehicle System Admin
@admin.register(VehicleBrand)
class VehicleBrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'models_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def models_count(self, obj):
        return obj.models.count()
    models_count.short_description = 'Models'

@admin.register(VehicleModel)
class VehicleModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'brand', 'slug', 'is_active', 'years_count', 'created_at']
    list_filter = ['brand', 'is_active', 'created_at']
    search_fields = ['name', 'brand__name']
    prepopulated_fields = {'slug': ('name',)}
    
    def years_count(self, obj):
        return obj.years.count()
    years_count.short_description = 'Years'

@admin.register(VehicleYear)
class VehicleYearAdmin(admin.ModelAdmin):
    list_display = ['model', 'year', 'is_active', 'chassis_count', 'created_at']
    list_filter = ['model__brand', 'year', 'is_active', 'created_at']
    search_fields = ['model__name', 'year']
    
    def chassis_count(self, obj):
        return obj.chassis_codes.count()
    chassis_count.short_description = 'Chassis Codes'

@admin.register(VehicleChassis)
class VehicleChassisAdmin(admin.ModelAdmin):
    list_display = ['code', 'year', 'description', 'is_active', 'created_at']
    list_filter = ['year__model__brand', 'is_active', 'created_at']
    search_fields = ['code', 'description', 'year__model__name']

# Category Admin
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'is_active', 'products_count', 'order']
    list_filter = ['parent', 'is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['order', 'is_active']
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products'

# Brand Admin
@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'products_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def products_count(self, obj):
        return obj.products.count()
    products_count.short_description = 'Products'

# Product System Admin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']

class ProductVehicleInline(admin.TabularInline):
    model = ProductVehicle
    extra = 1
    autocomplete_fields = ['vehicle_year', 'chassis_specific']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'brand', 'get_price', 'stock_quantity', 
        'stock_status', 'is_active', 'is_featured', 'created_at'
    ]
    list_filter = [
        'category', 'brand', 'stock_status', 'is_active', 
        'is_featured', 'is_universal_fit', 'created_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured', 'stock_quantity']
    inlines = [ProductImageInline, ProductVehicleInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category', 'brand')
        }),
        ('Description', {
            'fields': ('short_description', 'description')
        }),
        ('Pricing', {
            'fields': ('regular_price', 'offer_price')
        }),
        ('Stock', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'stock_status')
        }),
        ('Product Details', {
            'fields': ('weight', 'dimensions', 'warranty_period', 'origin_country')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Flags', {
            'fields': ('is_active', 'is_featured', 'is_universal_fit')
        })
    )
    
    def get_price(self, obj):
        return f"৳{obj.get_price()}"
    get_price.short_description = 'Price'

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_thumbnail', 'is_primary', 'order']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_primary', 'order']
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return 'No Image'
    image_thumbnail.short_description = 'Thumbnail'

# Cart Admin
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_key', 'items_count', 'total_price', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'session_key']
    
    def items_count(self, obj):
        return obj.get_total_items()
    items_count.short_description = 'Items'
    
    def total_price(self, obj):
        return f"৳{obj.get_total_price()}"
    total_price.short_description = 'Total'

# Order System Admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_sku', 'total_price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer_name', 'customer_phone', 'status', 
        'payment_status', 'total_amount', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'fraud_check_status']
    search_fields = ['order_number', 'customer_name', 'customer_email', 'customer_phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    list_editable = ['status', 'payment_status']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_phone')
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'shipping_city', 'shipping_postal_code', 'shipping_cost')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'discount_amount', 'total_amount')
        }),
        ('Additional Information', {
            'fields': ('notes', 'fraud_check_status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing order
            return self.readonly_fields + ['subtotal', 'total_amount']
        return self.readonly_fields

# Courier and Shipping Admin
@admin.register(CourierService)
class CourierServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'delivery_time', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']
    list_editable = ['is_active']

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['order', 'courier_service', 'tracking_number', 'status', 'created_at']
    list_filter = ['courier_service', 'status', 'created_at']
    search_fields = ['order__order_number', 'tracking_number']
    list_editable = ['status']

# CMS Admin
@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug', 'is_published', 'created_at', 'updated_at']
    list_filter = ['is_published', 'created_at']
    search_fields = ['title', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ['title', 'parent', 'link_type', 'order', 'is_active']
    list_filter = ['link_type', 'is_active']
    search_fields = ['title']
    list_editable = ['order', 'is_active']

# Banner Admin
@admin.register(HeroBanner)
class HeroBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'banner_type', 'order', 'is_active', 'created_at']
    list_filter = ['banner_type', 'is_active', 'created_at']
    search_fields = ['title', 'subtitle']
    list_editable = ['order', 'is_active']

# Settings Admin
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ['key', 'value_preview', 'description', 'updated_at']
    search_fields = ['key', 'value']
    
    def value_preview(self, obj):
        return obj.value[:100] + '...' if len(obj.value) > 100 else obj.value
    value_preview.short_description = 'Value'

# Customize admin site
admin.site.site_header = 'GrandShopBD Admin'
admin.site.site_title = 'GrandShopBD Admin Portal'
admin.site.index_title = 'Welcome to GrandShopBD Administration'