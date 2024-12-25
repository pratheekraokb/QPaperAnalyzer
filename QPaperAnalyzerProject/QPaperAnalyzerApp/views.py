from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Course, College

import re
import json
import pandas as pd
from transformers import pipeline

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

    def ClassifyQuestion(question, topics):
        try:
            classifier = pipeline("zero-shot-classification", model="./bart-large-mnli")
        except:
            classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        result = classifier(question, topics)
        return result["labels"][0]

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

            resultArray = []

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

                resultTopic = QPaperModule.ClassifyQuestion(question, topics)
                resultArray.append(resultTopic)
                print(resultTopic)

                # genAI(question, topics)
            return JsonResponse({
                'status': 'success',
                'message': 'Data received successfully',
                'result_topics': resultArray,
            }, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON format'}, status=400)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST method is allowed'}, status=405)

 
    
def index(request):
    return render(request, 'students/index.html')






from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Profile, College

from django.db import IntegrityError, DatabaseError

def register(request):
    colleges = College.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_num = request.POST.get('phone_num')
        user_type = request.POST.get('user_type')
        college_id = request.POST.get('college')

        if password != confirm_password:
            return render(request, 'students/register.html', {'colleges': colleges, 'error': 'Passwords do not match.'})

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            college = College.objects.get(pk=college_id) if college_id else None

            # Check if the profile exists
            profile, created = Profile.objects.get_or_create(user=user, defaults={
                'phone_num': phone_num,
                'user_type': user_type,
                'college': college
            })

            if not created:
                # If the profile exists, update it
                profile.phone_num = phone_num
                profile.user_type = user_type
                profile.college = college
                profile.save()

            return redirect('login')

        except IntegrityError:
            return render(request, 'students/register.html', {'colleges': colleges, 'error': 'User creation failed due to integrity error. Please try again.'})
        except DatabaseError:
            return render(request, 'students/register.html', {'colleges': colleges, 'error': 'A database error occurred. Please try again later.'})
        except Exception as e:
            return render(request, 'students/register.html', {'colleges': colleges, 'error': f'An unexpected error occurred: {e}'})

    return render(request, 'students/register.html', {'colleges': colleges})

def login_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            if user.profile.user_type == 'student':
                return redirect('student_dashboard')
            elif user.profile.user_type == 'faculty':
                return redirect('faculty_dashboard')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials.'})
    return render(request, 'students/login.html')

@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html', {'user': request.user})

@login_required
def faculty_dashboard(request):
    return render(request, 'faculty_dashboard.html', {'user': request.user})

def logout_user(request):
    logout(request)
    return redirect('login')
