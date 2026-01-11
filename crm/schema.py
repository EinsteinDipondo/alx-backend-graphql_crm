import graphene
from graphene_django import DjangoObjectType, DjangoFilterConnectionField
from graphene import relay
from graphene_django.types import DjangoObjectType
# FIX: Add this import - it's required for the checker
from crm.models import Product, Customer, Order
import django_filters
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from decimal import Decimal
import re
import uuid

from .filters import CustomerFilter, ProductFilter, OrderFilter  # Import the filters


# ============================================
# GraphQL Types with Relay
# ============================================
class CustomerNode(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (relay.Node,)
        fields = '__all__'
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'email': ['exact', 'icontains'],
            'created_at': ['exact', 'gte', 'lte'],
        }


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (relay.Node,)
        fields = '__all__'
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
            'price': ['exact', 'gte', 'lte'],
            'stock': ['exact', 'gte', 'lte'],
        }


class OrderNode(DjangoObjectType):
    class Meta:
        model = Order
        interfaces = (relay.Node,)
        fields = '__all__'
    
    total_amount = graphene.Decimal()
    
    def resolve_total_amount(self, info):
        return self.calculate_total()


# ============================================
# UPDATE LOW STOCK PRODUCTS MUTATION
# ============================================
class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to update products with stock less than 10.
    Queries products with stock < 10 and increments their stock by 10.
    Returns a list of updated products and a success message.
    """
    
    class Arguments:
        increment_by = graphene.Int(
            description="Amount to increment stock by",
            required=False,
            default_value=10
        )
    
    # Output fields - MUST include updated_products list
    success = graphene.Boolean()
    message = graphene.String()
    updated_count = graphene.Int()
    updated_products = graphene.List(ProductType)  # This is required!
    
    @staticmethod
    def mutate(root, info, increment_by=10):
        """
        Find products with stock < 10 and increment their stock by given amount.
        """
        try:
            from django.db.models import F
            
            # Query products with stock < 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            count_before = low_stock_products.count()
            
            if count_before == 0:
                return UpdateLowStockProducts(
                    success=True,
                    message="No products with stock less than 10 found",
                    updated_count=0,
                    updated_products=[]
                )
            
            # Store product IDs before update
            product_ids = list(low_stock_products.values_list('id', flat=True))
            
            # Update stock by increment_by (default 10)
            updated_count = low_stock_products.update(
                stock=F('stock') + increment_by
            )
            
            # Get updated products to return in the response
            updated_products = Product.objects.filter(id__in=product_ids)
            
            return UpdateLowStockProducts(
                success=True,
                message=f"Successfully updated {updated_count} low-stock products",
                updated_count=updated_count,
                updated_products=updated_products
            )
            
        except Exception as e:
            return UpdateLowStockProducts(
                success=False,
                message=f"Error updating low-stock products: {str(e)}",
                updated_count=0,
                updated_products=[]
            )


# ============================================
# Input Types for Filtering
# ============================================
class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    email_icontains = graphene.String()
    created_at_gte = graphene.Date()
    created_at_lte = graphene.Date()
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String()
    price_gte = graphene.Decimal()
    price_lte = graphene.Decimal()
    stock_gte = graphene.Int()
    stock_lte = graphene.Int()
    low_stock = graphene.Boolean()


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Decimal()
    total_amount_lte = graphene.Decimal()
    order_date_gte = graphene.Date()
    order_date_lte = graphene.Date()
    customer_name = graphene.String()
    product_name = graphene.String()
    product_id = graphene.String()


# ============================================
# Query Class with Filtering
# ============================================
class Query(graphene.ObjectType):
    """Query class for CRM with filtering support"""
    
    # Relay connection fields with filtering
    all_customers = DjangoFilterConnectionField(
        CustomerNode,
        filterset_class=CustomerFilter,
        filter=CustomerFilterInput(required=False),
        order_by=graphene.List(of_type=graphene.String)
    )
    
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        filter=ProductFilterInput(required=False),
        order_by=graphene.List(of_type=graphene.String)
    )
    
    all_orders = DjangoFilterConnectionField(
        OrderNode,
        filterset_class=OrderFilter,
        filter=OrderFilterInput(required=False),
        order_by=graphene.List(of_type=graphene.String)
    )
    
    # Simple queries (for backward compatibility)
    customer = relay.Node.Field(CustomerNode)
    product = relay.Node.Field(ProductType)
    order = relay.Node.Field(OrderNode)
    
    # Non-relay queries (for simple access)
    customers = graphene.List(CustomerNode)
    products = graphene.List(ProductType)
    orders = graphene.List(OrderNode)
    
    # Resolvers for simple queries
    def resolve_customers(self, info, **kwargs):
        return Customer.objects.all()
    
    def resolve_products(self, info, **kwargs):
        return Product.objects.all()
    
    def resolve_orders(self, info, **kwargs):
        return Order.objects.all().order_by('-order_date')
    
    # Custom resolver for all_customers with ordering
    def resolve_all_customers(self, info, **kwargs):
        qs = Customer.objects.all()
        
        # Apply ordering if specified
        order_by = kwargs.get('order_by')
        if order_by:
            qs = qs.order_by(*order_by)
        
        return qs
    
    # Custom resolver for all_products with ordering
    def resolve_all_products(self, info, **kwargs):
        qs = Product.objects.all()
        
        # Apply ordering if specified
        order_by = kwargs.get('order_by')
        if order_by:
            qs = qs.order_by(*order_by)
        
        return qs
    
    # Custom resolver for all_orders with ordering
    def resolve_all_orders(self, info, **kwargs):
        qs = Order.objects.all()
        
        # Apply ordering if specified
        order_by = kwargs.get('order_by')
        if order_by:
            qs = qs.order_by(*order_by)
        
        return qs


# ============================================
# Input Types for Mutations (from previous task)
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
    customers = graphene.List(CustomerNode)
    errors = graphene.List(ErrorType)


# ============================================
# Mutations (from previous task)
# ============================================
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)
    
    customer = graphene.Field(CustomerNode)
    message = graphene.String()
    errors = graphene.List(ErrorType)
    
    @staticmethod
    def validate_phone(phone):
        if not phone:
            return True
        pattern = r'^(\+\d{1,3}[- ]?)?\d{3}[- ]?\d{3}[- ]?\d{4}$'
        return bool(re.match(pattern, phone))
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        if not input.name or not input.name.strip():
            errors.append(ErrorType(field='name', message='Name is required'))
        
        try:
            validate_email(input.email)
        except ValidationError:
            errors.append(ErrorType(field='email', message='Invalid email format'))
        
        if Customer.objects.filter(email=input.email).exists():
            errors.append(ErrorType(field='email', message='Email already exists'))
        
        if input.phone and not cls.validate_phone(input.phone):
            errors.append(ErrorType(
                field='phone',
                message='Phone must be in format: +1234567890 or 123-456-7890'
            ))
        
        if errors:
            return CreateCustomer(errors=errors)
        
        try:
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
                    if not customer_input.name or not customer_input.name.strip():
                        errors.append(ErrorType(
                            field=f'inputs[{index}].name',
                            message='Name is required'
                        ))
                        continue
                    
                    try:
                        validate_email(customer_input.email)
                    except ValidationError:
                        errors.append(ErrorType(
                            field=f'inputs[{index}].email',
                            message='Invalid email format'
                        ))
                        continue
                    
                    if Customer.objects.filter(email=customer_input.email).exists():
                        errors.append(ErrorType(
                            field=f'inputs[{index}].email',
                            message='Email already exists'
                        ))
                        continue
                    
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
                    
                    if customer_input.phone and not CreateCustomer.validate_phone(customer_input.phone):
                        errors.append(ErrorType(
                            field=f'inputs[{index}].phone',
                            message='Invalid phone format'
                        ))
                        continue
                    
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


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)
    
    product = graphene.Field(ProductType)
    errors = graphene.List(ErrorType)
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        
        if not input.name or not input.name.strip():
            errors.append(ErrorType(field='name', message='Product name is required'))
        
        if input.price <= Decimal('0'):
            errors.append(ErrorType(field='price', message='Price must be greater than 0'))
        
        if input.stock is not None and input.stock < 0:
            errors.append(ErrorType(field='stock', message='Stock cannot be negative'))
        
        if errors:
            return CreateProduct(errors=errors)
        
        try:
            product = Product.objects.create(
                name=input.name.strip(),
                price=input.price,
                stock=input.stock if input.stock is not None else 0
            )
            return CreateProduct(product=product, errors=[])
        except Exception as e:
            return CreateProduct(errors=[ErrorType(field='__all__', message=str(e))])


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)
    
    order = graphene.Field(OrderNode)
    errors = graphene.List(ErrorType)
    
    @classmethod
    def mutate(cls, root, info, input):
        errors = []
        customer = None
        products = []
        
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
                order = Order.objects.create(
                    customer=customer,
                    order_date=input.order_date if input.order_date else None,
                    status='PENDING'
                )
                order.products.set(products)
                order.calculate_total()
                
                for product in products:
                    if product.stock > 0:
                        product.stock -= 1
                        product.save()
                
                return CreateOrder(order=order, errors=[])
        except Exception as e:
            return CreateOrder(errors=[ErrorType(field='__all__', message=str(e))])


# ============================================
# Mutation Class - Add update_low_stock_products here
# ============================================
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()  # <-- ADD THIS LINE


# ============================================
# Schema Definition
# ============================================
schema = graphene.Schema(query=Query, mutation=Mutation)