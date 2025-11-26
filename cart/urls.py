from django.urls import path
from . import views


urlpatterns = [
    path(route='', view=views.get_cart, name='Get cart'),
    path(route='add/<int:item_id>', view=views.add_to_cart, name='Add product to the cart'),
    path(route='add/<int:item_id>', view=views.remove_from_cart, name='Delete item from cart')
]