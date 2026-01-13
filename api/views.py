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

# ==========================================
# 1. LOGIN Y REGISTRO
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def login_with_google(request):
    return Response({'status': 'success', 'token': 'demo_token_123'}, status=200)

@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    """ LOGIN QUE NO FALLA (ERROR 500 SOLUCIONADO) """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data.get('user')
        
        # Respaldo de seguridad si el serializer no devuelve el objeto user
        if user is None:
            email_input = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            User = get_user_model()
            # Búsqueda manual robusta
            try:
                user_obj = User.objects.filter(Q(email__iexact=email_input) | Q(username__iexact=email_input)).first()
                if user_obj:
                    user = authenticate(username=user_obj.username, password=password)
            except Exception:
                pass

        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            
            # --- AQUÍ EVITAMOS EL ERROR 500 ---
            # Usamos get_or_create. Si el usuario no tiene Cliente, lo crea.
            cliente, _ = Cliente.objects.get_or_create(
                user=user,
                defaults={
                    'nombre': user.first_name or user.username,
                    'email': user.email
                }
            )

            return Response({
                "message": "Login exitoso",
                "user_id": user.id,
                "cliente_id": cliente.id, 
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
                "token": token.key 
            }, status=status.HTTP_200_OK)
        else:
            return Response({"error": "Credenciales inválidas."}, status=status.HTTP_401_UNAUTHORIZED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    def create(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                # Crear cliente automáticamente
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
# 2. CRUD PRINCIPAL
# ==========================================

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
# 3. LISTAS SIMPLES (CLASES QUE FALTABAN)
# ==========================================

class CategoriaList(generics.ListAPIView):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    permission_classes = [AllowAny] 

# ESTA ES LA CLASE QUE FALTABA Y DABA EL ERROR EN LA TERMINAL
class ProductoList(generics.ListAPIView):
    serializer_class = LlaveroSerializer 
    permission_classes = [AllowAny] 

    def get_queryset(self):
        queryset = Llavero.objects.all()
        category_id = self.kwargs.get('category_id')
        if category_id is not None:
            queryset = queryset.filter(categoria__id=category_id)
        return queryset.select_related('categoria')