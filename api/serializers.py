from rest_framework import serializers
from .models import Cliente, Categoria, Material, Llavero, Pedido, DetallePedido, LlaveroMaterial
# Importamos get_user_model para asegurar que trabajamos con el modelo Cliente
from django.contrib.auth import authenticate, get_user_model 
from rest_framework import exceptions 

# Obtener el modelo de usuario activo del proyecto (que es Cliente)
User = get_user_model() 

# === LOGIN DE USUARIO (EL PUNTO CRÍTICO) ===
class LoginSerializer(serializers.Serializer):
    """
    Serializador para validar el login de usuario (email/username y contraseña).
    """
    # CORRECCIÓN CLAVE: Cambiamos el nombre del campo esperado de 'username' a 'email'
    # para que coincida con el JSON que envía la App Android.
    email = serializers.CharField(label="Email o Username") 
    password = serializers.CharField(write_only=True, label="Contraseña")
    user = serializers.HiddenField(default=None) 

    def validate(self, data):
        # Renombrar 'email' a 'username' internamente para que la función authenticate funcione
        username_or_email = data.get("email") # <-- Tomamos el valor de 'email'
        password = data.get("password")

        # --- DEBUG LOGIN START ---
        print(f"\n--- DEBUG LOGIN START ---")
        print(f"Intento de login con email (transformado a username): {username_or_email}")
        
        if username_or_email and password:
            
            user = None
            
            # 1. Intentar autenticar por username.
            # NOTA: En este punto, 'username_or_email' podría ser el email.
            user = authenticate(username=username_or_email, password=password)
            
            print(f"Resultado autenticación por Username directo: {user}")
            
            # 2. Si falla y parece un email, intentar autenticar buscando el username real del cliente
            if user is None and ('@' in username_or_email):
                try:
                    # Buscamos el objeto Cliente (User) por email (insensible a mayúsculas/minúsculas)
                    cliente = User.objects.get(email__iexact=username_or_email)
                    
                    # 3. Intentar autenticar usando el username REAL del objeto Cliente encontrado
                    user = authenticate(username=cliente.username, password=password) 
                    
                    print(f"Cliente encontrado por email ({cliente.username}). Resultado autenticación por Email: {user}")

                except User.DoesNotExist:
                    print(f"Usuario NO encontrado con email: {username_or_email}")
                    user = None 
            
            # Si la autenticación falló, levanta error
            if user is None:
                print(f"--- DEBUG LOGIN FAILED: Credenciales incorrectas ---")
                raise exceptions.AuthenticationFailed('Credenciales incorrectas. Verifique su email/username y contraseña.')
            
            # Verificar si el usuario está activo
            if not user.is_active:
                print(f"--- DEBUG LOGIN FAILED: Usuario inactivo ---")
                raise exceptions.AuthenticationFailed('Usuario inactivo.')
            
            # --- DEBUGGING STEP 3: Éxito ---
            print(f"--- DEBUG LOGIN SUCCESSFUL for user ID: {user.id} ---")
            
        else:
            print(f"--- DEBUG LOGIN FAILED: Campos faltantes ---")
            raise exceptions.ValidationError("Debe ingresar el email y la contraseña.") # Mensaje ajustado
            
        # Almacenamos el objeto de usuario en el diccionario
        data['user'] = user
        print(f"--- DEBUG LOGIN END ---\n")
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
            raise serializers.ValidationError({'email': 'Este correo electrónico ya está registrado. Inicie sesión.'}) 

        return data

    def create(self, validated_data):
        print(f"--- DEBUG REGISTER: Creando usuario {validated_data.get('username')}...")
        user = Cliente.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            telefono=validated_data.get('telefono'),
            direccion=validated_data.get('direccion')
        )
        print(f"--- DEBUG REGISTER: Usuario creado con ID {user.id} ---")
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
    categoria = CategoriaSerializer(read_only=True)
    categoria_id = serializers.PrimaryKeyRelatedField(
        queryset=Categoria.objects.all(), source='categoria', write_only=True
    )
    class Meta:
        model = Llavero
        fields = '__all__'

# ¡NUEVO! Para asignar materiales a llaveros
class LlaveroMaterialSerializer(serializers.ModelSerializer):
    # Campos de lectura (nombres)
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

# === PEDIDOS ===
class DetallePedidoSerializer(serializers.ModelSerializer):
    llavero = LlaveroSerializer(read_only=True)
    llavero_id = serializers.PrimaryKeyRelatedField(
        queryset=Llavero.objects.all(), source='llavero', write_only=True
    )
    class Meta:
        model = DetallePedido
        fields = '__all__'

class PedidoSerializer(serializers.ModelSerializer):
    cliente = serializers.StringRelatedField(read_only=True)
    detalles = DetallePedidoSerializer(many=True, read_only=True)
    class Meta:
        model = Pedido
        fields = '__all__'
        read_only_fields = ('cliente', 'total', 'fecha_pedido')