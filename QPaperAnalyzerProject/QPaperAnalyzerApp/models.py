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

