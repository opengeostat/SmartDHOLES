from django.conf.urls import url
import views
urlpatterns = [
                url(r'^$', views.index, name='index'),
                url(r'^new/$', views.new, name='new'),
                url(r'^dashboard/$', views.dashboard, name='dashboard'),
                url(r'^reflector/$', views.reflector, name='reflector'),
                url(r'^reflector/(?P<table_key>\w+)/$', views.reflector, name='reflector'),
]
