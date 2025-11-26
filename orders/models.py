from django.db import models
from users.models import CustomUser
from products.models import Product


class Order(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    status_choices=[('pending', 'Pending'),
                 ('paid', 'Paid'),
                 ('shipped', 'Shipped'),
                 ('completed', 'Completed')]
    
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    payment_intent_id = models.CharField(max_length=200, null=True, blank=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2)
