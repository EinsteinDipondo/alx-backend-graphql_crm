# crm/filters.py
import django_filters
from django.db.models import Q
from .models import Customer, Product, Order
import re


class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    created_at_gte = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_at_lte = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Custom filter for phone number pattern
    phone_pattern = django_filters.CharFilter(method='filter_phone_pattern')
    
    class Meta:
        model = Customer
        fields = ['name', 'email', 'created_at_gte', 'created_at_lte']
    
    def filter_phone_pattern(self, queryset, name, value):
        """
        Filter customers by phone number pattern.
        Example: filter by phones starting with '+1'
        """
        if value:
            # Remove any non-digit characters except + for pattern matching
            pattern = re.escape(value)
            return queryset.filter(phone__regex=rf'^{pattern}')
        return queryset


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    price_gte = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_lte = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    stock_gte = django_filters.NumberFilter(field_name='stock', lookup_expr='gte')
    stock_lte = django_filters.NumberFilter(field_name='stock', lookup_expr='lte')
    
    # Custom filter for low stock
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    
    class Meta:
        model = Product
        fields = ['name', 'price_gte', 'price_lte', 'stock_gte', 'stock_lte']
    
    def filter_low_stock(self, queryset, name, value):
        """
        Filter products with low stock (stock < 10)
        """
        if value is True:
            return queryset.filter(stock__lt=10)
        elif value is False:
            return queryset.filter(stock__gte=10)
        return queryset


class OrderFilter(django_filters.FilterSet):
    total_amount_gte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='gte')
    total_amount_lte = django_filters.NumberFilter(field_name='total_amount', lookup_expr='lte')
    order_date_gte = django_filters.DateFilter(field_name='order_date', lookup_expr='gte')
    order_date_lte = django_filters.DateFilter(field_name='order_date', lookup_expr='lte')
    
    # Filter by customer name (related field lookup)
    customer_name = django_filters.CharFilter(method='filter_customer_name')
    
    # Filter by product name (related field lookup)
    product_name = django_filters.CharFilter(method='filter_product_name')
    
    # Filter by specific product ID
    product_id = django_filters.CharFilter(method='filter_product_id')
    
    class Meta:
        model = Order
        fields = [
            'total_amount_gte', 'total_amount_lte',
            'order_date_gte', 'order_date_lte'
        ]
    
    def filter_customer_name(self, queryset, name, value):
        """Filter orders by customer name (case-insensitive partial match)"""
        if value:
            return queryset.filter(customer__name__icontains=value)
        return queryset
    
    def filter_product_name(self, queryset, name, value):
        """Filter orders by product name (case-insensitive partial match)"""
        if value:
            return queryset.filter(products__name__icontains=value).distinct()
        return queryset
    
    def filter_product_id(self, queryset, name, value):
        """Filter orders that include a specific product ID"""
        if value:
            return queryset.filter(products__id=value).distinct()
        return queryset