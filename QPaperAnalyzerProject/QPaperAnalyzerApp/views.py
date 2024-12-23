from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Course

import re
import json
import pandas as pd

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
    
    def process_csv_rows(file_path):
        try:
            data = pd.read_csv(file_path)
            data = data.iloc[1:-1]
            print("\nProcessing each row:")
            
            for index, row in data.iterrows():
                course_code = str(row['Course_Code'])
                subject_name = str(row['Subject Name'])
                module1_heading = str(row['Module1 Heading'])
                module1_syllabus = str(row['Module1 Syllabus'])
                module2_heading = str(row['Module2 Heading'])
                module2_syllabus = str(row['Module2 Syllabus'])
                module3_heading = str(row['Module3 Heading'])
                module3_syllabus = str(row['Module3 Syllabus'])
                module4_heading = str(row['Module4 Heading'])
                module4_syllabus = str(row['Module4 Syllabus'])
                module5_heading = str(row['Module5 Heading'])
                module5_syllabus = str(row['Module5 Syllabus'])


                try:
                    course = Course(
                        coursecode=course_code,
                        subjectname=subject_name,
                        module1Head=module1_heading,
                        module1Syllabus=module1_syllabus,
                        module2Head=module2_heading,
                        module2Syllabus=module2_syllabus,
                        module3Head=module3_heading,
                        module3Syllabus=module3_syllabus,
                        module4Head=module4_heading,
                        module4Syllabus=module4_syllabus,
                        module5Head=module5_heading,
                        module5Syllabus=module5_syllabus,
                    )
                    course.save()
                    print(f"Saved course: {course_code}")
                except Exception as e:
                    print(f"Failed to save course {course_code}: {e}")

        except FileNotFoundError:
            print("Error: The specified file was not found.")
        except pd.errors.EmptyDataError:
            print("Error: The file is empty.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

def dataEntryFunc(request):
    QPaperModule.process_csv_rows("dataEntry/Syllabus_Dataset.csv")
    return HttpResponse("Sucess")


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

# POST API
@csrf_exempt
def API_question_to_topic(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            course_code = data.get('course_code')
            questions = data.get('questions', [])
            module_info = data.get('module_info', [])
            marks_info = data.get('marks_info', [])

            for i in range(len(questions)):
                question = questions[i]
                module = module_info[i]
                mark = marks_info[i]
                api_response = API_get_topics_syllabus(request, course_code, module)
                
                if isinstance(api_response, JsonResponse):
                    api_response_content = api_response.content.decode('utf-8')
                    api_response = json.loads(api_response_content)
                    data = api_response["Topics"]
                
                topics = data

                # genAI(question, topics)
            return JsonResponse({
                'status': 'success',
                'message': 'Data received successfully',
                
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

 
    
def index(request):
    return render(request, 'students/index.html')
