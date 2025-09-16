# GrandShopBD - Automotive Parts E-commerce Platform

A comprehensive Django-based e-commerce platform specialized for automotive parts in Bangladesh.

## Features

- Advanced vehicle-based filtering system
- Mobile-first responsive design
- Dual purchase options (Add to Cart & Buy Now)
- Complete order management
- Vehicle compatibility system
- Multiple courier integration
- Admin panel for complete control

## Quick Setup

1. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run deployment:
```bash
python deploy.py
```

4. Start development server:
```bash
python manage.py runserver
```

## Admin Access

- URL: http://localhost:8000/admin
- Username: admin
- Password: admin123

## Project Structure

- `shop/` - Main application
- `templates/` - HTML templates
- `static/` - CSS, JS, images
- `media/` - User uploads

## Production Deployment

1. Update settings for production
2. Configure MySQL database
3. Set up Redis cache
4. Configure email settings
5. Set up SSL certificate

For detailed documentation, see the admin panel after setup.
