# seed_db.py
import os
import django
import sys
from decimal import Decimal

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql.settings')
django.setup()

from crm.models import Customer, Product, Order
from django.db import transaction


def clear_database():
    """Clear existing data"""
    print("Clearing existing data...")
    Order.objects.all().delete()
    Customer.objects.all().delete()
    Product.objects.all().delete()
    print("Database cleared!")


def seed_customers():
    """Seed sample customers"""
    print("Seeding customers...")
    
    customers_data = [
        {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'phone': '+12345678901'
        },
        {
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'phone': '+19876543210'
        },
        {
            'name': 'Bob Johnson',
            'email': 'bob.johnson@example.com',
            'phone': '555-123-4567'
        },
        {
            'name': 'Alice Brown',
            'email': 'alice.brown@example.com',
            'phone': None  # No phone
        },
        {
            'name': 'Charlie Wilson',
            'email': 'charlie.wilson@example.com',
            'phone': '+441234567890'
        }
    ]
    
    customers = []
    for data in customers_data:
        customer = Customer.objects.create(**data)
        customers.append(customer)
        print(f"  Created customer: {customer.name}")
    
    print(f"Created {len(customers)} customers")
    return customers


def seed_products():
    """Seed sample products"""
    print("Seeding products...")
    
    products_data = [
        {
            'name': 'Laptop Pro',
            'price': Decimal('1299.99'),
            'stock': 25,
            'description': 'High-performance laptop'
        },
        {
            'name': 'Smartphone X',
            'price': Decimal('899.99'),
            'stock': 50,
            'description': 'Latest smartphone model'
        },
        {
            'name': 'Wireless Headphones',
            'price': Decimal('199.99'),
            'stock': 100,
            'description': 'Noise-cancelling headphones'
        },
        {
            'name': 'Monitor 4K',
            'price': Decimal('499.99'),
            'stock': 30,
            'description': '27-inch 4K monitor'
        },
        {
            'name': 'Keyboard Mechanical',
            'price': Decimal('129.99'),
            'stock': 75,
            'description': 'RGB mechanical keyboard'
        },
        {
            'name': 'Mouse Gaming',
            'price': Decimal('79.99'),
            'stock': 120,
            'description': 'Wireless gaming mouse'
        }
    ]
    
    products = []
    for data in products_data:
        product = Product.objects.create(**data)
        products.append(product)
        print(f"  Created product: {product.name} - ${product.price}")
    
    print(f"Created {len(products)} products")
    return products


def seed_orders(customers, products):
    """Seed sample orders"""
    print("Seeding orders...")
    
    orders_data = [
        {
            'customer': customers[0],  # John Doe
            'products': [products[0], products[1], products[2]],  # Laptop, Phone, Headphones
            'status': 'COMPLETED'
        },
        {
            'customer': customers[1],  # Jane Smith
            'products': [products[1], products[3]],  # Phone, Monitor
            'status': 'PROCESSING'
        },
        {
            'customer': customers[2],  # Bob Johnson
            'products': [products[4], products[5]],  # Keyboard, Mouse
            'status': 'PENDING'
        },
        {
            'customer': customers[3],  # Alice Brown
            'products': [products[0], products[3], products[4]],  # Laptop, Monitor, Keyboard
            'status': 'COMPLETED'
        },
        {
            'customer': customers[4],  # Charlie Wilson
            'products': [products[2], products[5]],  # Headphones, Mouse
            'status': 'COMPLETED'
        }
    ]
    
    orders = []
    for data in orders_data:
        order = Order.objects.create(
            customer=data['customer'],
            status=data['status']
        )
        order.products.set(data['products'])
        order.calculate_total()
        orders.append(order)
        
        product_names = ', '.join([p.name for p in data['products']])
        print(f"  Created order: {order.customer.name} - {product_names} - Total: ${order.total_amount}")
    
    print(f"Created {len(orders)} orders")
    return orders


def seed_database():
    """Main seeding function"""
    print("=" * 50)
    print("Starting database seeding...")
    print("=" * 50)
    
    try:
        with transaction.atomic():
            # Clear existing data
            clear_database()
            
            # Seed new data
            customers = seed_customers()
            products = seed_products()
            orders = seed_orders(customers, products)
            
            # Print summary
            print("\n" + "=" * 50)
            print("Database Seeding Complete!")
            print("=" * 50)
            print(f"Total Customers: {Customer.objects.count()}")
            print(f"Total Products: {Product.objects.count()}")
            print(f"Total Orders: {Order.objects.count()}")
            
            # Print sample order details
            print("\nSample Order Details:")
            print("-" * 30)
            for order in Order.objects.all()[:3]:  # Show first 3 orders
                print(f"Order ID: {order.id}")
                print(f"Customer: {order.customer.name}")
                print(f"Products: {', '.join([p.name for p in order.products.all()])}")
                print(f"Total: ${order.total_amount}")
                print(f"Status: {order.status}")
                print("-" * 20)
            
    except Exception as e:
        print(f"Error during seeding: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    seed_database()