from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

# === ROUTER PRINCIPAL ===
# El router habilita automáticamente GET, POST, PUT, DELETE
router = DefaultRouter()

# 1. Inventario (Nombres en inglés para coincidir con la App Android)
# Al cambiar 'categorias' por 'categories', la App Android usará este ViewSet completo
router.register(r'categories', views.CategoriaViewSet)       # /api/categories/ (GET, POST, DELETE)
router.register(r'llaveros', views.LlaveroViewSet)           # /api/llaveros/   (GET, POST, DELETE)
router.register(r'materials', views.MaterialViewSet)
router.register(r'llavero-materiales', views.LlaveroMaterialViewSet)

# 2. Usuarios y Ventas
router.register(r'clientes', views.ClienteViewSet)
# MODIFICACIÓN: Se añade basename='pedidos' porque el ViewSet usa get_queryset dinámico
router.register(r'pedidos', views.PedidoViewSet, basename='pedidos')
router.register(r'detalle-pedidos', views.DetallePedidoViewSet)
router.register(r'register', views.RegisterViewSet, basename='register')

# === URLS ===
urlpatterns = [
    # 1. Rutas del Router (Aquí entra /api/categories/ con permiso de escritura)
    path('', include(router.urls)),
    
    # 2. Autenticación
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/google/', views.login_with_google, name='google-login'),
    
    # 3. Rutas específicas Android
    # Solo dejamos la de productos filtrados porque esa sí necesita lógica especial.
    path('products/<int:category_id>/', views.ProductoList.as_view(), name='android-products'),

    # 4. Login Android
    path('android/login/', views.android_login_view, name='android-login'),
]