from django.urls import path
from . import views


urlpatterns = [
    path(route='checkout/', view=views.checkout, name='Checkout cart'),
    path(route='<int:id>/', view=views.check_order, name='Check an order by id'),
    path(route='<int:id>/payment/', view=views.create_payment_intent, name='Creating payment intent for an order by id'),
    path(route='stripe/webhook/', view=views.stripe_webhook, name='Webhook for Stripe payment')
]