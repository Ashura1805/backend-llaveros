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
            user = authenticate(username=username_or_email, password=password)
            
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

# === PRODUCTOS ===
class LlaveroSerializer(serializers.ModelSerializer):
    # Lectura: Objeto completo
    categoria_info = CategoriaSerializer(source='categoria', read_only=True)
    # Escritura: Solo ID (Renombrado a 'categoria' para coincidir con el modelo)
    categoria = serializers.PrimaryKeyRelatedField(queryset=Categoria.objects.all())

    class Meta:
        model = Llavero
        fields = [
            'id', 'nombre', 'descripcion', 'precio', 'stock_actual', 
            'imagen_url', 'categoria', 'categoria_info', 'es_personalizable'
        ]

class LlaveroMaterialSerializer(serializers.ModelSerializer):
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    material_nombre = serializers.ReadOnlyField(source='material.nombre')
    
    llavero = serializers.PrimaryKeyRelatedField(queryset=Llavero.objects.all())
    material = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all())

    class Meta:
        model = LlaveroMaterial
        fields = '__all__'

# === PEDIDOS (LÓGICA MEJORADA) ===

class DetallePedidoSerializer(serializers.ModelSerializer):
    # Lectura: Nombre del producto
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    
    # Escritura: ID del producto (Importante: nombre del campo 'llavero' coincide con modelo)
    llavero = serializers.PrimaryKeyRelatedField(queryset=Llavero.objects.all())

    class Meta:
        model = DetallePedido
        fields = ['id', 'llavero', 'llavero_nombre', 'cantidad', 'precio_unitario', 'subtotal']
        read_only_fields = ['precio_unitario', 'subtotal'] # Se calculan solos

class PedidoSerializer(serializers.ModelSerializer):
    # Permitimos escribir la lista de detalles
    detalles = DetallePedidoSerializer(many=True)
    
    # Campos de solo lectura
    cliente_nombre = serializers.ReadOnlyField(source='cliente.username')
    fecha_pedido = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'cliente', 'cliente_nombre', 'fecha_pedido', 'estado', 'total', 'detalles']
        read_only_fields = ['cliente', 'total', 'estado', 'fecha_pedido']

    def create(self, validated_data):
        # 1. Extraer los productos (detalles) de la petición
        detalles_data = validated_data.pop('detalles')
        
        # 2. Obtener el usuario actual
        user = self.context['request'].user
        
        # Buscar el perfil de Cliente asociado al usuario
        try:
            cliente = Cliente.objects.get(pk=user.pk) # Usamos PK porque Cliente hereda de User
        except Cliente.DoesNotExist:
            # Si es un admin puro (superuser) y no tiene perfil cliente, podríamos fallar o crear uno.
            # Asumimos que el usuario logueado es un Cliente válido.
            # Fallback para admins:
            cliente, _ = Cliente.objects.get_or_create(username=user.username, defaults={'email': user.email})

        # 3. Crear el Pedido (total 0 inicial)
        pedido = Pedido.objects.create(cliente=cliente, total=0, **validated_data)
        
        total_acumulado = 0

        # 4. Crear cada detalle
        for detalle_data in detalles_data:
            llavero = detalle_data['llavero']
            cantidad = detalle_data['cantidad']
            
            # Usar precio actual del producto
            precio_unitario = llavero.precio
            subtotal = precio_unitario * cantidad
            
            DetallePedido.objects.create(
                pedido=pedido,
                llavero=llavero,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                subtotal=subtotal
            )
            total_acumulado += subtotal
            

        # 5. Actualizar total y guardar
        pedido.total = total_acumulado
        pedido.save()
        
        return pedido