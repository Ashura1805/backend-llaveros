from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token 
from django.contrib.auth import authenticate, get_user_model 
from django.db.models import Q 
from django.db import transaction # IMPORTANTE PARA COMPRAS SEGURAS
from .models import Categoria, Llavero, Pedido, Cliente, Material, LlaveroMaterial, DetallePedido

from .serializers import (
    RegisterSerializer, 
    LoginSerializer,
    CategoriaSerializer, 
    LlaveroSerializer, 
    PedidoSerializer, 
    ClienteSerializer, 
    MaterialSerializer,
    LlaveroMaterialSerializer,
    DetallePedidoSerializer
)

# === 1. AUTENTICACIÓN Y LOGIN ===

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_google(request):
    """ Login simulado con Google (Stub). """
    return Response({
        'status': 'success',
        'role': 'user',
        'token': 'demo_token_123_oauth' 
    })

@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    """ LOGIN HÍBRIDO: Acepta Email O Username """
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        login_input = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        User = get_user_model()
        user_found = User.objects.filter(Q(email=login_input) | Q(username=login_input)).first()
        
        if not user_found:
            return Response(
                {"error": "El usuario o correo no existe. Por favor, regístrese."}, 
                status=status.HTTP_404_NOT_FOUND 
            )

        user = authenticate(username=user_found.username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "message": "Login exitoso",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_staff": user.is_staff, 
                "token": token.key 
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Contraseña incorrecta. Inténtalo de nuevo."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    print(f"\n--- ERROR FORMATO LOGIN --- Errores: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterViewSet(viewsets.ViewSet):
    """ Registro de usuarios con generación de Token. """
    permission_classes = [AllowAny]
    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user) 
            return Response({
                "token": token.key, 
                "message": "¡Cuenta creada exitosamente!", 
                "success": True, 
                "user_id": user.id,
                "is_staff": user.is_staff
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# === 2. VIEWSETS COMPLETOS (CRUD) ===

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]

class LlaveroViewSet(viewsets.ModelViewSet):
    queryset = Llavero.objects.select_related('categoria').all()
    serializer_class = LlaveroSerializer
    permission_classes = [AllowAny]

class ClienteViewSet(viewsets.ModelViewSet):
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [AllowAny]

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]

class LlaveroMaterialViewSet(viewsets.ModelViewSet):
    queryset = LlaveroMaterial.objects.all()
    serializer_class = LlaveroMaterialSerializer
    permission_classes = [AllowAny]

class PedidoViewSet(viewsets.ModelViewSet):
    """
    LOGICA ACTUALIZADA PARA EVITAR ERRORES DE COMPRA.
    Se asegura de que el cliente exista y vincula el pedido al usuario autenticado.
    """
    serializer_class = PedidoSerializer
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Pedido.objects.all().order_by('-fecha')
        return Pedido.objects.filter(cliente__user=user).order_by('-fecha')

    def create(self, request, *args, **kwargs):
        try:
            # 1. Vincular o crear perfil de Cliente para el usuario logueado
            # Esto evita el error si el usuario existe en Auth pero no en la tabla Cliente
            cliente, _ = Cliente.objects.get_or_create(
                user=request.user,
                defaults={'nombre': request.user.get_full_name() or request.user.username}
            )

            # 2. Inyectar el ID del cliente en los datos recibidos
            data = request.data.copy()
            data['cliente'] = cliente.id
            
            serializer = self.get_serializer(data=data)
            if serializer.is_valid():
                # 3. Guardar pedido y detalles en una sola transacción
                with transaction.atomic():
                    self.perform_create(serializer)
                    return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            # Si hay errores de validación (ej. falta el total), se imprimen en consola
            print(f"ERROR VALIDACION PEDIDO: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(f"ERROR CRITICO EN COMPRA: {str(e)}")
            return Response({"error": "No se pudo procesar la compra en el servidor."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [IsAuthenticated]


# === 3. VISTAS DE COMPATIBILIDAD (Para App Android) ===

class CategoriaList(generics.ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny] 

class ProductoList(generics.ListAPIView):
    serializer_class = LlaveroSerializer 
    permission_classes = [AllowAny] 

    def get_queryset(self):
        queryset = Llavero.objects.all()
        category_id = self.kwargs.get('category_id')
        if category_id is not None:
            queryset = queryset.filter(categoria__id=category_id)
        return queryset.select_related('categoria')