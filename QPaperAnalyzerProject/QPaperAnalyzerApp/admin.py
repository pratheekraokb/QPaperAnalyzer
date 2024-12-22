from django.contrib import admin
from .models import Course

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('coursecode', 'subjectname', 'module1Head', 'module2Head', 'module3Head', 'module4Head', 'module5Head')
    search_fields = ('coursecode', 'subjectname')
    ordering = ('coursecode',)
