from django.conf.urls import url, include
import views
urlpatterns = [
                url(r'^$', views.index, name='index'),
                url(r'^desktop/$', views.desktop, name='desktop'),
                url(r'^signup/$', views.signup_user, name='signup'),
                url(r'^open/$', views.open, name='open'),
                url(r'^new/$', views.new, name='new'),
                url(r'^dashboard/$', views.dashboard, name='dashboard'),
                url(r'^reflector/$', views.reflector, name='reflector'),
                url(r'^reflector/(?P<table_key>\w+)/$', views.reflector, name='reflector'),
                url(r'^add_table/$', views.add_table, name='add_table'),
                url(r'^remove_table/$', views.remove_table, name='remove_table'),
                url(r'^verify/(?P<table_key>\w+)/$', views.verify, name='verify'),
                url(r'^add/(?P<table_key>\w+)/$', views.generic_add, name='generic_add'),
                url(r'^update/(?P<table_key>\w+)/(?P<oid>[\w\.,-]+)/$', views.generic_add, name='generic_update'),
                url(r'^get_folder_content_in_json/$', views.get_folder_content_in_json, name='get_folder_content_in_json'),
                url(r'^close_connection/$', views.close_connection, name='close_connection'),
                url(r'^get_collar_reference_tables_in_json/$', views.get_collar_reference_tables_in_json, name='get_collar_reference_tables_in_json'),
                url(r'^postgres_sqlite/$', views.postgres_to_sqlite, name='postgres_sqlite'),
                url(r'^test_json/$', views.test_json, name='test_json'),
]
