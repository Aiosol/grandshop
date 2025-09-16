#shop/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.HomeView.as_view(), name='home'),
    
    # Vehicle Filter AJAX
    path('ajax/vehicle-brands/', views.get_vehicle_brands, name='get_vehicle_brands'),  # ADD THIS LINE
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
]