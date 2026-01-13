from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token 
from django.contrib.auth import authenticate, get_user_model 
from django.db.models import Q 
from django.db import transaction 
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
    """ Login simulado con Google. """
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
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        user = authenticate(username=user_found.username, password=password)
        if user is not None:
            token, created = Token.objects.get_or_create(user=user)
            # Buscamos si tiene un Cliente asociado para devolver su ID (útil para la app)
            cliente_id = None
            try:
                cliente = Cliente.objects.get(user=user)
                cliente_id = cliente.id
            except Cliente.DoesNotExist:
                pass

            return Response({
                "message": "Login exitoso",
                "user_id": user.id,
                "cliente_id": cliente_id, # IMPORTANTE PARA LA APP
                "username": user.username,
                "token": token.key 
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Contraseña incorrecta."}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            # Creamos automáticamente el perfil de Cliente
            Cliente.objects.create(user=user, nombre=user.username, email=user.email)
            
            return Response({
                "token": token.key, 
                "message": "¡Cuenta creada!", 
                "success": True
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# === 2. VIEWSETS PRINCIPALES (CRUD) ===

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

# === AQUÍ ESTÁ LA CORRECCIÓN CLAVE PARA TU APP ===

class PedidoViewSet(viewsets.ModelViewSet):
    """
    Permite crear pedidos desde Android sin restricciones estrictas de usuario.
    Permite filtrar historial por cliente: /api/pedidos/?cliente=1
    """
    queryset = Pedido.objects.all().order_by('-fecha_pedido') # Ordenado por fecha descendente
    serializer_class = PedidoSerializer
    permission_classes = [AllowAny] # ✅ Abierto para que Android no de error 401

    def get_queryset(self):
        """ Filtra los pedidos si se pasa el parámetro ?cliente=ID """
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            return queryset.filter(cliente_id=cliente_id)
        return queryset

    def create(self, request, *args, **kwargs):
        # Usamos transaction.atomic para asegurar integridad
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"Error creando pedido: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DetallePedidoViewSet(viewsets.ModelViewSet):
    """
    Maneja los items dentro del pedido.
    Permite filtrar: /api/detalle-pedidos/?pedido=5
    """
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [AllowAny] # ✅ Abierto para Android

    def get_queryset(self):
        """ Filtra detalles por ID de pedido """
        queryset = super().get_queryset()
        pedido_id = self.request.query_params.get('pedido')
        if pedido_id:
            return queryset.filter(pedido_id=pedido_id)
        return queryset


# === 3. VISTAS EXTRA (Listas simples) ===

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