from rest_framework import serializers
from .models import Cliente, Categoria, Material, Llavero, Pedido, DetallePedido, LlaveroMaterial
from django.contrib.auth import authenticate, get_user_model
from rest_framework import exceptions

User = get_user_model()

# === LOGIN DE USUARIO ===
class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(label="Email o Username") 
    password = serializers.CharField(write_only=True, label="Contraseña")
    user = serializers.HiddenField(default=None) 

    def validate(self, data):
        username_or_email = data.get("email")
        password = data.get("password")

        if username_or_email and password:
            user = None
            # 1. Autenticar por username
            user = authenticate(username=username_or_email, password=password)
            
            # 2. Autenticar por email
            if user is None and ('@' in username_or_email):
                try:
                    cliente = User.objects.get(email__iexact=username_or_email)
                    user = authenticate(username=cliente.username, password=password) 
                except User.DoesNotExist:
                    user = None 
            
            if user is None:
                raise exceptions.AuthenticationFailed('Credenciales incorrectas.')
            
            if not user.is_active:
                raise exceptions.AuthenticationFailed('Usuario inactivo.')
            
        else:
            raise exceptions.ValidationError("Debe ingresar el email y la contraseña.")
            
        data['user'] = user
        return data

# === REGISTRO DE USUARIO ===
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    
    class Meta:
        model = Cliente 
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

# === MANTENIMIENTO BÁSICO ===
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

# === PRODUCTOS Y RELACIONES ===
class LlaveroSerializer(serializers.ModelSerializer):
    # Lectura: Objeto completo (Para que el catálogo en Android funcione bien y muestre datos)
    categoria = CategoriaSerializer(read_only=True)
    
    # Escritura: Solo ID (Para crear/editar productos)
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

# === PEDIDOS (LÓGICA DE CHECKOUT) ===

class DetallePedidoSerializer(serializers.ModelSerializer):
    # Lectura: Nombre del producto
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    
    # Escritura: ID del producto
    # Android debe enviar {"llavero": ID, "cantidad": N}
    llavero = serializers.PrimaryKeyRelatedField(queryset=Llavero.objects.all())

    class Meta:
        model = DetallePedido
        fields = ['id', 'llavero', 'llavero_nombre', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    cliente = serializers.StringRelatedField(read_only=True)
    detalles = DetallePedidoSerializer(many=True)
    fecha_pedido = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'cliente', 'fecha_pedido', 'estado', 'total', 'detalles']
        read_only_fields = ['cliente', 'total', 'estado', 'fecha_pedido']

    def create(self, validated_data):
        # 1. Extraer los productos
        detalles_data = validated_data.pop('detalles')
        
        # 2. Obtener el usuario
        user = self.context['request'].user
        
        # 3. Buscar o crear el cliente
        cliente, _ = Cliente.objects.get_or_create(username=user.username, defaults={'email': user.email})

        # 4. Crear el pedido
        pedido = Pedido.objects.create(cliente=cliente, total=0, **validated_data)
        
        total_acumulado = 0

        # 5. Crear los detalles
        for detalle_data in detalles_data:
            llavero_obj = detalle_data['llavero']
            cantidad = detalle_data['cantidad']
            precio = llavero_obj.precio
            subtotal = precio * cantidad
            
            DetallePedido.objects.create(
                pedido=pedido,
                llavero=llavero_obj,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=subtotal
            )
            total_acumulado += subtotal
        
        # 6. Actualizar total
        pedido.total = total_acumulado
        pedido.save()
        
        return pedido