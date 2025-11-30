from django.db import models
from users.models import CustomUser
from django.contrib.postgres.fields import ArrayField


class Product(models.Model):
    seller = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    tags = ArrayField(models.CharField(max_length=32), blank=True, default=list)
    created_at = models.DateTimeField(auto_now_add=True)

