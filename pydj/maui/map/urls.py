from django.conf.urls.defaults import *
from django.conf import settings



urlpatterns = patterns('',
    (r'^$', 'map.views.listjobsTorque'),
    (r'^login$', 'map.views.login'),
    (r'^logout$', 'map.views.logout'),
    (r'^listMyjobs$', 'map.views.listMyjobs'),
    (r'^listjobsTorque$', 'map.views.listjobsTorque'),
    (r'^submitjob$', 'map.views.submitjob'),
    (r'^submitscript$', 'map.views.submitscript'),
    (r'^viewnode/(\d+)$', 'map.views.viewnode'),
    (r'^listnodes$', 'map.views.listnodes'),
    (r'^listres$', 'map.views.listres'),
    (r'^listdirsAjax/(\S+)$', 'map.views.listdirsAjax'),
    (r'^changeHost/(\w+)$', 'map.views.changeHost'),
    (r'^changeLayout/(\w+)$', 'map.views.changeLayout'),
    (r'^liststats$', 'map.views.liststats'),
    (r'^viewjob/(\S+)$', 'map.views.viewjob'),
    (r'^viewMyjob/(\d+)$', 'map.views.viewMyjob'),
    (r'^deletejob/(\S+)$', 'map.views.deletejobTorque'),
    (r'^deleteMyjob/(\d+)$', 'map.views.deleteMyjob'),
    (r'^downloaderror/(\d+)$', 'map.views.downloaderror'),
    (r'^downloadout/(\d+)$', 'map.views.downloadout'),
    (r'^downloadscript/(\d+)$', 'map.views.downloadscript'),
    (r'^viewnode/(\w+)$', 'map.views.viewnode'),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.STATIC_DOC_ROOT}),
)
