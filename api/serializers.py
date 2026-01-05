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
# Este lo dejamos IGUAL que en tu código original para no romper el catálogo
class LlaveroSerializer(serializers.ModelSerializer):
    # Lectura: Objeto completo
    categoria_info = CategoriaSerializer(source='categoria', read_only=True)
    # Escritura: Solo ID
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True
    )
    class Meta:
        model = Llavero
        fields = '__all__'

class LlaveroMaterialSerializer(serializers.ModelSerializer):
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    material_nombre = serializers.ReadOnlyField(source='material.nombre')
    
    llavero = serializers.PrimaryKeyRelatedField(queryset=Llavero.objects.all())
    material = serializers.PrimaryKeyRelatedField(queryset=Material.objects.all())

    class Meta:
        model = LlaveroMaterial
        fields = '__all__'

# === PEDIDOS (MODIFICADO PARA QUE FUNCIONE EL CHECKOUT) ===

class DetallePedidoSerializer(serializers.ModelSerializer):
    # 1. Para Leer (Historial): Enviamos el nombre del producto
    llavero_nombre = serializers.ReadOnlyField(source='llavero.nombre')
    
    # 2. Para Escribir (Carrito): Recibimos el ID en el campo "llavero"
    # IMPORTANTE: Esto coincide con el JSON {"llavero": 1, "cantidad": 2} que manda Android
    llavero = serializers.PrimaryKeyRelatedField(queryset=Llavero.objects.all())

    class Meta:
        model = DetallePedido
        fields = ['id', 'llavero', 'llavero_nombre', 'cantidad', 'precio_unitario', 'subtotal']
        # Precio y subtotal se calculan solos en el backend
        read_only_fields = ['precio_unitario', 'subtotal']

class PedidoSerializer(serializers.ModelSerializer):
    cliente = serializers.StringRelatedField(read_only=True)
    # "many=True" permite recibir una lista de productos
    detalles = DetallePedidoSerializer(many=True)
    
    fecha_pedido = serializers.DateTimeField(format="%Y-%m-%d %H:%M", read_only=True)

    class Meta:
        model = Pedido
        fields = ['id', 'cliente', 'fecha_pedido', 'estado', 'total', 'detalles']
        read_only_fields = ['cliente', 'total', 'estado', 'fecha_pedido']

    # Lógica mágica para guardar el pedido y sus productos
    def create(self, validated_data):
        # 1. Sacamos la lista de productos
        detalles_data = validated_data.pop('detalles')
        
        # 2. Asignamos el cliente actual
        cliente = self.context['request'].user
        
        # 3. Creamos el pedido (cabecera)
        pedido = Pedido.objects.create(cliente=cliente, total=0, **validated_data)
        
        total_acumulado = 0

        # 4. Guardamos cada producto del carrito
        for detalle in detalles_data:
            llavero_obj = detalle['llavero']
            cantidad = detalle['cantidad']
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
        
        # 5. Actualizamos el total final
        pedido.total = total_acumulado
        pedido.save()
        
        return pedido