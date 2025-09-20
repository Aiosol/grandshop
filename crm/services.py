# crm/services.py
import requests
import json
from django.conf import settings
from .models import CourierAPIConfig

class SteadfastAPI:
    """Steadfast Courier API Integration"""
    
    def __init__(self):
        try:
            config = CourierAPIConfig.objects.get(courier_name='steadfast', is_active=True)
            self.api_key = config.api_key
            self.secret_key = config.secret_key
            self.base_url = config.base_url or "https://portal.steadfast.com.bd/api/v1"
            self.is_test = config.is_test_mode
        except CourierAPIConfig.DoesNotExist:
            # Fallback to hardcoded values
            self.api_key = "lvbzordcng9xvhx1rkc7gw3gjxngyzzw"
            self.secret_key = "wtljzusnzyeditpwhnwthxky"
            self.base_url = "https://portal.steadfast.com.bd/api/v1"
            self.is_test = True
    
    def create_parcel(self, order_data):
        """Create a parcel/shipment"""
        url = f"{self.base_url}/create_order"
        
        headers = {
            'Api-Key': self.api_key,
            'Secret-Key': self.secret_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            "invoice": order_data['order_number'],
            "recipient_name": order_data['customer_name'],
            "recipient_phone": order_data['customer_phone'],
            "recipient_address": order_data['shipping_address'],
            "cod_amount": float(order_data['total_amount']),
            "note": order_data.get('notes', ''),
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}
    
    def track_parcel(self, tracking_number):
        """Track a parcel"""
        url = f"{self.base_url}/status_by_trackingcode/{tracking_number}"
        
        headers = {
            'Api-Key': self.api_key,
            'Secret-Key': self.secret_key,
        }
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

class PathaoAPI:
    """Pathao Courier API Integration"""
    
    def __init__(self):
        try:
            config = CourierAPIConfig.objects.get(courier_name='pathao', is_active=True)
            self.client_id = config.client_id
            self.client_secret = config.client_secret
            self.base_url = config.base_url or "https://api-hermes.pathao.com"
            self.is_test = config.is_test_mode
        except CourierAPIConfig.DoesNotExist:
            # Fallback to hardcoded values
            self.client_id = "QBeXrE5byK"
            self.client_secret = "m9mrYMHyxFx7Wp2ht290a1gCCoS4xHwGaoiDobPh"
            self.base_url = "https://api-hermes.pathao.com"
            self.is_test = True
        
        self.access_token = None
    
    def get_access_token(self):
        """Get OAuth access token"""
        if self.access_token:
            return self.access_token
        
        url = f"{self.base_url}/aladdin/api/v1/issue-token"
        
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": "your-username",  # Replace with actual username
            "password": "your-password",  # Replace with actual password
            "grant_type": "password"
        }
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data.get('access_token')
            return self.access_token
        except requests.exceptions.RequestException as e:
            return None
    
    def create_order(self, order_data):
        """Create an order"""
        token = self.get_access_token()
        if not token:
            return {'error': 'Failed to get access token'}
        
        url = f"{self.base_url}/aladdin/api/v1/orders"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "store_id": 1,  # Your store ID
            "merchant_order_id": order_data['order_number'],
            "sender_name": "GrandShopBD",
            "sender_phone": "+8801234567890",
            "recipient_name": order_data['customer_name'],
            "recipient_phone": order_data['customer_phone'],
            "recipient_address": order_data['shipping_address'],
            "recipient_city": order_data['city_id'],  # Pathao city ID
            "recipient_zone": order_data['zone_id'],  # Pathao zone ID
            "delivery_type": 48,  # 48 hours delivery
            "item_type": 2,  # Parcel
            "special_instruction": order_data.get('notes', ''),
            "item_quantity": order_data['total_items'],
            "item_weight": 0.5,  # Default weight in kg
            "amount_to_collect": float(order_data['total_amount']),
            "item_description": "Automotive Parts"
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': str(e)}

class ManagerIOAPI:
    """Manager.io API Integration (placeholder for future implementation)"""
    
    def __init__(self):
        self.api_key = ""  # Will be configured later
        self.base_url = ""  # Will be configured later
    
    def sync_inventory(self):
        """Sync inventory with Manager.io"""
        # Placeholder for future implementation
        return {'status': 'pending', 'message': 'Manager.io API integration pending'}
    
    def sync_sales_data(self):
        """Sync sales data with Manager.io"""
        # Placeholder for future implementation
        return {'status': 'pending', 'message': 'Manager.io API integration pending'}
    
    def sync_customer_data(self):
        """Sync customer data with Manager.io"""
        # Placeholder for future implementation
        return {'status': 'pending', 'message': 'Manager.io API integration pending'}