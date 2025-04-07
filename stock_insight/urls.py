from django.urls import path
from . import views

urlpatterns = [
    path('', views.stock_news_other, name='other_news'),
    path('news/', views.stock_news, name='news'),
    path('content/<int:news_id>/', views.news_content, name='content'),
    path('detail/', views.stock_detail, name='details'),
    path('control/', views.news_control, name='control'),
    path('edit_news/', views.edit_news, name='edit_news'),
    path('auto_process_news/', views.auto_process_news, name='auto_process_news'), #news route for auto-process
    path('auto_process_symbols/', views.auto_process_symbols, name='auto_process_symbols'), #route for Symbol auto-process
    path('review/', views.review, name='review'),
    path('contact-us/', views.contact_us, name='contact-us'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
