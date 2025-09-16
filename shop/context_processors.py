# context_processors.py (shop/context_processors.py)
from .models import Category, MenuItem, Cart

def site_context(request):
    """Global context for all templates"""
    context = {
        'site_name': 'GrandShopBD',
        'main_categories': Category.objects.filter(is_active=True, parent=None)[:8],
        'main_menu': MenuItem.objects.filter(is_active=True, parent=None),
    }
    
    # Add cart info
    cart_count = 0
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            pass
    elif request.session.session_key:
        try:
            cart = Cart.objects.get(session_key=request.session.session_key)
            cart_count = cart.get_total_items()
        except Cart.DoesNotExist:
            pass
    
    context['cart_count'] = cart_count
    
    return context