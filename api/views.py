from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser 
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token 
from django.contrib.auth import authenticate, get_user_model 
from django.db.models import Q # <--- NECESARIO PARA BUSCAR "O" (Email O Username)
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
    """
    Login simulado con Google (Stub). 
    """
    return Response({
        'status': 'success',
        'role': 'user',
        'token': 'demo_token_123_oauth' 
    })

@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    """
    LOGIN HÍBRIDO: Acepta Email O Username (Para que el Admin pueda entrar)
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        # El campo viene etiquetado como 'email' desde la App, 
        # pero aquí lo trataremos como "input de login" (puede ser user o email)
        login_input = serializer.validated_data.get('email')
        password = serializer.validated_data.get('password')
        
        User = get_user_model()
        
        # 1. BÚSQUEDA INTELIGENTE
        # Buscamos si existe alguien con ese Email O con ese Username
        user_found = User.objects.filter(
            Q(email=login_input) | Q(username=login_input)
        ).first()
        
        if not user_found:
            return Response(
                {"error": "El usuario o correo no existe. Por favor, regístrese."}, 
                status=status.HTTP_404_NOT_FOUND 
            )

        # 2. INTENTAR AUTENTICAR
        # Usamos el 'username' real del usuario encontrado para que la función authenticate no falle
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
                "is_staff": user.is_staff, # Enviamos el poder de Admin
                "token": token.key 
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {"error": "Contraseña incorrecta. Inténtalo de nuevo."}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
    
    print(f"\n--- ERROR FORMATO LOGIN ---")
    print(f"Errores: {serializer.errors}")
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterViewSet(viewsets.ViewSet):
    """
    Registro de usuarios. Permite a cualquier persona registrarse. 
    Genera un token tras el registro.
    """
    permission_classes = [AllowAny]

    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Usamos Token para crear el token
            token, created = Token.objects.get_or_create(user=user) 
            
            return Response({
                "token": token.key, 
                "message": "¡Cuenta creada exitosamente! Puedes iniciar sesión ahora.", 
                "success": True, 
                "user_id": user.id,
                "is_staff": user.is_staff
            }, status=status.HTTP_201_CREATED)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# === 2. VIEWSETS COMPLETOS (CRUD para el Panel Web) ===

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
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and not user.is_anonymous:
            if user.is_staff:
                return Pedido.objects.all()
            return Pedido.objects.filter(cliente__user=user)
        return Pedido.objects.all() 

class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [AllowAny]


# === 3. VISTAS DE COMPATIBILIDAD (Para App Android) ===

class CategoriaList(generics.ListAPIView):
    """Devuelve la lista de categorías para el menú lateral de Android."""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny] 

class ProductoList(generics.ListAPIView):
    """Devuelve llaveros filtrados por categoría para Android."""
    serializer_class = LlaveroSerializer 
    permission_classes = [AllowAny] 

    def get_queryset(self):
        queryset = Llavero.objects.all()
        category_id = self.kwargs.get('category_id')
        if category_id is not None:
            queryset = queryset.filter(categoria__id=category_id)
        return queryset.select_related('categoria')