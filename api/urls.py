from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# === ROUTER PRINCIPAL (Genera URLs automáticas para los ViewSets) ===
# Este router crea automáticamente las rutas GET, POST, PUT, DELETE para cada ViewSet registrado.
router = DefaultRouter()

# 1. Inventario y Productos
router.register(r'categorias', views.CategoriaViewSet)          # /api/categorias/
router.register(r'llaveros', views.LlaveroViewSet)              # /api/llaveros/
router.register(r'materials', views.MaterialViewSet)            # /api/materials/
router.register(r'llavero-materiales', views.LlaveroMaterialViewSet) # /api/llavero-materiales/

# 2. Usuarios, Ventas y Pedidos
router.register(r'clientes', views.ClienteViewSet)              # /api/clientes/
router.register(r'pedidos', views.PedidoViewSet)                # /api/pedidos/
router.register(r'detalle-pedidos', views.DetallePedidoViewSet) # /api/detalle-pedidos/
router.register(r'register', views.RegisterViewSet, basename='register') # /api/register/


# === LISTA DEFINITIVA DE URLS ===
urlpatterns = [
    # 1. Incluimos todas las rutas generadas por el router
    path('', include(router.urls)),
    
    # 2. Rutas de Autenticación (JWT para Web)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'), # Login estándar JWT
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),      # Refrescar token JWT
    path('auth/google/', views.login_with_google, name='google-login'),           # Login con Google (Simulado)
    
    # 3. Rutas específicas para compatibilidad con la App Android
    # Estas rutas usan las vistas genéricas (ListAPIView) definidas al final de tu views.py
    path('categories/', views.CategoriaList.as_view(), name='android-categories'),
    path('products/<int:category_id>/', views.ProductoList.as_view(), name='android-products'),

    # ¡NUEVO! Ruta Login Simplificada para Android
    # Esta es la URL que debes usar en tu app móvil: http://IP:8000/api/android/login/
    path('android/login/', views.android_login_view, name='android-login'),
]