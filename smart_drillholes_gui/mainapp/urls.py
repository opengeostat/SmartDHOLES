from django.conf.urls import url
import views
urlpatterns = [
                url(r'^$', views.index, name='index'),
                url(r'^new/$', views.new, name='new'),
                url(r'^dashboard/$', views.dashboard, name='dashboard'),
]
