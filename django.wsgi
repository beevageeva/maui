import os
import sys

soft_dir = '/srv/www/vhosts/maui/pydj/plugins'
sys.path.insert(0,soft_dir)
sys.path.append('/srv/www/vhosts/maui/pydj')
sys.path.append('/srv/www/vhosts/maui/pydj/maui')

os.environ['DJANGO_SETTINGS_MODULE'] = 'maui.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

