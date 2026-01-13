from rest_framework import serializers
from .models import Cliente, Categoria, Material, Llavero, Pedido, DetallePedido, LlaveroMaterial
from django.contrib.auth import authenticate, get_user_model
from rest_framework import exceptions
from django.db import transaction
import decimal
import traceback
import sys

User = get_user_model()

# ==========================================
# 1. LOGIN DE USUARIO (SIMPLIFICADO)
# ==========================================
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(label="Email o Username") 
    password = serializers.CharField(write_only=True, label="Contraseña")
    # user = serializers.HiddenField(default=None) # Comentado para evitar conflictos internos

    def validate(self, data):
        username_or_email = data.get("email")
        password = data.get("password")

        if username_or_email and password:
            user = None
            
            # 1. Intentar autenticar asumiendo que es un Username
            user = authenticate(username=username_or_email, password=password)
            
            # 2. Si falla, intentar buscar por Email
            if user is None:
                try:
                    # Buscamos en el modelo de Usuario genérico para ser más robustos
                    user_obj = User.objects.filter(email__iexact=username_or_email).first()
                    if user_obj:
                        user = authenticate(username=user_obj.username, password=password) 
                except Exception:
                    pass # Si falla la búsqueda, user sigue siendo None
            
            # 3. Validación final
            if user is None:
                raise exceptions.AuthenticationFailed('Credenciales incorrectas.')
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed('Usuario inactivo.')
            
        else:
            raise exceptions.ValidationError("Debe ingresar el email y la contraseña.")
            
        data['user'] = user
        return data

# ==========================================
# 2. REGISTRO DE USUARIO
# ==========================================
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = Cliente # Usamos Cliente ya que hereda de AbstractUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'telefono', 'direccion')

    def validate(self, data):
        username = data.get('username')
        email = data.get('email')

        if User.objects.filter(username=username).exists():
            raise serializers.ValidationError({'username': 'Este nombre de usuario ya está en uso.'})
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({'email': 'Este correo electrónico ya está registrado.'}) 

        return data

    def create(self, validated_data):
        # Creamos el usuario usando el método helper del modelo
        user = Cliente.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telefono=validated_data.get('telefono'),
            direccion=validated_data.get('direccion')
        )
        return user

# ==========================================
# 3. MANTENIMIENTO BÁSICO
# ==========================================
class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'telefono', 'direccion')

class MaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Material
        fields = '__all__'

class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

# ==========================================
# 4. PRODUCTOS Y RELACIONES
# ==========================================
class LlaveroSerializer(serializers.ModelSerializer):
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True
    )
    class Meta:
        model = Llavero
        fields = '__all__'

class LlaveroMaterialSerializer(serializers.ModelSerializer):
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    material_nombre = serializers.ReadOnlyField(source='material.nombre')
    
    llavero_id = serializers.PrimaryKeyRelatedField(
        queryset=Llavero.objects.all(), source='llavero', write_only=True
    )
    material_id = serializers.PrimaryKeyRelatedField(
        queryset=Material.objects.all(), source='material', write_only=True
    )

    class Meta:
        model = LlaveroMaterial
        fields = '__all__'

# ==========================================
# 5. PEDIDOS (CORREGIDO)
# ==========================================

class DetallePedidoSerializer(serializers.ModelSerializer):
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    llavero = serializers.PrimaryKeyRelatedField(queryset=Llavero.objects.all())

    class Meta:
        model = DetallePedido
        fields = ['id', 'pedido', 'llavero', 'llavero_nombre', 'cantidad', 'precio_unitario', 'subtotal']
        # NOTA: Quitamos read_only de precio/subtotal para permitir que Android los envíe si es necesario,
        # aunque el modelo también puede calcularlos.

class PedidoSerializer(serializers.ModelSerializer):
    # CORRECCIÓN CRUCIAL:
    # 1. read_only=True en detalles: Permite crear la "cabecera" del pedido sin enviar productos inmediatamente.
    #    Esto es necesario porque tu App Android envía primero el pedido y luego los detalles.
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    
    # 2. Cliente StringRelatedField es bueno para leer, pero para escribir necesitamos aceptar el ID.
    #    Como DRF maneja esto automáticamente con ModelSerializer si el campo está en 'fields', 
    #    lo dejamos simple o usamos PrimaryKeyRelatedField si da problemas.
    #    Por ahora, usaremos el comportamiento por defecto para escritura y String para lectura si se requiere.
    
    fecha_pedido = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'cliente', 'fecha_pedido', 'estado', 'total', 'detalles']
        # NOTA: 'total' NO debe ser read_only si queremos que Android envíe el total calculado.
        read_only_fields = ['fecha_pedido'] 

   