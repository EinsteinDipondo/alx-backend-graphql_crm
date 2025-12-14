# crm/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from decimal import Decimal
import re

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
# Custom Error Types
# ============================================
class ErrorType(graphene.ObjectType):
    field = graphene.String()
    message = graphene.String()


class BulkCreateResult(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    errors = graphene.List(ErrorType)


# ============================================
# Mutations
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
        pattern = r'^(\+\d{1,3}[- ]?)?\d{10}$'
        return bool(re.match(pattern, phone))
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        # Validate email
        try:
            validate_email(input.email)
        except ValidationError:
            errors.append(ErrorType(
                field='email',
                message='Invalid email format'
            ))
        
        # Validate phone
        if input.phone and not cls.validate_phone(input.phone):
            errors.append(ErrorType(
                field='phone',
                message='Phone must be in format: +1234567890 or 1234567890'
            ))
        
        # Check for duplicate email
        if Customer.objects.filter(email=input.email).exists():
            errors.append(ErrorType(
                field='email',
                message='Email already exists'
            ))
        
        if errors:
            return CreateCustomer(errors=errors)
        
        try:
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone if input.phone else None
            )
            return CreateCustomer(
                customer=customer,
                message='Customer created successfully'
            )
        except Exception as e:
            return CreateCustomer(
                errors=[ErrorType(field='__all__', message=str(e))]
            )


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        inputs = graphene.List(CustomerInput, required=True)
    
    result = graphene.Field(BulkCreateResult)
    
    @classmethod
    def mutate(cls, root, info, inputs):
        customers = []
        errors = []
        
        with transaction.atomic():
            for index, input_data in enumerate(inputs):
                try:
                    # Validate email
                    validate_email(input_data.email)
                    
                    # Check for duplicate email
                    if Customer.objects.filter(email=input_data.email).exists():
                        errors.append(ErrorType(
                            field=f'customers[{index}].email',
                            message='Email already exists'
                        ))
                        continue
                    
                    # Validate phone
                    if input_data.phone:
                        pattern = r'^(\+\d{1,3}[- ]?)?\d{10}$'
                        if not re.match(pattern, input_data.phone):
                            errors.append(ErrorType(
                                field=f'customers[{index}].phone',
                                message='Invalid phone format'
                            ))
                            continue
                    
                    customer = Customer.objects.create(
                        name=input_data.name,
                        email=input_data.email,
                        phone=input_data.phone if input_data.phone else None
                    )
                    customers.append(customer)
                    
                except ValidationError as e:
                    errors.append(ErrorType(
                        field=f'customers[{index}].email',
                        message=str(e)
                    ))
                except Exception as e:
                    errors.append(ErrorType(
                        field=f'customers[{index}]',
                        message=str(e)
                    ))
        
        return BulkCreateCustomers(
            result=BulkCreateResult(
                customers=customers,
                errors=errors
            )
        )


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    errors = graphene.List(ErrorType)
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        # Validate price
        if input.price <= Decimal('0'):
            errors.append(ErrorType(
                field='price',
                message='Price must be greater than 0'
            ))
        
        # Validate stock
        if input.stock < 0:
            errors.append(ErrorType(
                field='stock',
                message='Stock cannot be negative'
            ))
        
        if errors:
            return CreateProduct(errors=errors)
        
        try:
            product = Product.objects.create(
                name=input.name,
                price=input.price,
                stock=input.stock if input.stock is not None else 0
            )
            return CreateProduct(product=product)
        except Exception as e:
            return CreateProduct(
                errors=[ErrorType(field='__all__', message=str(e))]
            )


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderType)
    errors = graphene.List(ErrorType)
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        # Validate customer exists
        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            errors.append(ErrorType(
                field='customer_id',
                message='Customer not found'
            ))
            customer = None
        
        # Validate products
        products = []
        if input.product_ids:
            for idx, product_id in enumerate(input.product_ids):
                try:
                    product = Product.objects.get(id=product_id)
                    products.append(product)
                except Product.DoesNotExist:
                    errors.append(ErrorType(
                        field=f'product_ids[{idx}]',
                        message=f'Product with ID {product_id} not found'
                    ))
        
        # Validate at least one product
        if not products:
            errors.append(ErrorType(
                field='product_ids',
                message='At least one valid product is required'
            ))
        
        if errors:
            return CreateOrder(errors=errors)
        
        try:
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date if input.order_date else None
                )
                
                # Add products
                order.products.set(products)
                
                # Calculate total
                order.calculate_total()
                
                return CreateOrder(order=order)
        except Exception as e:
            return CreateOrder(
                errors=[ErrorType(field='__all__', message=str(e))]
            )


# ============================================
# Query Definitions
# ============================================
class CRMQuery(graphene.ObjectType):
    # Customer queries
    customers = graphene.List(CustomerType)
    customer = graphene.Field(CustomerType, id=graphene.String(required=True))
    
    # Product queries
    products = graphene.List(ProductType)
    product = graphene.Field(ProductType, id=graphene.String(required=True))
    
    # Order queries
    orders = graphene.List(OrderType)
    order = graphene.Field(OrderType, id=graphene.String(required=True))
    
    # Resolvers
    def resolve_customers(self, info):
        return Customer.objects.all()
    
    def resolve_customer(self, info, id):
        try:
            return Customer.objects.get(id=id)
        except Customer.DoesNotExist:
            return None
    
    def resolve_products(self, info):
        return Product.objects.all()
    
    def resolve_product(self, info, id):
        try:
            return Product.objects.get(id=id)
        except Product.DoesNotExist:
            return None
    
    def resolve_orders(self, info):
        return Order.objects.all()
    
    def resolve_order(self, info, id):
        try:
            return Order.objects.get(id=id)
        except Order.DoesNotExist:
            return None


# ============================================
# Mutation Definitions
# ============================================
class CRMMutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()