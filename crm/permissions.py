# CRM Permissions - crm/permissions.py
from django.contrib.auth.decorators import user_passes_test
from functools import wraps

def crm_required(view_func):
    """Decorator to require CRM user access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'crmuser'):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("CRM access required")
        return view_func(request, *args, **kwargs)
    return wrapper

def crm_admin_required(view_func):
    """Decorator to require CRM admin access"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not hasattr(request.user, 'crmuser') or request.user.crmuser.role not in ['admin', 'manager']:
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("CRM admin access required")
        return view_func(request, *args, **kwargs)
    return wrapper