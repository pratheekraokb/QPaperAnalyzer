from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Profile, College, QPaper, QPaperQuestions

from django.db import IntegrityError, DatabaseError

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Course, College

import re
import json
import pandas as pd
from transformers import pipeline
import os

import requests



# Functions for the Caching
import hashlib
from functools import lru_cache
from transformers import TFBartForSequenceClassification, BartTokenizer
import tensorflow as tf






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
            # print("\nProcessing each row:")
            
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

    def QPaperExcelToJSON(file_path):
        # Load the Excel file
        df = pd.read_excel(file_path)
        def retrieveMetaData():
            returnData = {}
            for index, row in df.iterrows():
                first_col = row.iloc[0]
       
                if pd.isnull(first_col):
                    continue 
             
                if first_col == "Exam Name :":
                    examName = str(row.iloc[1])
                    examName = examName.strip("")
                
                    try:
                        pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s\d{4}\b'
                        match = re.search(pattern, examName)

                        if match:
                            date_info = str(match.group(0))
                        
                        else:
                            date_info = ""
                            print("Date not found.")

                    except:
                        print("Error in extracting the month from exam name")
                    returnData["Exam_Name"] = examName
                    returnData["Month_Year"] = date_info

                elif first_col == "Course Code :":
                    returnData["Course_Code"] = str(row.iloc[1])
                elif first_col == "Course Name :":
                    returnData["Course_Name"] = str(row.iloc[1])
                elif first_col == "Max Marks :":
                    returnData["Max_Marks"] = int(row.iloc[1])
                elif first_col == "Duration :":
                    returnData["Duration"] = int(row.iloc[1])
                elif "Type" in first_col:
                    returnData["Type_Exam"] = str(row.iloc[1])
                    
                else:
                    break  # Stop processing when no matching field is found
                


            return returnData

        # Function to retrieve Part A questions
        def retrieve_partA_info():
            part_a_questions = []
            part_a_active = False

            # Iterate over rows in the dataframe
            for index, row in df.iterrows():
                first_col = row.iloc[0]  # First column value
                
                if first_col == "Part B":
                    break  # Stop if encountering an empty or "Part B" row
                
                if first_col == "Part A":
                    part_a_active = True
                    continue  # Skip the "Part A" row itself
                
                if part_a_active:
                    question_no = row.iloc[0]
                    question = row.iloc[1]
            
                    module = row.iloc[2]
                    marks = row.iloc[3]
                    if pd.notnull(question_no):
                        part_a_questions.append([question_no, question, module, marks])

            return part_a_questions[1:]

        def retrieve_partB_info():
            part_b_questions = []
            part_b_active = False

            for index, row in df.iterrows():
                first_col = row.iloc[0]  # First column value

                if first_col == "End":
                    break  # Stop if encountering "End"

                if first_col == "Part B":
                    part_b_active = True
                    continue  # Skip the "Part B" row itself

                if part_b_active:
                    question_no = row.iloc[0]
                    question = row.iloc[1]
                    module = row.iloc[2]
                    marks = row.iloc[3]
                    if pd.notnull(question_no):
                        part_b_questions.append([question_no, question, module, marks])

            return part_b_questions[1:]

        returnData = {
            "Meta_Data": retrieveMetaData(),
            "PartA_Questions": retrieve_partA_info(),
            "PartB_Questions": retrieve_partB_info()
        }
        
        return returnData


    # API QPaper Excel to Database

    def handle_qpaper_creation(meta_data):
        """Handles the creation or retrieval of a QPaper record."""
        month_year = str(meta_data.get("Month_Year", ""))
        course_code = str(meta_data.get("Course_Code", ""))
        type_exam = QPaperModule.normalize_exam_type(str(meta_data.get("Type_Exam", "")))
        max_marks = int(meta_data.get("Max_Marks", ""))
        exam_name = str(meta_data.get("Exam_Name", ""))

        qpaper, created = QPaper.objects.get_or_create(
            CourseCode=course_code,
            Exam_Type=type_exam,
            Exam_Name=exam_name,
            Month_Year=month_year,
            defaults={"Max_Marks": max_marks},
        )
        return qpaper
    
    def normalize_exam_type(type_exam):
        """Normalizes the exam type."""
        if "regular" in type_exam.lower():
            return "Regular"
        elif "supply" in type_exam.lower():
            return "Supply"
        else:
            raise ValueError("Invalid exam type provided.")
        
    def process_questions(qpaper, part_a_questions_data, part_b_questions_data):
        """Processes Part A and Part B questions."""
        questions_list, module_list, marks_list = [], [], []

        for question_data in part_a_questions_data + part_b_questions_data:
            question = question_data[1] if len(question_data) > 1 else ""
            module = question_data[2] if len(question_data) > 2 else ""
            mark = question_data[3] if len(question_data) > 3 else 0

            question_obj, _ = QPaperQuestions.objects.get_or_create(
                QPaper_ID=qpaper,
                QuestionText=str(question),
                defaults={
                    "Mark": int(mark),
                    "Module_Number": int(module),
                },
            )
            questions_list.append(question)
            module_list.append(module)
            marks_list.append(mark)

        return questions_list, module_list, marks_list
    
    def send_questions_to_topic_api(course_code, questions_list, module_list, marks_list):
        """Sends questions data to an external API for topic analysis."""
        url = "http://127.0.0.1:8000/api/QuestionsToTopic/"
        payload = {
            "course_code": course_code,
            "questions": questions_list,
            "module_info": module_list,
            "marks_info": marks_list,
        }
        try:
            response = requests.post(url, json=payload)
            if response.status_code == 200:
                print("Data sent successfully.")
            else:
                print(f"Failed to send data. Status code: {response.status_code}")
                print("Error response:", response.text)
        except requests.RequestException as e:
            print(f"Error in sending questions to API: {e}")
    def rename_file(file_path, base_url, course_code, type_exam):
        """Renames the file to a standardized format."""
        new_filename = f"{base_url}/{course_code}_{type_exam}.xlsx"
        try:
            os.rename(file_path, new_filename)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
        except FileExistsError:
            print(f"File already exists: {new_filename}")
        except Exception as e:
            print(f"Unexpected error while renaming the file: {e}")
    
    def handle_exception(error_message, status_code):
        """Handles exceptions by printing the error and returning a JSON response."""
        print(error_message)
        return JsonResponse({"status": "error", "message": error_message}, status=status_code)
    # Classifying the questions into corresponding topic from the module

    CACHE_FILE = "question_cache.json"  # File to store the cache
    cache = {}

    @staticmethod
    def load_cache():
        """
        Load the cache from the JSON file.
        """
        if os.path.exists(QPaperModule.CACHE_FILE):
            with open(QPaperModule.CACHE_FILE, "r") as file:
                QPaperModule.cache = json.load(file)
                print("Cache loaded from file.")
        else:
            QPaperModule.cache = {}

    @staticmethod
    def save_cache():
        """
        Save the cache to the JSON file.
        """
        with open(QPaperModule.CACHE_FILE, "w") as file:
            json.dump(QPaperModule.cache, file)
            print("Cache saved to file.")

    @staticmethod
    def hash_question_topics(question: str, topics: list) -> str:
        """
        Generates a unique hash key for the combination of question and topics.

        Args:
            question (str): The question to classify.
            topics (list): A list of topics.

        Returns:
            str: A unique hash key for caching.
        """
        hash_input = question + "".join(topics)
        return hashlib.md5(hash_input.encode()).hexdigest()

    @staticmethod
    def ClassifyQuestion(question: str, topics: list) -> str:
        """
        Classifies a question into one of the given topics using TFBartForSequenceClassification.

        Args:
            question (str): The question to classify.
            topics (list): A list of topics to classify the question into.

        Returns:
            str: The most likely topic for the question.
        """
        if not question or not topics:
            raise ValueError("Both 'question' and 'topics' must be provided and non-empty.")

        # Load cache on first call
        if not QPaperModule.cache:
            QPaperModule.load_cache()

        # Generate hash key for caching
        hash_key = QPaperModule.hash_question_topics(question, topics)

        # Check if the result is already cached
        if hash_key in QPaperModule.cache:
            print(f"Cache hit for question: {question}")
            return QPaperModule.cache[hash_key]

        # Load model and tokenizer
        try:
            model = TFBartForSequenceClassification.from_pretrained("./bart-large-mnli")
            tokenizer = BartTokenizer.from_pretrained("./bart-large-mnli")
        except Exception as e:
            print(f"Failed to load local model. Falling back to online model. Error: {e}")
            model = TFBartForSequenceClassification.from_pretrained("facebook/bart-large-mnli")
            tokenizer = BartTokenizer.from_pretrained("facebook/bart-large-mnli")

        # Perform classification
        try:
            scores = []
            for topic in topics:
                inputs = tokenizer(
                    f"This text is about {topic}: {question}",
                    return_tensors="tf",
                    padding=True,
                    truncation=True,
                )
                logits = model(inputs["input_ids"]).logits
                probabilities = tf.nn.softmax(logits, axis=-1).numpy()[0]
                scores.append(probabilities[1])  

            # Get the topic with the highest score
            most_likely_topic = topics[scores.index(max(scores))]

            # Cache the result
            QPaperModule.cache[hash_key] = most_likely_topic
            QPaperModule.save_cache()  
            return most_likely_topic
        except Exception as e:
            print(f"Classification failed: {e}")
            raise RuntimeError("An error occurred during classification.") from e


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
           
            course_code = str(data.get('course_code'))
            questions = data.get('questions', [])
            module_info = data.get('module_info', [])
            marks_info = data.get('marks_info', [])

            resultArray = []

            for i in range(len(questions)):
                question = questions[i]
                module = int(module_info[i])
                mark = int(marks_info[i])
                
                api_response = API_get_topics_syllabus(request, course_code, module)
                # print(api_response)
                if isinstance(api_response, JsonResponse):
                    api_response_content = api_response.content.decode('utf-8')
                    api_response = json.loads(api_response_content)
                    data = api_response["Topics"]
                topics = data
                resultTopic = QPaperModule.ClassifyQuestion(question, topics)
                resultArray.append(resultTopic)
            # print(resultArray)
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
    return redirect('login')


def API_QPaperExcelToDB(request):
    try:
        # File and path initialization
        filename = "CST204_Regular.xlsx"
        file_path = f"QPaperAnalyzerApp/media/Excel_Files/Temp_QPapers/{filename}"
        base_url = "QPaperAnalyzerApp/media/Excel_Files/Temp_QPapers/"

        data = QPaperModule.QPaperExcelToJSON(file_path)
    
        # Extract data
        meta_data = data.get("Meta_Data", {})
        part_a_questions_data = data.get("PartA_Questions", [])
        part_b_questions_data = data.get("PartB_Questions", [])

        # Handle QPaper creation
        qpaper = QPaperModule.handle_qpaper_creation(meta_data)

        # Handle questions processing
        questions_list, module_list, marks_list = QPaperModule.process_questions(qpaper, part_a_questions_data, part_b_questions_data)

        # Send data for further processing
        QPaperModule.send_questions_to_topic_api(qpaper.CourseCode, questions_list, module_list, marks_list)

        # Rename the file
        QPaperModule.rename_file(file_path, base_url, meta_data.get("Course_Code", ""), qpaper.Exam_Type)

        return JsonResponse(data, safe=True)

    except KeyError as e:
        return QPaperModule.handle_exception(f"KeyError: Missing key {e} in JSON data.", 400)
    except FileNotFoundError as e:
        return QPaperModule.handle_exception(f"FileNotFoundError: {e}", 404)
    except Exception as e:
        return QPaperModule.handle_exception(f"An unexpected error occurred: {e}", 500)

# def API_QPaperExcelToDB(request):
#     try:
#         # File and path initialization
#         filename = "CST204_Regular.xlsx"
#         file_path = f"QPaperAnalyzerApp/media/Excel_Files/Temp_QPapers/{filename}"
#         base_url = "QPaperAnalyzerApp/media/Excel_Files/Temp_QPapers/"

#         data = QPaperModule.QPaperExcelToJSON(file_path)
    
#         meta_data = data.get("Meta_Data", {})
#         part_a_questions_data = data.get("PartA_Questions", [])
#         part_b_questions_data = data.get("PartB_Questions", [])

#         # Extract values from meta_data
#         month_year = str(meta_data.get("Month_Year", ""))
#         course_code = str(meta_data.get("Course_Code", ""))
#         type_exam = str(meta_data.get("Type_Exam", ""))
#         max_marks = int(meta_data.get("Max_Marks", ""))
#         exam_name = str(meta_data.get("Exam_Name", ""))

#         # Normalize type_exam value
#         if "regular" in type_exam.lower():
#             type_exam = "Regular"
#         elif "supply" in type_exam.lower():
#             type_exam = "Supply"
#         else:
#             raise ValueError("Invalid exam type provided.")
        

#         # Add a new QPaper record only if it doesn't exist
#         qpaper, created = QPaper.objects.get_or_create(
#             CourseCode=course_code,
#             Exam_Type=type_exam,
#             Exam_Name=exam_name,
#             Month_Year=month_year,
#             defaults={
#                 "Max_Marks": max_marks,
#             }
#         )

#         # Provide feedback on the operation
#         if created:
#             print("A new QPaper record has been added.")
#         else:
#             print("The QPaper record already exists.")


#         # Initialize lists to hold question details
#         QuestionsList = []
#         ModuleList = []
#         MarksList = []

#         try:
#             qpaper = QPaper.objects.get(Exam_Name=exam_name, Month_Year=month_year)
#             qpaper_id = qpaper.QPaper_ID
#             print(f"QPaper_ID: {qpaper_id}")
#         except QPaper.DoesNotExist:
#             print("No QPaper record found for the given Exam_Name and Month_Year.")

#         # Process Part A questions
#         for questionData in part_a_questions_data:
#             question = questionData[1] if len(questionData) > 1 else ""
#             module = questionData[2] if len(questionData) > 2 else ""
#             mark = questionData[3] if len(questionData) > 3 else 0

#             # print(question, module, mark)
#             question = str(question)
#             module = int(module)
#             mark = int(mark)

#             question_obj, created = QPaperQuestions.objects.get_or_create(
#                 QPaper_ID=qpaper,
#                 QuestionText=question,
#                 defaults={
#                     "Mark": mark,
#                     "Module_Number": module,
#                 }
#             )


#             QuestionsList.append(question)
#             ModuleList.append(module)
#             MarksList.append(mark)




#         # Process Part B questions
#         for questionData in part_b_questions_data:
#             question = questionData[1] if len(questionData) > 1 else ""
#             module = questionData[2] if len(questionData) > 2 else ""
#             mark = questionData[3] if len(questionData) > 3 else 0

#             QuestionsList.append(question)
#             ModuleList.append(module)
#             MarksList.append(mark)

#             question_obj, created = QPaperQuestions.objects.get_or_create(
#                 QPaper_ID=qpaper,
#                 QuestionText=question,
#                 defaults={
#                     "Mark": mark,
#                     "Module_Number": module,
#                 }
#             )

        
#             questions = data.get('', [])
#             module_info = data.get('module_info', [])
#             marks_info = data.get('marks_info', [])
    
#         sendJSONFormat = {
#             "course_code": course_code,
#             "questions": QuestionsList,
#             "module_info": ModuleList,
#             "marks_info": MarksList
#         }
#         # SENDING POST REQUEST TO get the topic of each question
        
#         url = "http://127.0.0.1:8000/api/QuestionsToTopic/"
#         try:
#             response = requests.post(url, json=sendJSONFormat)

#             # Check the response status
#             if response.status_code == 200:
#                 print("Data sent successfully.")
#                 # print("Response:", response.json())
#             else:
#                 print(f"Failed to send data. Status code: {response.status_code}")
#                 print("Error response:", response.text)
#         except:
#             print("Error in retriveing the topic of each question")

        
#         new_filename = f"{base_url}/{course_code}_{type_exam}.xlsx"
#         try:
#             os.rename(file_path, new_filename)
#         except FileNotFoundError:
#             print(f"File not found: {file_path}")
#         except FileExistsError:
#             print(f"File already exists: {new_filename}")
#         except Exception as e:
#             print(f"Unexpected error while renaming the file: {e}")

#         return JsonResponse(data, safe=True)

#     except KeyError as e:
#         error_message = f"KeyError: Missing key {e} in JSON data."
#         print(error_message)
#         return JsonResponse({"status": "error", "message": error_message}, status=400)

#     except FileNotFoundError as e:
#         error_message = f"FileNotFoundError: {e}"
#         print(error_message)
#         return JsonResponse({"status": "error", "message": error_message}, status=404)

#     except Exception as e:
#         error_message = f"An unexpected error occurred: {e}"
#         print(error_message)
#         return JsonResponse({"status": "error", "message": error_message}, status=500)


def register(request):
    colleges = College.objects.all()
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        phone_num = request.POST.get('phone_num')
        user_type = request.POST.get('user_type')
        college_name = request.POST.get('college')
        # print("College id is ", college_id)
        if password != confirm_password:
            return render(request, 'students/register.html', {'colleges': colleges, 'error': 'Passwords do not match.'})

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            # college = College.objects.get(pk=college_name) if college_name else None
            college = College.objects.filter(CollegeName=college_name).first() if college_name else None

            # print("College Details")
            # print(college)

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
            return render(request, 'authentication/register.html', {'colleges': colleges, 'error': 'User creation failed due to integrity error. Please try again.'})
        except DatabaseError:
            return render(request, 'authentication/register.html', {'colleges': colleges, 'error': 'A database error occurred. Please try again later.'})
        except Exception as e:
            return render(request, 'authentication/register.html', {'colleges': colleges, 'error': f'An unexpected error occurred: {e}'})

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
            return render(request, 'authentication/login.html', {'error': 'Invalid credentials.'})
    return render(request, 'authentication/login.html')

@login_required
def student_dashboard(request):
    return render(request, 'student_dashboard.html', {'user': request.user})

@login_required
def faculty_dashboard(request):
    return render(request, 'faculty_dashboard.html', {'user': request.user})

def logout_user(request):
    logout(request)
    return redirect('login')
