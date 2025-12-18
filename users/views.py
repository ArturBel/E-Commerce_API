from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from .serializers import UserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from argon2.exceptions import VerifyMismatchError
from django.utils import timezone
from rest_framework.throttling import UserRateThrottle
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache
import jwt
from ecommerce_api import settings
import hashlib


# rate limiter for user authorization
class AuthorizationThrottle(UserRateThrottle):
    rate = '1/min'


# helper function to get tokens
def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user=user)
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


# helper function to get jwt token from request
def get_token_from_header(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationFailed("Authorization header missing.")

    parts = auth_header.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise AuthenticationFailed("Invalid Authorization header format.")

    return parts[1]


@api_view(['POST'])
@throttle_classes([AuthorizationThrottle])
def register(request):
    # creating a new user from json data
    user_serializer = UserSerializer(data=request.data)

    # checking if prohibited fields are not present (or false)
    if request.data.get('is_staff') is True or request.data.get('is_superuser') is True:
        return Response(data={'msg': 'You do not have permission to register as superuser or staff.'}, status=status.HTTP_401_UNAUTHORIZED)

    # checking if json data is valid
    if user_serializer.is_valid():
        # hashing the password before storing in the database
        new_user = user_serializer.save()
        new_user.hash_password(new_user.password)
        
        # saving new user, generation tokens and outputting result
        new_user.save()
        tokens = get_tokens_for_user(user=new_user)
        return Response(data={**user_serializer.data, 'msg': 'Registration successful.', 'tokens': tokens}, status=status.HTTP_201_CREATED)
    else:
        return Response(data=user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@throttle_classes([AuthorizationThrottle])
def login(request):
    # getting data from json request
    data = request.data
    email = data['email']
    password = data['password']

    # checking if all required fields are present
    if not email or not password:
        return Response(data={'msg': 'Email and password fields are required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # checking if credentials are valid
    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        return Response(data={'msg': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
    try:
        user.check_password(raw_password=password)
    except VerifyMismatchError:
        return Response(data={'msg': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    # generating tokens, updating last login date and outputting message of successful login
    tokens = get_tokens_for_user(user=user)
    user.last_login = timezone.now()
    user.save()
    return Response(data={'msg': f'Login successful. Welcome, {user.username}!', 'tokens': tokens}, status=status.HTTP_200_OK)


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def edit_profile(request):
    # finding required user
    try:
        user_id = request.user.pk
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response(data=request.data, status=status.HTTP_404_NOT_FOUND)
    
    # checking if request contains prohibited fields
    if request.data.get('is_staff') is True or request.data.get('is_superuser') is True:
        return Response(data={'msg': 'You do not have permission to assign yourself as superuser or staff.'}, status=status.HTTP_401_UNAUTHORIZED)
    
    if request.data['password']:
        return Response(data={'msg': "Password can only be changed on '/password/' endpoint."}, status=status.HTTP_400_BAD_REQUEST)

    # changing user's data
    updated_user = UserSerializer(user, data=request.data, partial=True)
    if updated_user.is_valid():
        updated_user.save()
        return Response(data={**updated_user.data, 'msg': 'Profile was edited successfully.'}, status=status.HTTP_200_OK)
    else:
        return Response(data=updated_user.errors, status=status.HTTP_400_BAD_REQUEST)


@permission_classes([IsAuthenticated])
@api_view(['POST'])
def password_reset(request):
    # finding required user
    try:
        user_id = request.user.pk
        user = CustomUser.objects.get(pk=user_id)
    except CustomUser.DoesNotExist:
        return Response(data=request.data, status=status.HTTP_404_NOT_FOUND)
    
    # checking the request and old password
    if request.data.get('old_password') is None or request.data.get('new_password') is None:
        return Response(data={'msg': "'old_password' and 'new_password' are required fields."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user.check_password(raw_password=request.data['old_password'])
        # setting and hashing new password
        user.hash_password(request.data['new_password'])
        user.save()
        return Response(data={'msg': 'Password was changed successully.'}, status=status.HTTP_202_ACCEPTED)
    except VerifyMismatchError:
        return Response(data={'msg': 'Old password does not match.'}, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    # getting token from request
    token = get_token_from_header(request=request)

    # decoding the token
    decoded_token = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=['HS256'],
        options={'verify_exp': False},
    )

    # checking if token is valid or expired already
    exp_timestamp = decoded_token.get('exp')
    if not exp_timestamp:
        return Response({'msg': 'Invalid token.'}, status=status.HTTP_400_BAD_REQUEST)

    # calculating remaining lifetime
    now = timezone.now().timestamp()
    timeout = int(exp_timestamp - now)

    if timeout <= 0:
        return Response({'msg': 'Token already expired.'}, status=status.HTTP_400_BAD_REQUEST)
    
    # hashing token to reduce its length and for security
    key = hashlib.sha256(string=token.encode()).hexdigest()

    # blacklisting the hashed token
    cache.set(
        key=f"blacklisted_token:{key}",
        value="true",
        timeout=timeout
    )

    # returning response
    return Response(data={'msg': 'Logout successful.'}, status=status.HTTP_200_OK)

        