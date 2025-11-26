from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductSerializer


class ItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta():
        model = CartItem
        exclude = ['cart', 'id']
    
    def get_subtotal(self, obj):
        return obj.quantity * obj.product.price