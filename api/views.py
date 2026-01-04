from rest_framework import viewsets, status, generics
from rest_framework.response import Response
# Revertimos los permisos a AllowAny para enfocarnos en la lógica de login/registro
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser 
from rest_framework.decorators import api_view, permission_classes
# CORRECCIÓN CLAVE: Importamos el modelo Token
from rest_framework.authtoken.models import Token 
from .models import Categoria, Llavero, Pedido, Cliente, Material, LlaveroMaterial, DetallePedido

# Asegúrate de tener LoginSerializer aquí, es CRUCIAL para el login de Android
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
    LOGIN PARA ANDROID 
    Capturamos y mostramos los errores de serialización en la terminal.
    """
    serializer = LoginSerializer(data=request.data)
    
    # Si la validación ES exitosa
    if serializer.is_valid(): 
        user = serializer.validated_data['user']
        # Si la validación es exitosa, genera o recupera el token usando Token
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            "message": "Login exitoso",
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "token": token.key 
        }, status=status.HTTP_200_OK)
    
    # CAPTURAMOS EL ERROR Y LO IMPRIMIMOS EN LA TERMINAL (LÍNEA CLAVE DE DIAGNÓSTICO)
    print(f"\n--- ERROR SERIALIZER LOGIN ---")
    print(f"Datos recibidos: {request.data}")
    print(f"Errores de Serializer: {serializer.errors}")
    print(f"--- FIN ERROR SERIALIZER ---\n")
    
    # Devuelve error 400 con los detalles
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
            
            # MEJORA: Respuesta de ÉXITO CLARA para que el móvil pueda redirigir
            return Response({
                "token": token.key, 
                "message": "¡Cuenta creada exitosamente! Puedes iniciar sesión ahora.", 
                "success": True, # Bandera explícita
                "user_id": user.id
            }, status=status.HTTP_201_CREATED)
            
        # Si falla la validación (duplicado, campos incompletos), devuelve 400
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# === 2. VIEWSETS COMPLETOS (CRUD para el Panel Web - PERMISIVIDAD TEMPORAL) ===

class CategoriaViewSet(viewsets.ModelViewSet):
    """CRUD de Categorias (Revertido a AllowAny)."""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]

class LlaveroViewSet(viewsets.ModelViewSet):
    """CRUD de Llaveros (Revertido a AllowAny)."""
    # select_related optimiza la consulta a la base de datos
    queryset = Llavero.objects.select_related('categoria').all()
    serializer_class = LlaveroSerializer
    permission_classes = [AllowAny]

class ClienteViewSet(viewsets.ModelViewSet):
    """CRUD de Clientes (Revertido a AllowAny)."""
    queryset = Cliente.objects.all()
    serializer_class = ClienteSerializer
    permission_classes = [AllowAny]

class MaterialViewSet(viewsets.ModelViewSet):
    """CRUD de Materiales (Revertido a AllowAny)."""
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]

class LlaveroMaterialViewSet(viewsets.ModelViewSet):
    """CRUD para la relación muchos a muchos (Revertido a AllowAny)."""
    queryset = LlaveroMaterial.objects.all()
    serializer_class = LlaveroMaterialSerializer
    permission_classes = [AllowAny]

class PedidoViewSet(viewsets.ModelViewSet):
    """CRUD de Pedidos (Revertido a AllowAny). Se mantiene el get_queryset para filtrar."""
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    permission_classes = [AllowAny] 

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and not user.is_anonymous:
            if user.is_staff:
                return Pedido.objects.all()
            return Pedido.objects.filter(cliente__user=user)
        # Si no hay autenticación, devolvemos todo (temporalmente)
        return Pedido.objects.all() 

class DetallePedidoViewSet(viewsets.ModelViewSet):
    """CRUD de DetallePedido (Revertido a AllowAny)."""
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [AllowAny]


# === 3. VISTAS DE COMPATIBILIDAD (Para App Android - Públicas) ===

class CategoriaList(generics.ListAPIView):
    """Devuelve la lista de categorías para el menú lateral de Android (Público/Navegación)."""
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny] 

class ProductoList(generics.ListAPIView):
    """Devuelve llaveros filtrados por categoría para Android (Público/Navegación)."""
    serializer_class = LlaveroSerializer 
    permission_classes = [AllowAny] 

    def get_queryset(self):
        queryset = Llavero.objects.all()
        category_id = self.kwargs.get('category_id')
        if category_id is not None:
            queryset = queryset.filter(categoria__id=category_id)
        return queryset.select_related('categoria')