from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('api/getTopicsSyllabus/<str:CourseCode>/<int:Module>/', views.API_get_topics_syllabus, name='API_get_topics_syllabus'),
    path('api/QuestionsToTopic/', views.API_question_to_topic, name='API_question_to_topic'),
    path('api/QPaperExcelToDB/', views.API_QPaperExcelToDB, name='API_QPaperExcelToDB'), #POST
    path('addCoursesThroughCSV/', views.dataEntryFunc, name='dataEntryFunc'),
    path('api/getQuestionsTopicsAnswer/<int:QPaperID>/', views.API_QuestTopicAns, name='API_QuestTopicAns'),
    path('upload/', views.upload_file, name='upload_file'),

    # Authentication

    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    

    # Frontend Designs
    # path('student/qPaperAnalysis/', views.qPaperAnalysis, name='qPaperAnalysis'),
    path('qPaperAnalyze/<int:QPaper1ID>/', views.WEB_QPaperAnalysis ,name='WEB_QPaperAnalysis'),
    path('student/qPaperUpload/', views.qPaperUpload, name='qPaperUpload'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    # path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),   
]
