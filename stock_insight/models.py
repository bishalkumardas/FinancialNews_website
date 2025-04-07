from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.

#login model
class CustomUser(AbstractUser):
    #can pass more custom fields
    remember_me = models.BooleanField(default=False)
  
class Other_news(models.Model):
    date=models.DateField()
    head=models.CharField(max_length=200)
    sub_head=models.CharField(max_length=400)
    source=models.CharField(max_length=50)
    image_link=models.URLField()
    news_link=models.URLField()
    
    def __str__(self):
        return self.head
    
class StockSymbol(models.Model):
    symbol = models.CharField(max_length=20, primary_key=True) #stock symbols
    security_name= models.CharField(max_length=255) #stock name    
    
    def __str__(self):
        return f"{self.symbol} - {self.security_name}"
    
    
class News(models.Model):
    
    SENTIMENT_CHOICES= [
        ('Positive','Positive'),
        ('Negative','Negative'),
        ('Neutral','Neutral'),
    ]
    
    date=models.DateField()
    head=models.CharField(max_length=100)
    sub_head=models.CharField(max_length=200)
    image_link=models.URLField()
    content=models.TextField()
    sentiment=models.CharField(max_length=8, choices=SENTIMENT_CHOICES)
    
    def __str__(self):
        return self.head