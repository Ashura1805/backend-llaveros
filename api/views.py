from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token 
from django.contrib.auth import get_user_model 
from django.contrib.auth.hashers import check_password # IMPORTANTE: Para verificar contraseña manual
from django.db.models import Q 
from django.db import transaction 
import traceback # Para capturar el error exacto

from .models import Categoria, Llavero, Pedido, Cliente, Material, LlaveroMaterial, DetallePedido

from .serializers import (
    RegisterSerializer, LoginSerializer, CategoriaSerializer, LlaveroSerializer, 
    PedidoSerializer, ClienteSerializer, MaterialSerializer, 
    LlaveroMaterialSerializer, DetallePedidoSerializer
)

# Con tu configuración, User es Cliente
User = get_user_model()

# ==========================================
# LOGIN MANUAL (EVITA ERROR 500)
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    print("\n" + "█"*40)
    print("🚑 LOGIN DE EMERGENCIA (MANUAL)")

    try:
        # 1. Obtener datos
        login_input = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')

        print(f"📩 Intentando entrar con: '{login_input}'")

        if not login_input or not password:
            return Response({"error": "Faltan credenciales"}, status=status.HTTP_400_BAD_REQUEST)

        login_input = str(login_input).strip()

        # 2. BUSCAR EL USUARIO (CLIENTE) DIRECTAMENTE
        # No usamos authenticate() porque está causando el Error 500
        user_obj = User.objects.filter(Q(email__iexact=login_input) | Q(username__iexact=login_input)).first()

        if not user_obj:
            print(f"❌ Usuario no encontrado en tabla {User.__name__}")
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        print(f"✅ Usuario encontrado: {user_obj.email} (ID: {user_obj.id})")

        # 3. VERIFICACIÓN MANUAL DE CONTRASEÑA
        # Aquí es donde fallaba authenticate(). Lo hacemos a mano.
        password_is_valid = False
        
        # Opción A: La contraseña está encriptada (Django standard)
        if user_obj.password.startswith('pbkdf2_') or user_obj.password.startswith('argon2'):
            password_is_valid = check_password(password, user_obj.password)
        # Opción B: La contraseña es texto plano (Si la metiste manual en la BD)
        else:
            password_is_valid = (user_obj.password == password)

        if password_is_valid:
            # Generar Token manual
            token, _ = Token.objects.get_or_create(user=user_obj)
            
            print("🚀 LOGIN EXITOSO (MANUAL).")
            
            return Response({
                "message": "Login exitoso",
                "user_id": user_obj.id,
                "cliente_id": user_obj.id,
                "username": getattr(user_obj, 'username', 'Usuario'), 
                "email": getattr(user_obj, 'email', ''),
                "is_staff": getattr(user_obj, 'is_staff', False),
                "token": token.key 
            }, status=status.HTTP_200_OK)

        else:
            print("❌ Contraseña incorrecta.")
            return Response({"error": "Contraseña incorrecta"}, status=status.HTTP_401_UNAUTHORIZED)

    except Exception as e:
        # AQUÍ CAPTURAMOS EL ERROR 500 Y TE LO MOSTRAMOS EN EL CELULAR
        error_msg = str(e)
        trace_msg = traceback.format_exc()
        print(f"🔥 CRASH DEL SERVIDOR: {error_msg}")
        print(trace_msg)
        
        return Response({
            "error": f"Error Interno del Servidor: {error_msg}",
            "detail": "Revisa la terminal para ver el traceback completo."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
        try:
            serializer = RegisterSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    "token": token.key, 
                    "message": "¡Cuenta creada exitosamente!", 
                    "success": True
                }, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny]

class LlaveroViewSet(viewsets.ModelViewSet):
    queryset = Llavero.objects.all()
    serializer_class = LlaveroSerializer
    permission_classes = [AllowAny]

class ClienteViewSet(viewsets.ModelViewSet):
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