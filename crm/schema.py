# crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from decimal import Decimal
import re
import uuid

from .models import Customer, Product, Order


# ============================================
# GraphQL Types
# ============================================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = '__all__'


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = '__all__'


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = '__all__'
    
    total_amount = graphene.Decimal()
    
    def resolve_total_amount(self, info):
        return self.calculate_total()


# ============================================
# Input Types
# ============================================
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.String(required=True)
    product_ids = graphene.List(graphene.String, required=True)
    order_date = graphene.DateTime()


# ============================================
# Response Types for Errors
# ============================================
class ErrorType(graphene.ObjectType):
    field = graphene.String()
    message = graphene.String()


class BulkCreateResponse(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    errors = graphene.List(ErrorType)


# ============================================
# Mutation: CreateCustomer
# ============================================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()
    errors = graphene.List(ErrorType)
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        if not phone:
            return True
        # Accept formats: +1234567890, 123-456-7890, 1234567890
        pattern = r'^(\+\d{1,3}[- ]?)?\d{3}[- ]?\d{3}[- ]?\d{4}$'
        return bool(re.match(pattern, phone))
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        # Validate required fields
        if not input.name or not input.name.strip():
            errors.append(ErrorType(
                field='name',
                message='Name is required'
            ))
        
        # Validate email format
        try:
            validate_email(input.email)
        except ValidationError:
            errors.append(ErrorType(
                field='email',
                message='Invalid email format'
            ))
        
        # Validate email uniqueness
        if Customer.objects.filter(email=input.email).exists():
            errors.append(ErrorType(
                field='email',
                message='Email already exists'
            ))
        
        # Validate phone format if provided
        if input.phone and not cls.validate_phone(input.phone):
            errors.append(ErrorType(
                field='phone',
                message='Phone must be in format: +1234567890 or 123-456-7890'
            ))
        
        # Return errors if any
        if errors:
            return CreateCustomer(errors=errors)
        
        try:
            # Create customer
            customer = Customer.objects.create(
                name=input.name.strip(),
                email=input.email.lower(),
                phone=input.phone if input.phone else None
            )
            
            return CreateCustomer(
                customer=customer,
                message='Customer created successfully',
                errors=[]
            )
            
        except Exception as e:
            return CreateCustomer(
                errors=[ErrorType(field='__all__', message=str(e))]
            )


# ============================================
# Mutation: BulkCreateCustomers
# ============================================
class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)
    
    result = graphene.Field(BulkCreateResponse)
    
    @classmethod
    def mutate(cls, root, info, inputs):
        customers = []
        errors = []
        
        with transaction.atomic():
            for index, customer_input in enumerate(inputs):
                try:
                    # Validate required fields
                    if not customer_input.name or not customer_input.name.strip():
                        errors.append(ErrorType(
                            field=f'inputs[{index}].name',
                            message='Name is required'
                        ))
                        continue
                    
                    # Validate email format
                    try:
                        validate_email(customer_input.email)
                    except ValidationError:
                        errors.append(ErrorType(
                            field=f'inputs[{index}].email',
                            message='Invalid email format'
                        ))
                        continue
                    
                    # Check for duplicate email in database
                    if Customer.objects.filter(email=customer_input.email).exists():
                        errors.append(ErrorType(
                            field=f'inputs[{index}].email',
                            message='Email already exists'
                        ))
                        continue
                    
                    # Check for duplicate email in current batch
                    email_in_batch = any(
                        c.email == customer_input.email 
                        for c in customers
                    )
                    if email_in_batch:
                        errors.append(ErrorType(
                            field=f'inputs[{index}].email',
                            message='Duplicate email in batch'
                        ))
                        continue
                    
                    # Validate phone format if provided
                    if customer_input.phone and not CreateCustomer.validate_phone(customer_input.phone):
                        errors.append(ErrorType(
                            field=f'inputs[{index}].phone',
                            message='Invalid phone format'
                        ))
                        continue
                    
                    # Create customer
                    customer = Customer.objects.create(
                        name=customer_input.name.strip(),
                        email=customer_input.email.lower(),
                        phone=customer_input.phone if customer_input.phone else None
                    )
                    customers.append(customer)
                    
                except Exception as e:
                    errors.append(ErrorType(
                        field=f'inputs[{index}]',
                        message=str(e)
                    ))
        
        return BulkCreateCustomers(
            result=BulkCreateResponse(
                customers=customers,
                errors=errors
            )
        )


# ============================================
# Mutation: CreateProduct
# ============================================
class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    errors = graphene.List(ErrorType)
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        # Validate name
        if not input.name or not input.name.strip():
            errors.append(ErrorType(
                field='name',
                message='Product name is required'
            ))
        
        # Validate price
        if input.price <= Decimal('0'):
            errors.append(ErrorType(
                field='price',
                message='Price must be greater than 0'
            ))
        
        # Validate stock
        if input.stock is not None and input.stock < 0:
            errors.append(ErrorType(
                field='stock',
                message='Stock cannot be negative'
            ))
        
        if errors:
            return CreateProduct(errors=errors)
        
        try:
            # Create product
            product = Product.objects.create(
                name=input.name.strip(),
                price=input.price,
                stock=input.stock if input.stock is not None else 0
            )
            
            return CreateProduct(
                product=product,
                errors=[]
            )
            
        except Exception as e:
            return CreateProduct(
                errors=[ErrorType(field='__all__', message=str(e))]
            )


# ============================================
# Mutation: CreateOrder
# ============================================
class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    errors = graphene.List(ErrorType)
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        customer = None
        products = []
        
        # Validate customer exists
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            errors.append(ErrorType(
                field='customer_id',
                message=f'Customer with ID {input.customer_id} not found'
            ))
        except ValueError:
            errors.append(ErrorType(
                field='customer_id',
                message='Invalid customer ID format'
            ))
        
        # Validate products
        if not input.product_ids:
            errors.append(ErrorType(
                field='product_ids',
                message='At least one product is required'
            ))
        else:
            for idx, product_id in enumerate(input.product_ids):
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    errors.append(ErrorType(
                        field=f'product_ids[{idx}]',
                        message=f'Product with ID {product_id} not found'
                    ))
                except ValueError:
                    errors.append(ErrorType(
                        field=f'product_ids[{idx}]',
                        message=f'Invalid product ID format: {product_id}'
                    ))
        
        # Check stock availability (optional enhancement)
        for product in products:
            if product.stock <= 0:
                errors.append(ErrorType(
                    field='product_ids',
                    message=f'Product {product.name} is out of stock'
                ))
        
        if errors:
            return CreateOrder(errors=errors)
        
        try:
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date if input.order_date else None,
                    status='PENDING'
                )
                
                # Add products to order
                order.products.set(products)
                
                # Calculate and save total amount
                order.calculate_total()
                
                # Update product stock (optional)
                for product in products:
                    if product.stock > 0:
                        product.stock -= 1
                        product.save()
                
                return CreateOrder(
                    order=order,
                    errors=[]
                )
                
        except Exception as e:
            return CreateOrder(
                errors=[ErrorType(field='__all__', message=str(e))]
            )


# ============================================
# Query Class (Required by previous task)
# ============================================
class Query(graphene.ObjectType):
    """Query class for CRM"""
    
    # All customers query
    all_customers = graphene.List(CustomerType)
    
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.String(required=True))
    
    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.String(required=True))
    
    # Order queries
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.String(required=True))
    
    # Customer count
    customer_count = graphene.Int()
    
    # Resolver for all_customers
    def resolve_all_customers(self, info):
        return Customer.objects.all()
    
    # Resolver for customers (same as all_customers)
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except (Customer.DoesNotExist, ValueError):
            return None
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except (Product.DoesNotExist, ValueError):
            return None
    
    def resolve_orders(self, info):
        return Order.objects.all().order_by('-order_date')
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except (Order.DoesNotExist, ValueError):
            return None
    
    def resolve_customer_count(self, info):
        return Customer.objects.count()


# ============================================
# Mutation Class
# ============================================
class Mutation(graphene.ObjectType):
    """Mutation class for CRM"""
    
    # Customer mutations
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    
    # Product mutation
    create_product = CreateProduct.Field()
    
    # Order mutation
    create_order = CreateOrder.Field()