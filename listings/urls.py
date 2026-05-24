from django.urls import path
from . import views
from .views import index

urlpatterns = [

    path('', index, name='index'),

    path(
        'property-list',
        views.property_list,
        name='property_list'
    ),

    path(
        'create/',
        views.create_property,
        name='create_property'
    ),

    path(
        'my-properties/',
        views.my_properties,
        name='my_properties'
    ),

    path(
        'favorite/<int:property_id>/',
        views.toggle_favorite,
        name='toggle_favorite'
    ),

    path(
        'detail/<int:id>/',
        views.property_detail,
        name='detail'
    ),

    path(
        'inbox/',
        views.inbox,
        name='inbox'
    ),

    path(
        'chat/<int:user_id>/<int:property_id>/',
        views.chat_view,
        name='chat'
    ),

    path(
        'messages/',
        views.conversations,
        name='conversations'
    ),
]