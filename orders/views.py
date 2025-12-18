from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from cart.views import get_user_cart
from cart.models import CartItem
from .models import Order, OrderItem
from products.models import Product
from .serializers import OrderItemSerializer, OrderSerializer
from django.shortcuts import get_object_or_404
import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt


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
    
    if order_object.status != 'pending':
        return Response(data={'msg': 'Payment intent is already created for this order.'}, status=status.HTTP_200_OK)
    
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

    # creating intent for payment
    intent = stripe.PaymentIntent.create(
        amount=total_price,
        currency='usd',
        payment_method="pm_card_visa",
        automatic_payment_methods={'enabled': True, 'allow_redirects': 'never'},
        metadata={
            'order_id': order_object.id,
            'user_id': request.user.id,
        }
    )

    # confirmin payment intent (for testing)
    intent = stripe.PaymentIntent.confirm(
        intent.id,
        payment_method="pm_card_visa"
    )

    # saving payment intent id to the db
    order_object.payment_intent_id = intent["id"]
    order_object.save()

    # returning response with client's secret for payment
    return Response(data={'msg': 'Payment intent created successfully', 'client_secret': intent['client_secret']})


@csrf_exempt
def stripe_webhook(request):
    # getting request data
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

    # creating a stripe's event
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except Exception as error:
        return HttpResponse(data={'msg': f'{error}'}, status=400)

    # logic for successful payment
    if event['type'] == 'payment_intent.succeeded':
        intent = event['data']['object']
        payment_intent_id = intent['id']

        try:
            # getting required order
            order_object = Order.objects.get(payment_intent_id=payment_intent_id)

            # updating products' stock and checking if stock is sufficient
            items_query = order_object.items.all()
            for item in items_query:
                current_product = item.product
                if item.quantity > current_product.stock:
                    return Response(data={'msg': f'Insufficient stock for {current_product.name}'}, status=status.HTTP_400_BAD_REQUEST)
                current_product.stock -= item.quantity
                current_product.save()
            
            # marking order as paid
            order_object.status = 'paid'
            order_object.save()
        except Order.DoesNotExist:
            return HttpResponse(status=404)

    return HttpResponse(status=200)