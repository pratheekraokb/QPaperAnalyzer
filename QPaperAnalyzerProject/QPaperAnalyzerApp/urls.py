from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/getTopicsSyllabus/<str:CourseCode>/<int:Module>/', views.API_get_topics_syllabus, name='API_get_topics_syllabus'),
    path('api/QuestionsToTopic/', views.API_question_to_topic, name='API_question_to_topic'),
    path('api/QPaperExcelToDB/', views.API_QPaperExcelToDB, name='API_QPaperExcelToDB'),
    path('addCoursesThroughCSV/', views.dataEntryFunc, name='dataEntryFunc'),

    # Authentication

    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),   
]
