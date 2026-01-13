from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# === ROUTER PRINCIPAL ===
router = DefaultRouter()

# 1. INVENTARIO
# CORRECCIÓN IMPORTANTE: Cambiado a 'categorias' (español) para coincidir con la petición de la App/Web
router.register(r'categorias', views.CategoriaViewSet)       # /api/categorias/
router.register(r'llaveros', views.LlaveroViewSet)           # /api/llaveros/
router.register(r'materials', views.MaterialViewSet)         # /api/materials/ (La app lo pide así en el log)
router.register(r'llavero-materiales', views.LlaveroMaterialViewSet)

# 2. USUARIOS Y VENTAS
router.register(r'clientes', views.ClienteViewSet)
router.register(r'pedidos', views.PedidoViewSet, basename='pedidos')
router.register(r'detalle-pedidos', views.DetallePedidoViewSet)
router.register(r'register', views.RegisterViewSet, basename='register')

# === URLS ===
urlpatterns = [
    # 1. Rutas del Router
    path('', include(router.urls)),
    
    # 2. Autenticación
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/google/', views.login_with_google, name='google-login'),
    
    # 3. Rutas específicas (Filtros manuales si los usas)
    path('products/<int:category_id>/', views.ProductoList.as_view(), name='android-products'),

    # 4. Login Android (Híbrido)
    path('android/login/', views.android_login_view, name='android-login'),
]