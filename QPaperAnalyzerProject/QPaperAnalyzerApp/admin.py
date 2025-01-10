from django.contrib import admin
from .models import (
    Course,
    QPaper,
    QPaperQuestions,
    PrivateQPaper,
    PrivateQPaperQuestions,
    University,
    College,
    Department,
    Department_Course_Map,
    CollegeDepartmentMap,
    Profile,
    Quiz,
    QnA,
    QuizScore
)

# Register each model to make it manageable through the admin interface
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('coursecode', 'subjectname')
    search_fields = ('coursecode', 'subjectname')


@admin.register(QPaper)
class QPaperAdmin(admin.ModelAdmin):
    list_display = ('CourseCode', 'Exam_Name', 'Exam_Type', 'Max_Marks', 'Month_Year')
    search_fields = ('CourseCode', 'Exam_Name')
    list_filter = ('Exam_Type',)


@admin.register(QPaperQuestions)
class QPaperQuestionsAdmin(admin.ModelAdmin):
    list_display = ('QPaper_ID', 'QuestionText', 'Mark', 'Module_Number', 'Topic' ,'AnswerText')
    search_fields = ('QuestionText',)
    list_filter = ('Module_Number',)


@admin.register(PrivateQPaper)
class PrivateQPaperAdmin(admin.ModelAdmin):
    list_display = ('CourseCode', 'Exam_Name', 'Max_Marks')
    search_fields = ('CourseCode', 'Exam_Name')


@admin.register(PrivateQPaperQuestions)
class PrivateQPaperQuestionsAdmin(admin.ModelAdmin):
    list_display = ('QPaper_ID', 'QuestionText', 'Mark', 'Module_Number')
    search_fields = ('QuestionText',)
    list_filter = ('Module_Number',)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ('University_ID', 'University_Name', 'Location')
    search_fields = ('University_Name',)


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('CollegeID', 'CollegeName', 'University_ID', 'Address')
    search_fields = ('CollegeName', 'Address')
    list_filter = ('University_ID',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('Department_ID', 'Department_Name', 'Department_Code')
    search_fields = ('Department_Name',)
    list_filter = ('Department_Code',)


@admin.register(Department_Course_Map)
class DepartmentCourseMapAdmin(admin.ModelAdmin):
    list_display = ('Dep_Cour_ID', 'Department_ID', 'Course_ID')
    search_fields = ('Department_ID__Department_Name', 'Course_ID__coursecode')
    list_filter = ('Department_ID',)

@admin.register(CollegeDepartmentMap)
class CollegeDepartmentMapAdmin(admin.ModelAdmin):
    list_display = ('ColDepartID', 'College_ID', 'Department_ID')
    search_fields = ('College_ID__CollegeName', 'Department_ID__Department_Name')
    list_filter = ('College_ID', 'Department_ID')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'phone_num', 'user_type', 'college')  # Customize display in admin panel
    list_filter = ('user_type', 'college')  # Allow filtering in admin panel
    search_fields = ('user__username', 'college__CollegeName')  # Enable searching in admin panel


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('quiz_title', 'creation_timestamp', 'scheduled_date', 'max_score', 'created_by')
    list_filter = ('scheduled_date', 'max_score', 'created_by')
    search_fields = ('quiz_title', 'created_by__user__username')

# Register QnA model
@admin.register(QnA)
class QnAAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'question_text', 'correct_option', 'mark')
    list_filter = ('quiz', 'correct_option')
    search_fields = ('question_text', 'quiz__quiz_title')

# Register QuizScore model
@admin.register(QuizScore)
class QuizScoreAdmin(admin.ModelAdmin):
    list_display = ('profile', 'quiz', 'score')
    list_filter = ('quiz', 'profile')
    search_fields = ('profile__user__username', 'quiz__quiz_title')