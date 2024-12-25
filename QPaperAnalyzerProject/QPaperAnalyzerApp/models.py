from django.db import models

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
        return self.coursecode  # Returning course code as string representation

class QPaper(models.Model):
    EXAM_TYPE_CHOICES = [
        ('Supply', 'Supply'),
        ('Regular', 'Regular'),
    ]

    QPaper_ID = models.AutoField(primary_key=True)
    CourseCode = models.CharField(max_length=8)
    Max_Marks = models.IntegerField(default=100)
    Exam_Type = models.CharField(max_length=7, choices=EXAM_TYPE_CHOICES, default='Regular')
    Exam_Name = models.CharField(max_length=400)

    def __str__(self):
        return f"{self.CourseCode} - {self.Exam_Name}"

class QPaperQuestions(models.Model):
    ID = models.AutoField(primary_key=True)
    QPaper_ID = models.ForeignKey(QPaper, on_delete=models.CASCADE, related_name="questions")
    QuestionText = models.TextField()
    Mark = models.IntegerField(default=1)
    Topic = models.TextField()
    Module_Number = models.IntegerField(default=1)

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
    Topic = models.TextField()
    Module_Number = models.IntegerField(default=1)

    def __str__(self):
        return f"Question {self.ID} for QPaper {self.QPaper_ID}"