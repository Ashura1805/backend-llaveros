import pymysql

# 1. ESTA LÍNEA ES VITAL: Convierte pymysql en MySQLdb
pymysql.install_as_MySQLdb()

# 2. Ahora sí podemos importar MySQLdb (porque pymysql ya tomó su lugar)
import MySQLdb

# 3. Aplicamos el parche de versión para engañar a Django
if hasattr(MySQLdb, 'version_info'):
    MySQLdb.version_info = (2, 2, 1, 'final', 0)
    MySQLdb.__version__ = '2.2.1'