from django.contrib import admin
from .models import Other_news, StockSymbol, CustomUser
from django.contrib.auth.admin import UserAdmin
# Register your models here.

# admin.site.register(News)

#login model
class CustomUserAdmin(UserAdmin):
    model = CustomUser # Ensure Django knows this is the user model
    
#register the custom user model
admin.site.register(CustomUser, CustomUserAdmin)

@admin.register(Other_news)
class LoginDetailAdmin(admin.ModelAdmin):
    list_display=('id','date','head','source',)
    # Exclude 'subhead' and 'body' from list_display
    # list_display = [field.name for field in News._meta.fields if field.name not in ['image_link','head','subhead', 'content']]


@admin.register(StockSymbol)
class LoginDetailAdmin(admin.ModelAdmin):
    list_display=('symbol','security_name',)

# @admin.register(News)
# class LoginDetailAdmin(admin.ModelAdmin):
#     list_display=('id','date','head','sentiment',)
#     # Exclude 'subhead' and 'body' from list_display
#     # list_display = [field.name for field in News._meta.fields if field.name not in ['image_link','head','subhead', 'content']]