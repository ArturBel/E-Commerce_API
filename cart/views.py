from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import ItemSerializer
from products.models import Product
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from products.serializers import ProductSerializer


# helper function to get/create a cart for user
def get_user_cart(user):
    cart, created = Cart.objects.get_or_create(user=user)
    return cart


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cart(request):
    # getting cart's data
    cart = get_user_cart(request.user)
    owner_id = cart.user.pk
    username = request.user.username
    items = ItemSerializer(CartItem.objects.filter(cart=cart), many=True)
    total = sum(item['subtotal'] for item in items.data)
    data = {
        'owner_id': owner_id,
        'owner_username': username,
        'items': items.data,
        'total': total
    }

    # outputting result
    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['POST', 'PUT'])
@permission_classes([IsAuthenticated])
def add_to_cart(request, item_id):
    # getting data from json request
    cart = get_user_cart(request.user)
    quantity = request.data.get('quantity', 1)
    product = get_object_or_404(Product, pk=item_id)

    # checking if item already exists
    item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
    )
    
    # adding item to the cart
    if request.method == 'POST':
        if created:
            item.quantity = quantity
        else:
            item.quantity += quantity
    # editing quantity of existing item or adding new item to the cart
    elif request.method == 'PUT':
        item.quantity = quantity
        return Response({'msg': 'Item quantity was editted'}, status=status.HTTP_200_OK)

    # saving item and returning response
    item.save()
    return Response({'msg': 'Item added to cart'}, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_from_cart(request, item_id):
    # finding an item in the cart and deleting it
    item = get_object_or_404(CartItem, pk=item_id, cart=get_user_cart(request.user))
    item.delete()
    return Response({"message": "Item removed"}, status=status.HTTP_200_OK)
