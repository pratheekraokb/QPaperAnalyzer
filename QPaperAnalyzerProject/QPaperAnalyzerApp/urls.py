from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/getTopicsSyllabus/<str:CourseCode>/<int:Module>/', views.API_get_topics_syllabus, name='API_get_topics_syllabus'),
    
]
