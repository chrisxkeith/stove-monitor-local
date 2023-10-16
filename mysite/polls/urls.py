from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dev", views.dev, name="dev"),
    path("history", views.history, name="history"),
    path("forecast", views.forecast, name="forecast"),
]