from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    # ViewSets
    RegisterViewSet, 
    CategoriaViewSet, 
    LlaveroViewSet, 
    PedidoViewSet, 
    DetallePedidoViewSet,
    ClienteViewSet,
    MaterialViewSet,
    LlaveroMaterialViewSet,
    
    # Listas específicas
    CategoriaList,
    ProductoList,

    # Autenticación
    android_login_view,
    login_with_google,

    # Recuperación de contraseña
    solicitar_recuperacion,
    confirmar_recuperacion,
    
    # 🔥 CARRITO (NUEVAS IMPORTACIONES) 🔥
    obtener_carrito,
    agregar_item_carrito,
    eliminar_item_carrito,
    vaciar_carrito
)

router = DefaultRouter()
router.register(r'register', RegisterViewSet, basename='register')
router.register(r'categorias', CategoriaViewSet)
router.register(r'llaveros', LlaveroViewSet)
router.register(r'pedidos', PedidoViewSet)
router.register(r'detalle-pedidos', DetallePedidoViewSet)
router.register(r'clientes', ClienteViewSet)
router.register(r'materiales', MaterialViewSet)
router.register(r'llavero-materiales', LlaveroMaterialViewSet)

urlpatterns = [
    # Rutas del Router (CRUD automático)
    path('', include(router.urls)),

    # Rutas personalizadas (Login, Listas específicas)
    path('android/login/', android_login_view, name='android_login'),
    path('auth/google/', login_with_google, name='google_login'),
    
    # Listas para la App
    path('categories/', CategoriaList.as_view(), name='category-list'),
    path('products/<str:category_id>/', ProductoList.as_view(), name='product-list-by-category'),

    # 🔥 RUTAS DE RECUPERACIÓN DE CONTRASEÑA 🔥
    path('auth/reset-request/', solicitar_recuperacion, name='password_reset_request'),
    path('auth/reset-confirm/', confirmar_recuperacion, name='password_reset_confirm'),

    # 🔥 RUTAS DEL CARRITO DE COMPRAS 🔥
    # Nota: Ya no usamos 'views.' porque importamos las funciones arriba
    path('carrito/<int:cliente_id>/', obtener_carrito, name='obtener_carrito'),
    path('carrito/add/', agregar_item_carrito, name='agregar_item_carrito'),
    path('carrito/remove/', eliminar_item_carrito, name='eliminar_item_carrito'),
    path('carrito/clear/', vaciar_carrito, name='vaciar_carrito'),
]