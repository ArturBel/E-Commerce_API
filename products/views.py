from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from users.models import CustomUser
from .models import Product
from .serializers import ProductSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination


@permission_classes([IsAuthenticated])
@api_view(['GET'])
def all_products(request):
    # listing all products
    queryset = Product.objects.all().order_by('-created_at')

    # paginating and serializing queryset
    paginator = PageNumberPagination()
    paginated_qs = paginator.paginate_queryset(queryset, request)
    serializer = ProductSerializer(paginated_qs, many=True)

    # returing paginated result
    return paginator.get_paginated_response(serializer.data)



@permission_classes([IsAuthenticated])
@api_view(['GET'])
def my_products(request):
    # finding required user by id
    try:
        user_id = request.user.pk
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response(data=request.data, status=status.HTTP_404_NOT_FOUND)
    
    # listing all products user posted, if any, via pagination
    queryset = Product.objects.filter(seller=request.user.pk).order_by('-created_at')
    if queryset:
        # paginating and serializing queryset
        paginator = PageNumberPagination()
        paginated_qs = paginator.paginate_queryset(queryset, request)
        serializer = ProductSerializer(paginated_qs, many=True)

        # returing paginated result
        return paginator.get_paginated_response(serializer.data)
    else:
        return Response(data={'msg': 'You have not posted any products.'}, status=status.HTTP_200_OK)
    

@permission_classes([IsAuthenticated])
@api_view(['POST'])
def post_new_product(request):
    # finding required user
    try:
        user_id = request.user.pk
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response(data=request.data, status=status.HTTP_404_NOT_FOUND)
    
    # getting data from request
    new_product = ProductSerializer(data={**request.data, 'seller': request.user.pk})

    # checking if data is valid
    if new_product.is_valid():
        new_product.save(seller=request.user)
        return Response(data={**new_product.data, 'msg': 'Product was posted successfully.'}, status=status.HTTP_201_CREATED)
    else:
        return Response(new_product.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
@api_view(['GET', 'PUT', 'DELETE'])
def product_by_id(request, pk):
    # finding required user and product
    try:
        user_id = request.user.pk
        productObject = Product.objects.get(pk=pk, seller=user_id)
    except CustomUser.DoesNotExist:
        return Response(data=request.data, status=status.HTTP_404_NOT_FOUND)
    
    # getting product information by id
    if request.method == 'GET':
        product = ProductSerializer(productObject)
        return Response(data=product.data, status=status.HTTP_200_OK)
    # updating product by id
    elif request.method == 'PUT':
        # getting data from request
        updated_product = ProductSerializer(productObject, data=request.data, partial=True)

        # checking if data is valid
        if updated_product.is_valid():
            updated_product.save()
            return Response(data={**updated_product.data, 'msg': 'Product information was updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(data=updated_product.errors, status=status.HTTP_400_BAD_REQUEST)
    # deleting product by id
    elif request.method == 'DELETE':
        productObject.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
