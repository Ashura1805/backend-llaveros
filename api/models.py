from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'categorias'

    def __str__(self):
        return self.nombre

class Material(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2)
    unidad_medida = models.CharField(max_length=50)

    class Meta:
        db_table = 'materiales'

    def __str__(self):
        return self.nombre

class Llavero(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True)
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.IntegerField()
    es_personalizable = models.BooleanField(default=False)
    imagen_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'llaveros'

    def __str__(self):
        return self.nombre

class LlaveroMaterial(models.Model):
    llavero = models.ForeignKey(Llavero, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    cantidad_requerida = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'llavero_materiales'
        unique_together = ('llavero', 'material')

class Cliente(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    # Solución de conflicto con auth.User nativo de Django
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='cliente_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='cliente_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

class Pedido(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En proceso', 'En proceso'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    ]
    # CAMBIO IMPORTANTE: SET_NULL para no borrar pedidos si se borra el cliente
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'pedidos'

    def __str__(self):
        return f"Pedido #{self.id} - {self.cliente}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    # Si borran el llavero del sistema, mantenemos el registro poniendo NULL
    llavero = models.ForeignKey(Llavero, on_delete=models.SET_NULL, null=True)
    cantidad = models.IntegerField(default=1)
    
    # Precios históricos para reportes
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    personalizacion = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'detalle_pedidos'

    def save(self, *args, **kwargs):
        # CAMBIO IMPORTANTE: Cálculo automático del subtotal antes de guardar
        if self.precio_unitario and self.cantidad:
            self.subtotal = float(self.precio_unitario) * int(self.cantidad)
        super().save(*args, **kwargs)

    def __str__(self):
        prod_name = self.llavero.nombre if self.llavero else "Producto Eliminado"
        return f"{self.cantidad} x {prod_name}"

# ==========================================
# 🔥 NUEVO MODELO PARA RECUPERAR CONTRASEÑA 🔥
# ==========================================
class CodigoRecuperacion(models.Model):
    user = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    codigo = models.CharField(max_length=6)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'codigos_recuperacion'

    def __str__(self):
        return f"{self.user.email} - {self.codigo}"
class Carrito(models.Model):
    cliente = models.OneToOneField(Cliente, on_delete=models.CASCADE, related_name='carrito')
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Carrito de {self.cliente.nombre}"

    @property
    def total(self):
        total = sum(item.subtotal for item in self.items.all())
        return total

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    llavero = models.ForeignKey(Llavero, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        # Asumiendo que llavero.precio es un Decimal o Float
        return self.llavero.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.llavero.nombre}"