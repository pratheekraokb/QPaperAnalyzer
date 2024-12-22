from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.shortcuts import get_object_or_404
from .models import Course

import re

class QPaperModule:
    def topicsFromSyllabus(syllabus):
        try:
            if not isinstance(syllabus, str):
                raise ValueError("Input syllabus must be a string.")

            topics = re.split(r'(?<=\.)\s*–', syllabus.replace('\n', ' '))
            cleaned_topics = []
            for topic in topics:
                sub_topics = re.split(r'\.\s+', topic)
                for sub_topic in sub_topics:
                    if sub_topic.strip():
                        cleaned_topics.append(sub_topic.strip().rstrip('.'))
            
            return cleaned_topics

        except ValueError as ve:
            print(f"ValueError: {ve}")
            return []

        except re.error as re_err:
            print(f"RegexError: {re_err}")
            return []

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return []

# API
def API_get_topics_syllabus(request, CourseCode, Module):
    CourseCode = str(CourseCode)
    Module = int(Module)
    try:
        course = get_object_or_404(Course, coursecode = CourseCode)
        module_head = getattr(course, f"module{Module}Head", None)
        module_syllabus = getattr(course, f"module{Module}Syllabus", None)
        subject_name = getattr(course, f"subjectname", None)

        topics = QPaperModule.topicsFromSyllabus(module_syllabus)

        if(module_head and module_syllabus):
            return JsonResponse({
                    "CourseCode": CourseCode,
                    "Module": Module,
                    "SubjectName": subject_name,
                    "Heading": module_head,
                    "Syllabus": module_syllabus,
                    "Topics": topics,
                    
                })
        else:
            return JsonResponse({
                "error": "Invalid Module number or no data available for this module."
            }, status=400)
    except Exception as e:
        return JsonResponse({
            "error": str(e)
        }, status=500)
    


def index(request):
    return render(request, 'students/index.html')
