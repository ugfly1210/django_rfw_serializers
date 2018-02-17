from django.conf.urls import url,include
from . import views

urlpatterns = [
    url(r'^users/',views.UsersView.as_view(),name='user_view'),
    url(r'^detail/(?P<pk>\d+)/', views.UsersView.as_view(), name='detail'),
]

