from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    # NUEVO CAMPO: Para guardar el link de la imagen de la categoría
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
    # NUEVO CAMPO: Para guardar el link de la imagen del producto
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
        return f"{self.first_name} {self.last_name}"

class Pedido(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completado', 'Completado'),
        ('cancelado', 'Cancelado'),
    ]
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='pendiente')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00) # Added default just in case

    class Meta:
        db_table = 'pedidos'

    def __str__(self):
        return f"Pedido {self.id}"

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE) # Added related_name for serializer
    llavero = models.ForeignKey(Llavero, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    personalizacion = models.TextField(blank=True)
    # Agregamos subtotal para facilitar cálculos, aunque se puede calcular
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    class Meta:
        db_table = 'detalle_pedidos'
        # unique_together = ('pedido', 'llavero') # Opcional: Si quieres permitir el mismo llavero dos veces (ej. personalizaciones distintas), quita esto.

    def __str__(self):
        return f"{self.cantidad} x {self.llavero.nombre}"