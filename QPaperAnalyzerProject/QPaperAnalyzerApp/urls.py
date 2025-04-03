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
    # path('api/getModuleTopicsFromCourseCode/<str:CourseCode>/', views.API_getModuleTopicsFromCourseCode, 'API_getModuleTopicsFromCourseCode'),
    path('api/getModuleTopicsFromCourseCode/<str:CourseCode>/', views.API_getModuleTopicsFromCourseCode, name='API_getModuleTopicsFromCourseCode'),

    path('api/setupQPaper/', views.API_SetUpQPaper, name="API_SetUpQPaper"),
    path('api/comparePublicQPaper/<int:QPaper1ID>/<int:QPaper2ID>/', views.comparePublicQPaper, name='comparePublicQPaper'),
    path('api/createQuiz/', views.create_quiz, name='create_quiz'),

    # Authentication

    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    

    # Frontend Designs
    # path('student/qPaperAnalysis/', views.qPaperAnalysis, name='qPaperAnalysis'),
    path('qPaperAnalyze/<int:QPaper1ID>/', views.WEB_QPaperAnalysis ,name='WEB_QPaperAnalysis'),
    path('student/qPaperUpload/', views.qPaperUpload, name='qPaperUpload'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/compareQPaper/', views.StudentCompareUI, name='StudentCompareUI'),
    path('qPaperAnalyze/compareQPapers/<int:QPaper1ID>/<int:QPaper2ID>/', views.compareQPapers, name='compareQPapers'),

    path('faculty/dashboard/', views.faculty_dashboard, name='faculty_dashboard'),  
    path('faculty/generateQPaper/', views.generateQPaper, name='generateQPaper'),
    path('faculty/compareQPaper/', views.FacultyCompareUI, name='FacultyCompareUI'),
    path('faculty/createQuiz/', views.createQuiz, name='createQuiz')

]
