from django.urls import path
from . import views


urlpatterns = [
    path(route='all/', view=views.all_products, name='All products'),
    path(route='my/', view=views.my_products, name='List products of user'),
    path(route='post/', view=views.post_new_product, name='Post a new product'),
    path(route='product/<int:pk>', view=views.product_by_id, name='Product by id')
]