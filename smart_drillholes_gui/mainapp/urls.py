from django.conf.urls import url
import views
urlpatterns = [
                url(r'^$', views.index, name='index'),
                url(r'^open/$', views.open, name='open'),
                url(r'^new/$', views.new, name='new'),
                url(r'^dashboard/$', views.dashboard, name='dashboard'),
                url(r'^add_table/$', views.add_table, name='add_table'),
]
