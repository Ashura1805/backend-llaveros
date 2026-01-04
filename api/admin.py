# api/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Cliente, Categoria, Material, Llavero, Pedido, DetallePedido, LlaveroMaterial

# === REGISTRO CORRECTO: Cliente (modelo) + UserAdmin (clase) ===
@admin.register(Cliente)
class ClienteAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'telefono', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')

    fieldsets = UserAdmin.fieldsets + (
        ('Datos Extra', {
            'fields': ('telefono', 'direccion', 'fecha_registro')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Datos Extra', {
            'fields': ('telefono', 'direccion')
        }),
    )

# === RESTO DE MODELOS ===
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock_actual', 'unidad_medida')
    search_fields = ('nombre',)

@admin.register(Llavero)
class LlaveroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'stock_actual', 'es_personalizable')
    list_filter = ('categoria', 'es_personalizable')
    search_fields = ('nombre',)

@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'cliente', 'fecha_pedido', 'estado', 'total')
    list_filter = ('estado', 'fecha_pedido')
    readonly_fields = ('fecha_pedido', 'total')

# Registrar sin configuración extra
admin.site.register(LlaveroMaterial)
admin.site.register(DetallePedido)