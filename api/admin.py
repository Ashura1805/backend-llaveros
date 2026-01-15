from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Cliente, 
    Categoria, 
    Material, 
    Llavero, 
    Pedido, 
    DetallePedido, 
    LlaveroMaterial
)

# ==========================================
# 1. CONFIGURACIÓN DE CLIENTE (USUARIO)
# ==========================================
@admin.register(Cliente)
class ClienteAdmin(UserAdmin):
    # Columnas visibles en la lista de usuarios
    list_display = ('id', 'username', 'email', 'first_name', 'last_name', 'telefono', 'is_staff')
    
    # Filtros laterales
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    # Buscador (Busca por usuario, correo o nombre)
    search_fields = ('username', 'email', 'first_name', 'last_name')

    # Configuración del formulario de edición
    fieldsets = UserAdmin.fieldsets + (
        ('Datos Extra', {
            'fields': ('telefono', 'direccion')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos Extra', {
            'fields': ('telefono', 'direccion')
        }),
    )

# ==========================================
# 2. CONFIGURACIÓN DE PRODUCTOS (LLAVEROS)
# ==========================================

class LlaveroMaterialInline(admin.TabularInline):
    model = LlaveroMaterial
    extra = 1 
    autocomplete_fields = ['material'] 

@admin.register(Llavero)
class LlaveroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock_actual', 'es_personalizable')
    list_filter = ('categoria', 'es_personalizable')
    search_fields = ('nombre', 'descripcion')
    inlines = [LlaveroMaterialInline]

# ==========================================
# 3. CONFIGURACIÓN DE PEDIDOS (TIENDA PRO)
# ==========================================

class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0 
    can_delete = False 
    readonly_fields = ('llavero', 'cantidad', 'precio_unitario', 'subtotal') 

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # 1. Columnas a mostrar
    list_display = ('id', 'ver_cliente', 'fecha_pedido', 'total', 'estado')
    
    # 🔥 ESTA ES LA ACTUALIZACIÓN CLAVE 🔥
    # Permite cambiar el estado (Pendiente -> Enviado) directamente desde la lista
    list_editable = ('estado',)
    
    # 2. Filtros laterales
    list_filter = ('estado', 'fecha_pedido')
    
    # 3. Buscador potente
    search_fields = ('cliente__username', 'cliente__email', 'cliente__first_name', 'id')
    
    # 4. Campos de solo lectura
    readonly_fields = ('fecha_pedido',)
    
    # 5. Detalles dentro del pedido
    inlines = [DetallePedidoInline]
    
    # 6. Ordenar (Más recientes primero)
    ordering = ('-fecha_pedido',)

    def ver_cliente(self, obj):
        return obj.cliente.username if obj.cliente else "Cliente Eliminado"
    ver_cliente.short_description = "Cliente"

# ==========================================
# 4. OTROS REGISTROS
# ==========================================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock_actual', 'unidad_medida')
    search_fields = ('nombre',)