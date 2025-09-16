# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Min, Max
from django.core.paginator import Paginator
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from decimal import Decimal  # Add this import too
import json

# ADD THIS LINE - Import all models from models.py
from .models import *

# Home Page View
class HomeView(TemplateView):
    template_name = 'shop/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'hero_banners': HeroBanner.objects.filter(is_active=True)[:3],
            'featured_products': Product.objects.filter(is_active=True, is_featured=True)[:8],
            'categories': Category.objects.filter(is_active=True, parent=None)[:12],
            'vehicle_brands': VehicleBrand.objects.filter(is_active=True)[:8],
        })
        return context

# Vehicle Filter Views
def get_vehicle_models(request):
    """AJAX view to get models for a brand"""
    brand_id = request.GET.get('brand_id')
    if brand_id:
        models = VehicleModel.objects.filter(brand_id=brand_id, is_active=True)
        data = [{'id': model.id, 'name': model.name, 'image': model.image.url if model.image else ''} 
                for model in models]
        return JsonResponse({'models': data})
    return JsonResponse({'models': []})

def get_vehicle_years(request):
    """AJAX view to get years for a model"""
    model_id = request.GET.get('model_id')
    if model_id:
        years = VehicleYear.objects.filter(model_id=model_id, is_active=True)
        data = [{'id': year.id, 'year': year.year} for year in years]
        return JsonResponse({'years': data})
    return JsonResponse({'years': []})

def get_chassis_codes(request):
    """AJAX view to get chassis codes for a year"""
    year_id = request.GET.get('year_id')
    if year_id:
        chassis_codes = VehicleChassis.objects.filter(year_id=year_id, is_active=True)
        data = [{'id': chassis.id, 'code': chassis.code, 'description': chassis.description} 
                for chassis in chassis_codes]
        return JsonResponse({'chassis_codes': data})
    return JsonResponse({'chassis_codes': []})

# Product Views
class ProductListView(ListView):
    model = Product
    template_name = 'shop/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).select_related('brand', 'category')
        
        # Search functionality
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(sku__icontains=search_query)
            )
        
        # Category filter
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, is_active=True)
            # Get category and all its children
            categories = [category]
            categories.extend(category.children.all())
            queryset = queryset.filter(category__in=categories)
        
        # Brand filter
        brand_ids = self.request.GET.getlist('brand')
        if brand_ids:
            queryset = queryset.filter(brand_id__in=brand_ids)
        
        # Price filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(regular_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(regular_price__lte=max_price)
        
        # Vehicle filter
        vehicle_year_id = self.request.GET.get('vehicle_year')
        chassis_id = self.request.GET.get('chassis')
        if vehicle_year_id:
            if chassis_id:
                queryset = queryset.filter(
                    Q(compatible_vehicles=vehicle_year_id, productvehicle__chassis_specific=chassis_id) |
                    Q(is_universal_fit=True)
                )
            else:
                queryset = queryset.filter(
                    Q(compatible_vehicles=vehicle_year_id) |
                    Q(is_universal_fit=True)
                )
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'name')
        sort_options = {
            'name': 'name',
            'price_low': 'regular_price',
            'price_high': '-regular_price',
            'newest': '-created_at',
        }
        if sort_by in sort_options:
            queryset = queryset.order_by(sort_options[sort_by])
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter options
        context.update({
            'brands': Brand.objects.filter(is_active=True, products__is_active=True).distinct(),
            'categories': Category.objects.filter(is_active=True, parent=None),
            'vehicle_brands': VehicleBrand.objects.filter(is_active=True),
            'current_filters': self.request.GET,
        })
        
        # Add selected vehicle info if available
        vehicle_year_id = self.request.GET.get('vehicle_year')
        if vehicle_year_id:
            try:
                vehicle_year = VehicleYear.objects.get(id=vehicle_year_id)
                context['selected_vehicle'] = vehicle_year
            except VehicleYear.DoesNotExist:
                pass
        
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'shop/product_detail.html'
    context_object_name = 'product'
    
    def get_object(self):
        return get_object_or_404(
            Product.objects.select_related('brand', 'category').prefetch_related('images'),
            slug=self.kwargs['slug'],
            is_active=True
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Related products
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        
        # Compatible vehicles
        compatible_vehicles = product.compatible_vehicles.select_related(
            'model__brand'
        )[:10]
        
        context.update({
            'related_products': related_products,
            'compatible_vehicles': compatible_vehicles,
        })
        
        return context
# Cart Views
@require_http_methods(["POST"])
def add_to_cart(request):
    """Add product to cart via AJAX"""
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
            
            # Get or create cart
            if request.user.is_authenticated:
                cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                if not request.session.session_key:
                    request.session.create()
                cart, created = Cart.objects.get_or_create(
                    session_key=request.session.session_key
                )
            
            # Add or update cart item
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            # Check stock
            if cart_item.quantity > product.stock_quantity:
                cart_item.quantity = product.stock_quantity
                cart_item.save()
                return JsonResponse({
                    'success': False,
                    'message': f'Only {product.stock_quantity} items available in stock'
                })
            
            return JsonResponse({
                'success': True,
                'message': 'Product added to cart',
                'cart_count': cart.get_total_items(),
                'cart_total': float(cart.get_total_price())
            })
            
        except Product.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Product not found'
            })
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})

def cart_view(request):
    """Display cart contents"""
    cart = None
    cart_items = []
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.select_related('product').all()
        except Cart.DoesNotExist:
            pass
    else:
        if request.session.session_key:
            try:
                cart = Cart.objects.get(session_key=request.session.session_key)
                cart_items = cart.items.select_related('product').all()
            except Cart.DoesNotExist:
                pass
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'shop/cart.html', context)

@require_http_methods(["POST"])
def update_cart_item(request):
    """Update cart item quantity via AJAX"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
        else:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__session_key=request.session.session_key
            )
        
        if quantity <= 0:
            cart_item.delete()
            return JsonResponse({
                'success': True,
                'message': 'Item removed from cart',
                'removed': True
            })
        
        # Check stock
        if quantity > cart_item.product.stock_quantity:
            return JsonResponse({
                'success': False,
                'message': f'Only {cart_item.product.stock_quantity} items available'
            })
        
        cart_item.quantity = quantity
        cart_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Cart updated',
            'item_total': float(cart_item.get_total_price()),
            'cart_total': float(cart_item.cart.get_total_price()),
            'cart_count': cart_item.cart.get_total_items()
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cart item not found'
        })

@require_http_methods(["POST"])
def remove_cart_item(request):
    """Remove item from cart"""
    item_id = request.POST.get('item_id')
    
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__user=request.user
            )
        else:
            cart_item = CartItem.objects.get(
                id=item_id,
                cart__session_key=request.session.session_key
            )
        
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart'
        })
        
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Cart item not found'
        })

# Checkout Views
def checkout_view(request):
    """Checkout page"""
    cart = None
    cart_items = []
    
    # Get cart
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.select_related('product').all()
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
    else:
        if request.session.session_key:
            try:
                cart = Cart.objects.get(session_key=request.session.session_key)
                cart_items = cart.items.select_related('product').all()
            except Cart.DoesNotExist:
                messages.error(request, 'Your cart is empty')
                return redirect('cart')
        else:
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
    
    if not cart_items:
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    
    # Calculate totals
    subtotal = cart.get_total_price()
    shipping_cost = Decimal('50.00')  # Fixed shipping for now
    total = subtotal + shipping_cost
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'total': total,
        'courier_services': CourierService.objects.filter(is_active=True),
    }
    
    return render(request, 'shop/checkout.html', context)

@require_http_methods(["POST"])
def process_order(request):
    """Process order submission"""
    # Get cart
    cart = None
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
    else:
        if request.session.session_key:
            try:
                cart = Cart.objects.get(session_key=request.session.session_key)
            except Cart.DoesNotExist:
                messages.error(request, 'Your cart is empty')
                return redirect('cart')
        else:
            messages.error(request, 'Your cart is empty')
            return redirect('cart')
    
    cart_items = cart.items.select_related('product').all()
    if not cart_items:
        messages.error(request, 'Your cart is empty')
        return redirect('cart')
    
    # Validate stock
    for item in cart_items:
        if item.quantity > item.product.stock_quantity:
            messages.error(request, f'Only {item.product.stock_quantity} of {item.product.name} available')
            return redirect('cart')
    
    # Create order
    subtotal = cart.get_total_price()
    shipping_cost = Decimal('50.00')
    total = subtotal + shipping_cost
    
    order = Order.objects.create(
        user=request.user if request.user.is_authenticated else None,
        customer_name=request.POST.get('customer_name'),
        customer_email=request.POST.get('customer_email'),
        customer_phone=request.POST.get('customer_phone'),
        shipping_address=request.POST.get('shipping_address'),
        shipping_city=request.POST.get('shipping_city'),
        shipping_postal_code=request.POST.get('shipping_postal_code', ''),
        shipping_cost=shipping_cost,
        subtotal=subtotal,
        total_amount=total,
        notes=request.POST.get('notes', ''),
    )
    
    # Create order items and update stock
    for cart_item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=cart_item.product,
            quantity=cart_item.quantity,
            unit_price=cart_item.product.get_price(),
        )
        
        # Update stock
        cart_item.product.stock_quantity -= cart_item.quantity
        cart_item.product.save()
    
    # Create shipment if courier service selected
    courier_id = request.POST.get('courier_service')
    if courier_id:
        try:
            courier = CourierService.objects.get(id=courier_id, is_active=True)
            Shipment.objects.create(
                order=order,
                courier_service=courier
            )
        except CourierService.DoesNotExist:
            pass
    
    # Clear cart
    cart.items.all().delete()
    
    messages.success(request, f'Order {order.order_number} placed successfully!')
    return redirect('order_detail', order_number=order.order_number)

# Order Views
class OrderDetailView(DetailView):
    model = Order
    template_name = 'shop/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'
    
    def get_queryset(self):
        queryset = Order.objects.prefetch_related('items__product')
        
        # Restrict access for authenticated users
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(user=self.request.user) | Q(customer_email=self.request.user.email)
            )
        
        return queryset

@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(
        Q(user=request.user) | Q(customer_email=request.user.email)
    ).order_by('-created_at')
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
    }
    
    return render(request, 'shop/order_history.html', context)

# Search Views
def search_view(request):
    """Product search"""
    query = request.GET.get('q', '').strip()
    products = []
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__name__icontains=query),
            is_active=True
        ).select_related('brand', 'category').distinct()
        
        # Paginate results
        paginator = Paginator(products, 20)
        page_number = request.GET.get('page')
        products = paginator.get_page(page_number)
    
    context = {
        'query': query,
        'products': products,
    }
    
    return render(request, 'shop/search_results.html', context)

def ajax_search(request):
    """AJAX search for autocomplete"""
    query = request.GET.get('q', '').strip()
    results = []
    
    if query and len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(sku__icontains=query),
            is_active=True
        )[:10]
        
        results = [{
            'id': product.id,
            'name': product.name,
            'sku': product.sku,
            'price': float(product.get_price()),
            'url': product.get_absolute_url(),
            'image': product.images.filter(is_primary=True).first().image.url if product.images.filter(is_primary=True).exists() else '',
        } for product in products]
    
    return JsonResponse({'results': results})

# Buy Now Views (Direct checkout)
@require_http_methods(["POST"])
def buy_now(request):
    """Direct checkout for single product"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Check stock
        if quantity > product.stock_quantity:
            messages.error(request, f'Only {product.stock_quantity} items available')
            return redirect('product_detail', slug=product.slug)
        
        # Store in session for checkout
        request.session['buy_now_item'] = {
            'product_id': product.id,
            'quantity': quantity,
        }
        
        return redirect('buy_now_checkout')
        
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        return redirect('home')

def buy_now_checkout(request):
    """Checkout page for buy now"""
    buy_now_item = request.session.get('buy_now_item')
    
    if not buy_now_item:
        messages.error(request, 'No item selected for purchase')
        return redirect('home')
    
    try:
        product = Product.objects.get(id=buy_now_item['product_id'], is_active=True)
        quantity = buy_now_item['quantity']
        
        # Check stock again
        if quantity > product.stock_quantity:
            messages.error(request, f'Only {product.stock_quantity} items available')
            del request.session['buy_now_item']
            return redirect('product_detail', slug=product.slug)
        
        subtotal = product.get_price() * quantity
        shipping_cost = Decimal('50.00')
        total = subtotal + shipping_cost
        
        context = {
            'product': product,
            'quantity': quantity,
            'subtotal': subtotal,
            'shipping_cost': shipping_cost,
            'total': total,
            'courier_services': CourierService.objects.filter(is_active=True),
        }
        
        return render(request, 'shop/buy_now_checkout.html', context)
        
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        del request.session['buy_now_item']
        return redirect('home')

@require_http_methods(["POST"])
def process_buy_now_order(request):
    """Process buy now order"""
    buy_now_item = request.session.get('buy_now_item')
    
    if not buy_now_item:
        messages.error(request, 'No item selected for purchase')
        return redirect('home')
    
    try:
        product = Product.objects.get(id=buy_now_item['product_id'], is_active=True)
        quantity = buy_now_item['quantity']
        
        # Check stock
        if quantity > product.stock_quantity:
            messages.error(request, f'Only {product.stock_quantity} items available')
            return redirect('product_detail', slug=product.slug)
        
        # Create order
        subtotal = product.get_price() * quantity
        shipping_cost = Decimal('50.00')
        total = subtotal + shipping_cost
        
        order = Order.objects.create(
            user=request.user if request.user.is_authenticated else None,
            customer_name=request.POST.get('customer_name'),
            customer_email=request.POST.get('customer_email'),
            customer_phone=request.POST.get('customer_phone'),
            shipping_address=request.POST.get('shipping_address'),
            shipping_city=request.POST.get('shipping_city'),
            shipping_postal_code=request.POST.get('shipping_postal_code', ''),
            shipping_cost=shipping_cost,
            subtotal=subtotal,
            total_amount=total,
            notes=request.POST.get('notes', ''),
        )
        
        # Create order item
        OrderItem.objects.create(
            order=order,
            product=product,
            quantity=quantity,
            unit_price=product.get_price(),
        )
        
        # Update stock
        product.stock_quantity -= quantity
        product.save()
        
        # Create shipment if courier service selected
        courier_id = request.POST.get('courier_service')
        if courier_id:
            try:
                courier = CourierService.objects.get(id=courier_id, is_active=True)
                Shipment.objects.create(
                    order=order,
                    courier_service=courier
                )
            except CourierService.DoesNotExist:
                pass
        
        # Clear session
        del request.session['buy_now_item']
        
        messages.success(request, f'Order {order.order_number} placed successfully!')
        return redirect('order_detail', order_number=order.order_number)
        
    except Product.DoesNotExist:
        messages.error(request, 'Product not found')
        del request.session['buy_now_item']
        return redirect('home')

# Category and Brand Views
class CategoryProductsView(ListView):
    model = Product
    template_name = 'shop/category_products.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        
        # Get category and all its children
        categories = [self.category]
        
        def get_all_children(category):
            children = category.children.filter(is_active=True)
            for child in children:
                categories.append(child)
                get_all_children(child)
        
        get_all_children(self.category)
        
        return Product.objects.filter(
            category__in=categories,
            is_active=True
        ).select_related('brand', 'category').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class BrandProductsView(ListView):
    model = Product
    template_name = 'shop/brand_products.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        self.brand = get_object_or_404(Brand, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            brand=self.brand,
            is_active=True
        ).select_related('brand', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brand'] = self.brand
        return context

# Page Views
class PageDetailView(DetailView):
    model = Page
    template_name = 'shop/page_detail.html'
    context_object_name = 'page'
    
    def get_queryset(self):
        return Page.objects.filter(is_published=True)
    

def get_vehicle_brands(request):
    """AJAX view to get all vehicle brands"""
    from django.http import JsonResponse
    
    brands = VehicleBrand.objects.filter(is_active=True).values(
        'id', 'name', 'slug', 'logo'
    )
    
    brands_data = []
    for brand in brands:
        brand_data = {
            'id': brand['id'],
            'name': brand['name'], 
            'slug': brand['slug'],
            'logo': brand['logo'] if brand['logo'] else None
        }
        brands_data.append(brand_data)
    
    return JsonResponse({'brands': brands_data})