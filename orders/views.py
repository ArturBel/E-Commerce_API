from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from cart.views import get_user_cart
from cart.models import CartItem
from .models import Order, OrderItem
from .serializers import OrderItemSerializer, OrderSerializer
from django.shortcuts import get_object_or_404
import stripe
from django.conf import settings


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout(request):
    # getting user's cart and its items
    cart = get_user_cart(request.user)
    cart_items = CartItem.objects.filter(cart=cart)

    if not cart_items.exists():
        return Response({'msg': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)

    # calculating total sum of an order
    total_price = sum(item.quantity * item.product.price for item in cart_items)

    # creating order
    order = Order.objects.create(
        user=request.user,
        total_price=total_price,
        status='pending'
    )

    # creating order's items
    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price_at_purchase=item.product.price
        )

    # clearing cart
    cart_items.delete()

    # returning response
    return Response({'msg': 'Order was created', 'order_id': order.id}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_order(request, id):
    # getting user's order and displaying its information
    order_object = get_object_or_404(Order, pk=id, user=request.user)
    order = OrderSerializer(order_object)

    return Response(data=order.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request, id):
    # getting user's order and items
    order_object = get_object_or_404(Order, pk=id, user=request.user)
    items_query = OrderItem.objects.filter(order=order_object)

    if not items_query.exists():
        return Response(data={'msg': 'Order does not contain any items'}, status=status.HTTP_400_BAD_REQUEST)
    
    # calculating total sum of an order
    total_price = int(sum(item.quantity * item.product.price for item in items_query) * 100)

    # preparing stripe and items for payment
    stripe.api_key = settings.STRIPE_SECRET_KEY
    line_items = []
    for item in items_query:
        line_items.append(
            {
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': item.product.name},
                    'unit_amount': int(item.product.price * 100)
                },
                'quantity': item.quantity
            }
        )

    # creating session for payment
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url='http://127.0.0.1:8000/orders/success/',
            cancel_url='http://127.0.0.1:8000/orders/cancel/'
        )

        # USE THIS SESSION ID FOR REDIRECT TO STRIPE'S CHECKOUT PAGE
        return Response({"session_id": session.id}, status=status.HTTP_200_OK)
    except Exception as error:
        return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)