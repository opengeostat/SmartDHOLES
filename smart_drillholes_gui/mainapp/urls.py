from django.conf.urls import url
import views
urlpatterns = [
                url(r'^$', views.index, name='index'),
                url(r'^signup/$', views.signup_user, name='signup'),
                url(r'^open/$', views.open, name='open'),
                url(r'^new/$', views.new, name='new'),
                url(r'^dashboard/$', views.dashboard, name='dashboard'),
                url(r'^reflector/$', views.reflector, name='reflector'),
                url(r'^reflector/(?P<table_key>\w+)/$', views.reflector, name='reflector'),
                url(r'^add_table/$', views.add_table, name='add_table'),

                #url(r'^add/(?P<tablename>\w+)/$', views.generic_add, name='generic_add'),

                url(r'^get_folder_content_in_json/$', views.get_folder_content_in_json, name='get_folder_content_in_json'),

]
