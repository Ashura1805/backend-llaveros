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

User = get_user_model()

# ==========================================
# 1. LOGIN BLINDADO (SOLUCIÓN ERROR 500)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    print("--- INTENTO DE LOGIN DESDE ANDROID ---") # Log para depurar
    
    # 1. Validar datos de entrada manualmente para evitar errores de serializer
    email_or_username = request.data.get('email')
    password = request.data.get('password')

    if not email_or_username or not password:
        return Response({"error": "Faltan credenciales"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 2. Buscar usuario (por email o username)
        user_found = User.objects.filter(Q(email__iexact=email_or_username) | Q(username__iexact=email_or_username)).first()

        if not user_found:
            return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)

        # 3. Verificar contraseña
        user = authenticate(username=user_found.username, password=password)

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            
            # --- AQUÍ ESTABA EL ERROR 500 ---
            # Intentamos obtener el cliente. Si falla, LO CREAMOS.
            try:
                cliente = Cliente.objects.get(user=user)
            except Cliente.DoesNotExist:
                print(f"El usuario {user.username} no tenía perfil de Cliente. Creando uno...")
                cliente = Cliente.objects.create(
                    user=user,
                    nombre=user.first_name or user.username,
                    email=user.email
                )
            except Exception as e:
                # Si hay duplicados u otro error raro, tomamos el primero que aparezca
                cliente = Cliente.objects.filter(user=user).first()
            
            # Si después de todo sigue siendo None (muy raro), evitamos el crash
            cliente_id = cliente.id if cliente else 0

            return Response({
                "message": "Login exitoso",
                "user_id": user.id,
                "cliente_id": cliente_id, 
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "token": token.key 
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Contraseña incorrecta"}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        # Si ocurre CUALQUIER error interno, lo imprimimos en consola y devolvemos JSON
        # en lugar de HTML rojo.
        print(f"ERROR CRÍTICO EN LOGIN: {e}")
        return Response({"error": f"Error interno del servidor: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_google(request):
    return Response({'status': 'success', 'token': 'demo_token_123'}, status=200)

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                Cliente.objects.get_or_create(user=user, defaults={'nombre': user.username, 'email': user.email})
                return Response({
                    "token": token.key, 
                    "message": "¡Cuenta creada exitosamente!", 
                    "success": True
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==========================================
# 2. API VIEWSETS (CRUD)
# ==========================================

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]

class LlaveroViewSet(viewsets.ModelViewSet):
    queryset = Llavero.objects.all()
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


# ==========================================
# 3. LISTAS SIMPLES (AQUÍ ESTÁ LA CLASE QUE FALTABA)
# ==========================================

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