from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User



class Course(models.Model):
    coursecode = models.CharField(max_length=8, unique=True, primary_key=True)  # Unique course code
    subjectname = models.CharField(max_length=200, default="")
    module1Head = models.CharField(max_length=800)
    module1Syllabus = models.TextField()  # Module 1
    module2Head = models.CharField(max_length=800)
    module2Syllabus = models.TextField()  # Module 2
    module3Head = models.CharField(max_length=800)
    module3Syllabus = models.TextField()  # Module 3
    module4Head = models.CharField(max_length=800)
    module4Syllabus = models.TextField()  # Module 4
    module5Head = models.CharField(max_length=800)
    module5Syllabus = models.TextField()  # Module 5

    def __str__(self):
        return self.coursecode 

class QPaper(models.Model):
    EXAM_TYPE_CHOICES = [
        ('Supply', 'Supply'),
        ('Regular', 'Regular'),
    ]

    QPaper_ID = models.AutoField(primary_key=True)
    CourseCode = models.ForeignKey('Course', on_delete=models.CASCADE)  # Establish a foreign key relationship
    # CourseCode = models.CharField(max_length=8)
    Max_Marks = models.IntegerField(default=100)
    Exam_Type = models.CharField(max_length=7, choices=EXAM_TYPE_CHOICES, default='Regular')
    Exam_Name = models.CharField(max_length=400)
    Month_Year = models.CharField(max_length=200, default="")

    def __str__(self):
        return f"{self.CourseCode} - {self.Exam_Name}"

class QPaperQuestions(models.Model):
    ID = models.AutoField(primary_key=True)
    QPaper_ID = models.ForeignKey(QPaper, on_delete=models.CASCADE, related_name="questions")
    QuestionText = models.TextField()
    Mark = models.IntegerField(default=1)
    Topic = models.TextField(default="")
    Module_Number = models.IntegerField(default=1)
    AnswerText = models.TextField(default="")


    def __str__(self):
        return f"Question {self.ID} for QPaper {self.QPaper_ID}"
    
class PrivateQPaper(models.Model):
    # EXAM_TYPE_CHOICES = 
    PrivateQPaper_ID = models.AutoField(primary_key=True)
    CourseCode = models.CharField(max_length = 8)
    Max_Marks = models.IntegerField(default=100)
    Exam_Name = models.CharField(max_length=400)

    def __str__(self):
        return f"{self.CourseCode} - {self.Exam_Name}"

class PrivateQPaperQuestions(models.Model):
    ID = models.AutoField(primary_key=True)
    QPaper_ID = models.ForeignKey(PrivateQPaper, on_delete=models.CASCADE, related_name="questions")
    QuestionText = models.TextField()
    Mark = models.IntegerField(default=1)
    Topic = models.TextField(default="")
    Module_Number = models.IntegerField(default=1)

    def __str__(self):
        return f"Question {self.ID} for QPaper {self.QPaper_ID}"
    


class University(models.Model):
    University_ID = models.AutoField(primary_key=True)  # Auto increment ID
    University_Name = models.CharField(max_length=255)  # Adjust max_length as per requirement
    Location = models.CharField(max_length=255)  # Adjust max_length as per requirement

    def __str__(self):
        return self.University_Name


class College(models.Model):
    CollegeID = models.AutoField(primary_key=True)  # Auto increment ID
    CollegeName = models.CharField(max_length=255)  # Adjust max_length as per requirement
    University_ID = models.ForeignKey(University, on_delete=models.CASCADE)  # FK to University
    Address = models.CharField(max_length=255)  # Adjust max_length as per requirement

    def __str__(self):
        return self.CollegeName

class Profile(models.Model):
    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=100, default="", blank = True)
    phone_num = models.CharField(max_length=15, null=True, blank=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    college = models.ForeignKey(College, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    

class Department(models.Model):
    Department_ID = models.AutoField(primary_key=True)  # Auto increment ID
    Department_Name = models.CharField(max_length=255)  # Adjust max_length as per requirement
    Department_Code = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.Department_Name

class CollegeDepartmentMap(models.Model):
    ColDepartID = models.AutoField(primary_key=True)  # Auto increment primary key
    College_ID = models.ForeignKey('College', on_delete=models.CASCADE, related_name="departments")  # FK to College
    Department_ID = models.ForeignKey('Department', on_delete=models.CASCADE, related_name="colleges")  # FK to Department

    def __str__(self):
        return f"{self.College_ID} - {self.Department_ID}"
    
class Department_Course_Map(models.Model):
    Dep_Cour_ID = models.AutoField(primary_key=True)  # Auto increment ID
    Department_ID = models.ForeignKey(Department, on_delete=models.CASCADE)  # FK to Department
    Course_ID = models.ForeignKey(Course, on_delete=models.CASCADE)  # FK to Course

    def __str__(self):
        return f"{self.Department_ID} - {self.Course_ID}"
    

class Quiz(models.Model):
    quiz_title = models.CharField(max_length=200)
    creation_timestamp = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateField()
    max_score = models.IntegerField()
    created_by = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='quizzes')
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    college_id = models.ForeignKey(College, on_delete=models.CASCADE, related_name='quizzes')
    def __str__(self):
        return self.quiz_title

class QnA(models.Model):
    quiz_qna_id = models.AutoField(primary_key=True)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_1 = models.CharField(max_length=255)
    option_2 = models.CharField(max_length=255)
    option_3 = models.CharField(max_length=255)
    option_4 = models.CharField(max_length=255)
    correct_option = models.IntegerField()  # 1, 2, 3, or 4 to match the correct option
    mark = models.IntegerField()

    def __str__(self):
        return f"Question for Quiz: {self.quiz.quiz_title}"

class QuizScore(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='quiz_scores')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='scores')
    score = models.IntegerField()

    def __str__(self):
        return f"{self.profile.user.username} - {self.quiz.quiz_title} - Score: {self.score}"