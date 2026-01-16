import random 
import traceback 
from django.core.mail import send_mail 
from django.conf import settings 
from django.http import HttpResponse
from django.contrib.auth import get_user_model 
from django.contrib.auth.hashers import check_password 
from django.db.models import Q 
from django.db import transaction 
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.decorators import api_view, permission_classes
from rest_framework.authtoken.models import Token 
from rest_framework.exceptions import ValidationError 

# Importaciones de tus modelos
from .models import (
    Categoria, Llavero, Pedido, Cliente, Material, 
    LlaveroMaterial, DetallePedido, CodigoRecuperacion, 
    Carrito, ItemCarrito
)

# Importaciones de tus serializers
from .serializers import (
    RegisterSerializer, LoginSerializer, CategoriaSerializer, LlaveroSerializer, 
    PedidoSerializer, ClienteSerializer, MaterialSerializer, 
    LlaveroMaterialSerializer, DetallePedidoSerializer,
    RequestPasswordResetSerializer, ResetPasswordConfirmSerializer, CarritoSerializer,
    # 🔥 IMPORTANTE: Agregamos el nuevo serializer del token
    FCMTokenSerializer
)

User = get_user_model()

# ==========================================
# LOGIN MANUAL
# ==========================================
@api_view(['POST'])
@permission_classes([AllowAny]) 
def android_login_view(request):
    print("\n" + "█"*40)
    print("🚑 LOGIN DE EMERGENCIA (MANUAL)")

    try:
        login_input = request.data.get('email') or request.data.get('username')
        password = request.data.get('password')

        print(f"📩 Intentando entrar con: '{login_input}'")

        if not login_input or not password:
            return Response({"error": "Faltan credenciales"}, status=status.HTTP_400_BAD_REQUEST)

        login_input = str(login_input).strip()

        # Buscar usuario
        user_obj = User.objects.filter(Q(email__iexact=login_input) | Q(username__iexact=login_input)).first()

        if not user_obj:
            print(f"❌ Usuario no encontrado en tabla {User.__name__}")
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        print(f"✅ Usuario encontrado: {user_obj.email} (ID: {user_obj.id})")

        # Verificar contraseña manual
        password_is_valid = False
        if user_obj.password.startswith('pbkdf2_') or user_obj.password.startswith('argon2'):
            password_is_valid = check_password(password, user_obj.password)
        else:
            password_is_valid = (user_obj.password == password)

        if password_is_valid:
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
        error_msg = str(e)
        trace_msg = traceback.format_exc()
        print(f"🔥 CRASH DEL SERVIDOR: {error_msg}")
        print(trace_msg)
        return Response({
            "error": f"Error Interno del Servidor: {error_msg}",
            "detail": "Revisa la terminal para ver el traceback completo."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================
# PEDIDOS (SIN PAGINACIÓN PARA ANDROID)
# ==========================================

class PedidoViewSet(viewsets.ModelViewSet):
    # 🔥 CORRECCIÓN AQUÍ: Cambiado 'fecha' por 'fecha_pedido'
    queryset = Pedido.objects.all().order_by('-fecha_pedido')
    serializer_class = PedidoSerializer
    permission_classes = [AllowAny] 
    pagination_class = None 

    def get_queryset(self):
        queryset = super().get_queryset()
        cliente_id = self.request.query_params.get('cliente')
        
        if cliente_id:
            print(f"🔍 HISTORIAL: Android pide pedidos del Cliente ID: {cliente_id}")
            filtered = queryset.filter(cliente_id=cliente_id)
            print(f"   -> Encontrados: {filtered.count()}")
            return filtered
        else:
            print("👀 HISTORIAL: Android pidió TODOS los pedidos.")
            
        return queryset

    def create(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                print("🛒 Creando NUEVO pedido...")
                return super().create(request, *args, **kwargs)
        except Exception as e:
            print(f"❌ Error creando pedido: {e}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DetallePedidoViewSet(viewsets.ModelViewSet):
    queryset = DetallePedido.objects.all()
    serializer_class = DetallePedidoSerializer
    permission_classes = [AllowAny]
    pagination_class = None 

    def get_queryset(self):
        queryset = super().get_queryset()
        pedido_id = self.request.query_params.get('pedido')
        if pedido_id:
            return queryset.filter(pedido_id=pedido_id)
        return queryset

    def perform_create(self, serializer):
        llavero = serializer.validated_data['llavero']
        cantidad = serializer.validated_data['cantidad']

        # 1. Validar que haya suficiente stock
        if llavero.stock_actual < cantidad:
            raise ValidationError({
                "error": f"No hay suficiente stock de '{llavero.nombre}'. Disponibles: {llavero.stock_actual}"
            })

        try:
            with transaction.atomic():
                # 2. Restar el stock
                llavero.stock_actual -= cantidad
                llavero.save()

                # 3. Guardar el detalle del pedido
                serializer.save()
                
                print(f"📉 Stock actualizado: {llavero.nombre} ahora tiene {llavero.stock_actual}")
                
        except Exception as e:
            if isinstance(e, ValidationError):
                raise e
            raise ValidationError({"error": f"Error actualizando stock: {str(e)}"})


# ==========================================
# RESTO DE VISTAS (CRUD)
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
    pagination_class = None 

class MaterialViewSet(viewsets.ModelViewSet):
    queryset = Material.objects.all()
    serializer_class = MaterialSerializer
    permission_classes = [AllowAny]

class LlaveroMaterialViewSet(viewsets.ModelViewSet):
    queryset = LlaveroMaterial.objects.all()
    serializer_class = LlaveroMaterialSerializer
    permission_classes = [AllowAny]

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

# ==========================================
# 🔐 RECUPERACIÓN DE CONTRASEÑA
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def solicitar_recuperacion(request):
    serializer = RequestPasswordResetSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    user = User.objects.filter(email=email).first()
    
    if not user:
        return Response({"message": "Si el correo existe, se ha enviado un código."})
    
    codigo_str = str(random.randint(100000, 999999))
    
    CodigoRecuperacion.objects.filter(user=user).delete()
    CodigoRecuperacion.objects.create(user=user, codigo=codigo_str)
    
    asunto = "Recuperación de Contraseña - Llaveros3D"
    mensaje = f"""Hola {user.username},

Recibimos una solicitud para restablecer tu contraseña.
Tu código de verificación es:

{codigo_str}

Si no fuiste tú, ignora este mensaje.
"""
    
    try:
        send_mail(asunto, mensaje, settings.EMAIL_HOST_USER, [email], fail_silently=False)
        return Response({"message": "Código enviado a tu correo."})
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return Response({"error": "Error interno enviando el correo"}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirmar_recuperacion(request):
    serializer = ResetPasswordConfirmSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    codigo = serializer.validated_data['codigo']
    new_password = serializer.validated_data['new_password']
    
    user = User.objects.filter(email=email).first()
    if not user:
        return Response({"error": "Usuario no encontrado"}, status=404)
        
    registro = CodigoRecuperacion.objects.filter(user=user, codigo=codigo).first()
    if not registro:
        return Response({"error": "Código inválido o incorrecto"}, status=400)
        
    user.set_password(new_password)
    user.save()
    
    registro.delete()
    
    return Response({"message": "¡Contraseña actualizada! Ya puedes iniciar sesión."}, status=status.HTTP_200_OK)


# ==========================================
# 🛒 CARRITO DE COMPRAS (NUEVO)
# ==========================================

@api_view(['GET'])
@permission_classes([AllowAny])
def obtener_carrito(request, cliente_id):
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    carrito, created = Carrito.objects.get_or_create(cliente=cliente)
    serializer = CarritoSerializer(carrito)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def agregar_item_carrito(request):
    cliente_id = request.data.get('cliente_id')
    llavero_id = request.data.get('llavero_id')
    cantidad = int(request.data.get('cantidad', 1))

    cliente = get_object_or_404(Cliente, pk=cliente_id)
    carrito, _ = Carrito.objects.get_or_create(cliente=cliente)
    llavero = get_object_or_404(Llavero, pk=llavero_id)

    item, created = ItemCarrito.objects.get_or_create(carrito=carrito, llavero=llavero)
    
    if not created:
        item.cantidad += cantidad
    else:
        item.cantidad = cantidad
    
    if item.cantidad > llavero.stock_actual:
        return Response({"error": "No hay suficiente stock"}, status=400)

    item.save()
    
    serializer = CarritoSerializer(carrito)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def eliminar_item_carrito(request):
    cliente_id = request.data.get('cliente_id')
    llavero_id = request.data.get('llavero_id')

    cliente = get_object_or_404(Cliente, pk=cliente_id)
    carrito = get_object_or_404(Carrito, cliente=cliente)
    
    ItemCarrito.objects.filter(carrito=carrito, llavero_id=llavero_id).delete()

    serializer = CarritoSerializer(carrito)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([AllowAny])
def vaciar_carrito(request):
    cliente_id = request.data.get('cliente_id')
    cliente = get_object_or_404(Cliente, pk=cliente_id)
    carrito = get_object_or_404(Carrito, cliente=cliente)
    carrito.items.all().delete()
    return Response({"status": "Carrito vaciado"})


# ==========================================
# 🔥 NOTIFICACIONES (FCM) 🔥
# ==========================================

@api_view(['POST'])
@permission_classes([AllowAny])
def actualizar_fcm_token(request):
    """
    Recibe el token FCM del celular y lo guarda en la base de datos
    para poder enviarle notificaciones luego.
    """
    serializer = FCMTokenSerializer(data=request.data)
    if serializer.is_valid():
        cliente_id = serializer.validated_data['cliente_id']
        token = serializer.validated_data['token']
        
        try:
            cliente = Cliente.objects.get(pk=cliente_id)
            cliente.fcm_token = token
            cliente.save()
            print(f"📲 Token FCM actualizado para usuario: {cliente.username}")
            return Response({"status": "Token actualizado correctamente"})
        except Cliente.DoesNotExist:
            return Response({"error": "Cliente no encontrado"}, status=404)
            
    return Response(serializer.errors, status=400)