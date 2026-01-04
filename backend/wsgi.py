"""
WSGI config for backend project.
"""

import os
import pymysql  # <--- NUEVO
pymysql.install_as_MySQLdb()  # <--- NUEVO: Esto engaña a Django para usar pymysql

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()