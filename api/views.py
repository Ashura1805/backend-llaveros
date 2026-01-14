from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token 
from django.contrib.auth import authenticate, get_user_model 
from django.db.models import Q 
from django.db import transaction 
from .models import Categoria, Llavero, Pedido, Cliente, Material, LlaveroMaterial, DetallePedido

from .serializers import (
    RegisterSerializer, LoginSerializer, CategoriaSerializer, LlaveroSerializer, 
    PedidoSerializer, ClienteSerializer, MaterialSerializer, 
    LlaveroMaterialSerializer, DetallePedidoSerializer
)

# IMPORTANTE: Con tu configuración, esta variable 'User' AHORA ES 'Cliente'
User = get_user_model()

# ==========================================
# LOGIN ADAPTADO A AUTH_USER_MODEL = 'api.Cliente'
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    print("\n" + "="*40)
    print("👤 LOGIN (MODELO PERSONALIZADO: CLIENTE)")

    # 1. Obtener datos (Email/Usuario y Contraseña)
    # Tu App Android envía 'email' y 'password'
    login_input = request.data.get('email')
    if not login_input:
        login_input = request.data.get('username')
        
    password = request.data.get('password')

    print(f"📩 Intentando entrar con: '{login_input}'")

    if not login_input or not password:
        return Response({"error": "Faltan credenciales"}, status=status.HTTP_400_BAD_REQUEST)

    login_input = str(login_input).strip()

    # 2. PRIMER PASO: BUSCAR EL USUARIO (CLIENTE) MANUALMENTE
    # Como tu usuario es el Cliente, buscamos directo en el modelo User (que es Cliente)
    # Buscamos por email O por username (para que funcione con AdminShura o el correo)
    user_obj = User.objects.filter(Q(email__iexact=login_input) | Q(username__iexact=login_input) | Q(nombre__iexact=login_input)).first()

    if not user_obj:
        print(f"❌ No se encontró ningún Cliente/Usuario con: {login_input}")
        return Response({"error": "Usuario no encontrado en la tabla Clientes."}, status=status.HTTP_404_NOT_FOUND)

    print(f"✅ Usuario/Cliente encontrado: {user_obj.email} (ID: {user_obj.id})")

    # 3. SEGUNDO PASO: VERIFICAR CONTRASEÑA
    # Usamos authenticate. Como authenticate espera 'username', le pasamos 
    # el username REAL que encontramos en la base de datos (user_obj.username)
    # o el campo que tu modelo use como identificador.
    
    user = authenticate(username=user_obj.username, password=password)
    
    # Si authenticate falla con username, intentamos pasando el email (algunos backends lo requieren)
    if user is None:
        user = authenticate(email=user_obj.email, password=password)

    if user is not None:
        # Generar Token (El token se vincula a 'user', que en tu caso es 'Cliente')
        token, _ = Token.objects.get_or_create(user=user)
        
        print("🚀 LOGIN EXITOSO.")
        
        # OJO: En tu caso, user_id y cliente_id SON LO MISMO
        return Response({
            "message": "Login exitoso",
            "user_id": user.id,
            "cliente_id": user.id,   # Mismo ID porque User ES Cliente
            "username": user.username, # O user.nombre, según tu modelo
            "email": user.email,
            "is_staff": user.is_staff,
            "token": token.key 
        }, status=status.HTTP_200_OK)

    else:
        print("❌ Contraseña incorrecta para este Cliente.")
        return Response({"error": "Contraseña incorrecta"}, status=status.HTTP_401_UNAUTHORIZED)


# ==========================================
# RESTO DEL CÓDIGO (CRUD)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_google(request):
    return Response({'status': 'success', 'token': 'demo_token_123'}, status=200)

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        # Usamos el serializer de registro
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                # Esto crea un 'Cliente' directamente porque ese es tu User model
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                
                return Response({
                    "token": token.key, 
                    "message": "¡Cuenta creada exitosamente!", 
                    "success": True
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]

class LlaveroViewSet(viewsets.ModelViewSet):
    queryset = Llavero.objects.all()
    serializer_class = LlaveroSerializer
    permission_classes = [AllowAny]

class ClienteViewSet(viewsets.ModelViewSet):
    # OJO: User es Cliente, así que esto lista los usuarios
    queryset = User.objects.all() 
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
    queryset = Pedido.objects.all().order_by('-fecha_pedido')
    serializer_class = PedidoSerializer
    permission_classes = [AllowAny] 
    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        if cliente_id:
            return queryset.filter(cliente_id=cliente_id)
        return queryset
    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                return super().create(request, *args, **kwargs)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [AllowAny]
    def get_queryset(self):
        queryset = super().get_queryset()
        pedido_id = self.request.query_params.get('pedido')
        if pedido_id:
            return queryset.filter(pedido_id=pedido_id)
        return queryset

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
        return queryset