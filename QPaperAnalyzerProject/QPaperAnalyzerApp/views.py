from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import User, Profile, College, QPaper, QPaperQuestions, Course, PrivateQPaper
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseServerError
from django.db import IntegrityError, DatabaseError

from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .models import Course, College, Quiz, QnA
from collections import defaultdict
import re
import json
import pandas as pd
from transformers import pipeline
import os

import requests, json

import difflib

# Functions for the Caching
import hashlib
from functools import lru_cache
from transformers import TFBartForSequenceClassification, BartTokenizer
import tensorflow as tf

import time

import google.generativeai as genai
from dotenv import load_dotenv

from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.db.models import Sum, Count
import random


load_dotenv()
# api_endpoint = "https://api.gemini.com/v1/question"
api_endpoint = os.getenv('api_endpoint')
api_key = os.getenv('api_key')

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
                    # print(f"Saved course: {course_code}")
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


    

    def genAIQuestionsToAnswers(api_key, question_list, mark_list):
        try:
            # Check if question_list and mark_list have the same length
            if len(question_list) != len(mark_list):
                return "Error: The question list and mark list must have the same length."
            # print(len(question_list))
            # Configure the API key
            genai.configure(api_key=api_key)

            # Initialize the model
            model = genai.GenerativeModel("gemini-1.5-flash")
            guidelines = "Write 1/2 page for 3 marks, 1 page for 8 marks, and adjust length for other marks. Use text only, no points or graphics, with simple examples."

            # Prepare the results dictionary
            results = {}

            for question, marks in zip(question_list, mark_list):
                # Check if the question exists and if AnswerText is empty
                existing_question = QPaperQuestions.objects.filter(QuestionText=question).first()

                if existing_question and existing_question.AnswerText.strip():
                    print("No Generation")
                    continue
                
                # Generate the content for the question
                query_format = f"""
                    {guidelines}
                    {question} - 3 Marks
                """
                response = model.generate_content(query_format)
                response_text = str(response.text).strip()
                # print(response_text)  # For debugging purposes, print the generated response
                
                if existing_question:
                    # Update the AnswerText field if the question exists
                    existing_question.AnswerText = response_text
                    existing_question.save()
                    print("Ans present")
                else:
                    # If the question does not exist, store the generated response
                    
                    results[question] = response_text
                    print("Answer Generated")

            return results if results else "All questions were already answered or updated."
        except Exception as e:
            print(e)
            return f"An unexpected error occurred: {e}"




    # API QPaper Excel to Database

    def handle_qpaper_creation(meta_data):
        """Handles the creation or retrieval of a QPaper record."""
        month_year = str(meta_data.get("Month_Year", ""))
        course_code = str(meta_data.get("Course_Code", ""))
        type_exam = QPaperModule.normalize_exam_type(str(meta_data.get("Type_Exam", "")))
        max_marks = int(meta_data.get("Max_Marks", ""))
        exam_name = str(meta_data.get("Exam_Name", ""))
        print(month_year, course_code, type_exam, max_marks, exam_name)
        print("hai")
        # Retrieve the Course instance based on course_code with error handling
        try:
            course_instance = Course.objects.get(coursecode=course_code)  # Assuming 'code' is the field in Course model
        except ObjectDoesNotExist:
            # Handle the case where the course code doesn't exist in the database
            raise ValueError(f"Course with code {course_code} does not exist.")
        print("done")
        # Use get_or_create with the Course instance
        qpaper, created = QPaper.objects.get_or_create(
            CourseCode=course_instance,  # Pass the Course instance here
            Exam_Type=type_exam,
            Exam_Name=exam_name,
            Month_Year=month_year,
            defaults={"Max_Marks": max_marks},
        )
        print("error")
        
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
        
        try:
            # Iterate over Part A and Part B question data
            for question_data in part_a_questions_data + part_b_questions_data:
                # Extract data, ensuring each element exists
                question = question_data[1] if len(question_data) > 1 else ""
                module = question_data[2] if len(question_data) > 2 else ""
                mark = question_data[3] if len(question_data) > 3 else 0

                # Get or create the question object
                question_obj, created = QPaperQuestions.objects.get_or_create(
                    QPaper_ID=qpaper,
                    QuestionText=str(question),
                    defaults={
                        "Mark": int(mark),
                        "Module_Number": int(module),
                    },
                )
                
                # Append relevant details to the lists
                questions_list.append(question)
                module_list.append(module)
                marks_list.append(mark)

        except IntegrityError as e:
            # This handles issues like duplicate entries due to unique constraints
            return {"error": f"Integrity error occurred: {str(e)}"}

        except ObjectDoesNotExist as e:
            # This handles cases where an object is not found when querying the database
            return {"error": f"Object does not exist: {str(e)}"}

        except ValueError as e:
            # This handles any issues with type conversions (e.g., converting to int)
            return {"error": f"Value error occurred: {str(e)}"}

        except Exception as e:
            # General exception handler for unexpected errors
            return {"error": f"An unexpected error occurred: {str(e)}"}

        return questions_list, module_list, marks_list
    
    def send_questions_to_topic_api(course_code, questions_list, module_list, marks_list):
        """Sends questions data to an external API for topic analysis."""
        url = "http://127.0.0.1:8000/api/QuestionsToTopic/"
        course_code = str(course_code)
        # print("hai")
        payload = {
            "course_code": course_code,
            "questions": questions_list,
            "module_info": module_list,
            "marks_info": marks_list,
        }
        try:
            response = requests.post(url, json=payload)
            # print("hai2")
            if response.status_code == 200:
                data = response.json()
                question_topic_list = data["result_topics"]

                # print(question_topic_list)
                if len(questions_list) == len(question_topic_list):
                    for question_text, topic in zip(questions_list, question_topic_list):
                        # Check if the question already exists in the QPaperQuestions table
                        question = QPaperQuestions.objects.filter(QuestionText=question_text).first()
                        if question:
                            question.Topic = str(topic)
                            question.save()
                            # print(question_text)
                        else:
                            print("Question not present")

                # print(len(questions_list))
                print("Data sent successfully.")
            else:
                print(f"Failed to send data. Status code: {response.status_code}")
                print("Error response:", response.text)
        except requests.RequestException as e:
            print(f"Error in sending questions to API: {e}")

    def rename_file(file_path, base_url, course_code, type_exam, month_year):
        """Renames the file to a standardized format."""
        new_filename = f"{base_url}/{course_code}_{type_exam}_{month_year}.xlsx"
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


@csrf_exempt
def API_SetUpQPaper(request):
    if request.method == "POST":
        # Parse the request body as JSON
        body = json.loads(request.body)

        # Extract values from the body with default values if not provided
        course_code = body.get("CourseCode", "")
        max_marks = int(body.get("MaxMarks", 50))
        module_required = body.get("module_required", [1,2,3,4,5])
        topics = body.get("TopicsList", [])


        # print(module_required, topics)

        if not course_code:
            return JsonResponse({"error": "Course code is required"}, status=400)

        try:
            # Start building the QPaper filter
            filter_conditions = {"CourseCode__coursecode": course_code}

            # List to store questions that match all conditions
            matching_questions = []
            total_marks = 0  # Initialize total marks to zero

            # To track added questions and avoid duplicates
            added_question_ids = set()

            # Handle the case when topics are provided
            if topics:
                # Loop through all QPapers and their questions
                qpapers = QPaper.objects.filter(**filter_conditions)

                all_questions = []
                for qpaper in qpapers:
                    questions = qpaper.questions.all()
                    all_questions.extend(questions)

                # Shuffle questions for randomness
                random.shuffle(all_questions)

                for question in all_questions:
                    # Check if the question's module is in the module_required list
                    if module_required and question.Module_Number not in module_required:
                        continue  # Skip this question if the module is not in the required list

                    # Check for topic similarity
                    topic_match = False
                    for topic in topics:
                        similarity_score = difflib.SequenceMatcher(None, question.Topic, topic).ratio()
                        if similarity_score > 0.6:  # If similarity is high enough, consider it a match
                            topic_match = True
                            break
                    if not topic_match:
                        continue  # Skip this question if no topic match

                    # Avoid adding duplicate questions
                    if question.ID not in added_question_ids:
                        if total_marks + question.Mark > max_marks:
                            # If adding this question exceeds the max marks, stop adding more questions
                            break

                        # Add the question to the matching list
                        matching_questions.append({
                            "QuestionText": question.QuestionText,
                            "Topic": question.Topic,
                            "Module_Number": question.Module_Number,
                            "Mark": question.Mark,
                        })
                        total_marks += question.Mark  # Add question's marks to the total
                        added_question_ids.add(question.ID)  # Mark this question as added
                        if total_marks >= max_marks:
                            # If the total marks reach the max marks, stop adding more questions
                            break

            # If no topics are provided, simply fetch all questions and apply module filter
            else:
                qpapers = QPaper.objects.filter(**filter_conditions)

                all_questions = []
                for qpaper in qpapers:
                    questions = qpaper.questions.all()
                    all_questions.extend(questions)

                # Shuffle questions for randomness
                random.shuffle(all_questions)

                for question in all_questions:
                    # Check if the question's module is in the module_required list
                    if module_required and question.Module_Number not in module_required:
                        continue  # Skip this question if the module is not in the required list

                    # Avoid adding duplicate questions
                    if question.ID not in added_question_ids:
                        if total_marks + question.Mark > max_marks:
                            # If adding this question exceeds the max marks, stop adding more questions
                            break

                        # Add the question to the matching list
                        question_text = str(question.QuestionText)
                        # question_text = str(re.sub(r'[^a-zA-Z0-9\s?]', '', question_text))
                        matching_questions.append({
                            "QuestionText": question_text,
                            "Topic": question.Topic,
                            "Module_Number": question.Module_Number,
                            "Mark": question.Mark,
                        })
                        total_marks += question.Mark  # Add question's marks to the total
                        added_question_ids.add(question.ID)  # Mark this question as added
                        if total_marks >= max_marks:
                            # If the total marks reach the max marks, stop adding more questions
                            break
            #  Sort the questions by marks in ascending order
            matching_questions = sorted(matching_questions, key=lambda x: x["Mark"])
            # Adjust the total marks to exactly match max_marks

            # Adjust the total marks based on the number of questions
            num_questions = len(matching_questions)
            if total_marks < max_marks:
                difference = max_marks - total_marks

                # Case 1: Number of questions >= difference (incremental distribution)
                if num_questions >= difference:
                    for question in matching_questions:
                        if difference <= 0:
                            break
                        if total_marks < max_marks:  # Ensure we don't exceed max marks
                            question["Mark"] += 1
                            total_marks += 1
                            difference -= 1

                # Case 2: Number of questions < difference (uniform increment)
                else:
                    for question in matching_questions:
                        if total_marks < max_marks:  # Ensure we don't exceed max marks
                            question["Mark"] += 1
                            total_marks += 1
            # print(matching_questions)
            # print(total_marks)
                            
            # print("Hai")
            # print(matching_questions)
            
            # for eachquest in matching_questions:
            #     topic = str(eachquest["Topic"])
            #     module = f"Module {eachquest["Module_Number"]}"
            #     mark = eachquest["Mark"]
            
            # def process_questions(matching_questions):
         
            topic_marks = defaultdict(int)  # Topic-wise marks
            module_marks = defaultdict(int)  # Module-wise marks
            module_topics = defaultdict(set)  # Topics covered per module
            mark_distribution = defaultdict(int)  # Number of questions for each mark

            for eachquest in matching_questions:
                topic = str(eachquest["Topic"])
                module = f"Module {eachquest['Module_Number']}"
                mark = eachquest["Mark"]

                # Aggregate marks per topic
                topic_marks[topic] += mark

                # Aggregate marks per module
                module_marks[module] += mark

                # Track unique topics per module
                module_topics[module].add(topic)

                # Count number of questions for each mark type
                mark_distribution[f"{mark} Marks"] += 1

            # Convert sets to list for JSON serialization
            module_topics = {module: list(topics) for module, topics in module_topics.items()}

            # Prepare response
            response_data = {
                "topic_marks": topic_marks,  # How many marks were asked for each topic
                "module_marks": module_marks,  # How many marks were asked from each module
                "module_topics": module_topics,  # How many topics were covered in each module
                "mark_distribution": mark_distribution,  # How many questions of each mark type
            }

            # return JsonResponse(response_data)
                

            return JsonResponse({
                "questions": matching_questions,
                "total_marks": total_marks,
                "response_data": response_data
                }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid HTTP method"}, status=405)

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


@csrf_exempt
def API_QPaperExcelToDB(request):
    if request.method == "POST":
        try:
            body = json.loads(request.body)
            filename = body.get("filename", "")
            if not filename:
                return JsonResponse({"error": "Filename is required."}, status=400)
            
            file_path = f"QPaperAnalyzerApp/media/Excel_Files/Temp_QPapers/{filename}"
            base_url = "QPaperAnalyzerApp/media/Excel_Files/Temp_QPapers/"

            data = QPaperModule.QPaperExcelToJSON(file_path)
            meta_data = data.get("Meta_Data", {})
            part_a_questions_data = data.get("PartA_Questions", [])
            part_b_questions_data = data.get("PartB_Questions", [])

            # Handle QPaper creation
            # print("bye")
            qpaper = QPaperModule.handle_qpaper_creation(meta_data)
            # print("hai")
            questions_list, module_list, marks_list = QPaperModule.process_questions(
                qpaper, part_a_questions_data, part_b_questions_data
            )
            QPaperModule.send_questions_to_topic_api(
                str(qpaper.CourseCode), questions_list, module_list, marks_list
            )
            try:
                QPaperModule.genAIQuestionsToAnswers(api_key=api_key, question_list=questions_list,mark_list=marks_list)
                time.sleep(0.1)
                QPaperModule.genAIQuestionsToAnswers(api_key=api_key, question_list=questions_list,mark_list=marks_list)
            except:
                print("Answer not updated")
            
            # Rename the file for proper storage
            month_year = str(meta_data.get("Month_Year", "")).replace(" ", "_")
            QPaperModule.rename_file(
                file_path, base_url, meta_data.get("Course_Code", ""), qpaper.Exam_Type, month_year
            )

            return JsonResponse({"message": "File processed successfully."}, status=200)

        except KeyError as e:
            return QPaperModule.handle_exception(f"KeyError: Missing key {e} in JSON data.", 400)
        except FileNotFoundError as e:
            return QPaperModule.handle_exception(f"FileNotFoundError: {e}", 404)
        except Exception as e:
            return QPaperModule.handle_exception(f"An unexpected error occurred: {e}", 500)
    else:
        return JsonResponse({"error": "Only POST method is allowed."}, status=405)


def API_QuestTopicAns(request, QPaperID):
    try:
        # Fetch questions for the given QPaperID
        QPaperID = int(QPaperID)
        questions = QPaperQuestions.objects.filter(QPaper_ID=QPaperID)

        # If no questions are found, raise an exception
        if not questions.exists():
            raise ObjectDoesNotExist("No questions found for the given QPaperID.")

        # Create a list to store the question data
        question_data = []
        
        for question in questions:
            # Prepare the data for each question
            data = {
                'QuestionText': question.QuestionText,
                'Mark': question.Mark,
                'Topic': question.Topic,
                'ID': question.ID,
                'ModuleNumber': question.Module_Number,
                'AnswerText': question.AnswerText if question.AnswerText else "",
            }
            question_data.append(data)

        # Return the data as a JSON response
        return JsonResponse({'questions': question_data})

    except ObjectDoesNotExist as e:
        # Handle case where no questions are found
        return JsonResponse({'error': str(e)}, status=404)

    except Exception as e:
        # Handle any other unexpected exceptions
        return JsonResponse({'error': 'An error occurred: ' + str(e)}, status=500)

def WEB_QPaperAnalysis(request, QPaper1ID):
    try:
        # Fetch the QPaper object using the provided QPaper1ID
        qpaper = QPaper.objects.get(QPaper_ID=QPaper1ID)

        # Fetch associated Course details
        course = qpaper.CourseCode

        # Fetch the questions related to the QPaper
        questions = QPaperQuestions.objects.filter(QPaper_ID=qpaper)

        if not questions.exists():
            return JsonResponse({"error": "No questions found for the provided QPaper ID."}, status=404)

        # Group by Topic and calculate the sum of marks
        topic_summary = (
            questions.values('Topic')
            .annotate(total_marks=Sum('Mark'))
            .order_by('Topic')  # Sort by Topic
        )

        # Add the module name (module head) based on the topic and syllabus
        topic_summary_with_modules = []
        for item in topic_summary:
            topic = item['Topic']
            
            def clean_string(s):
                return re.sub(r'[^A-Za-z0-9]', '', s)

            # Check if the topic is present in any module's syllabus
            cleaned_topic = clean_string(topic)  # Clean the topic string

            module_name = "Unknown"  # Default value if topic is not found in any syllabus

            # Clean each module syllabus and compare with cleaned topic
            if cleaned_topic in clean_string(course.module1Syllabus):
                module_name = f"Module 1 - {course.module1Head}"
            elif cleaned_topic in clean_string(course.module2Syllabus):
                module_name = f"Module 2 - {course.module2Head}"
            elif cleaned_topic in clean_string(course.module3Syllabus):
                module_name = f"Module 3 - {course.module3Head}"
            elif cleaned_topic in clean_string(course.module4Syllabus):
                module_name = f"Module 4 - {course.module4Head}"
            elif cleaned_topic in clean_string(course.module5Syllabus):
                module_name = f"Module 5 - {course.module5Head}"

            # Add the module name to the topic summary
            topic_summary_with_modules.append({
                "Topic": topic,
                "TotalMarks": item['total_marks'],
                "ModuleName": module_name
            })
        top_5_topics = sorted(topic_summary_with_modules, key=lambda x: x['TotalMarks'], reverse=True)[:5]

        # Mark-wise breakdown
        mark_wise_split = questions.values('Mark').annotate(question_count=Count('ID'))

        # Prepare the Mark-wise breakdown dictionary
        mark_wise_split_down = {}
        for item in mark_wise_split:
            mark = int(item['Mark'])
            count = item['question_count']
            mark_wise_split_down[f"{mark}_Marks"] = count

        # Module-wise breakdown
        module_wise_split = questions.values('Module_Number').annotate(total_marks=Sum('Mark'))

        # Prepare the Module-wise breakdown dictionary
        module_wise_split_down = {}
        for item in module_wise_split:
            module = item['Module_Number']
            total_marks = item['total_marks']
            module_wise_split_down[f"Module{module}"] = total_marks

        # Prepare the metadata for response (Course details and QPaper details)
        metadata = {
            "QPaperID": QPaper1ID,
            "CourseCode": course.coursecode,
            "ExamName": qpaper.Exam_Name,
            "MonthYear": qpaper.Month_Year,
            "SubjectName": course.subjectname,
            "MaxMarks": qpaper.Max_Marks,
            "ExamType": qpaper.Exam_Type
        }

        # Prepare the data for response
        response_data = {
            "QPaperID": QPaper1ID,
            "TopicSummary": topic_summary_with_modules,  # Add the module name to TopicSummary
            "MarkWiseSplitDown": mark_wise_split_down,
            "Top5Topics": top_5_topics,
            "ModuleWiseSplitDown": module_wise_split_down,
            "Metadata": metadata  # Add metadata to the response
        }

        # Render the result page with the response data
        return render(request, "results/qPaperAnalysis.html", response_data)

    except QPaper.DoesNotExist:
        return JsonResponse({"error": "The provided QPaper ID does not exist."}, status=400)
    
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def comparePublicQPaper(request, QPaper1ID, QPaper2ID):
    try:
        # Fetch both QPapers
        # print("hai")
        QPaper1ID = int(QPaper1ID)
        QPaper2ID = int(QPaper2ID)
        print(QPaper1ID, QPaper2ID)
        qpaper1 = QPaper.objects.get(QPaper_ID=QPaper1ID)
        qpaper2 = QPaper.objects.get(QPaper_ID=QPaper2ID)

        # Fetch courses for both QPapers
        course1 = qpaper1.CourseCode
        course2 = qpaper2.CourseCode

        # Fetch questions for both QPapers
        questions1 = QPaperQuestions.objects.filter(QPaper_ID=qpaper1)
        questions2 = QPaperQuestions.objects.filter(QPaper_ID=qpaper2)
        
        if not questions1.exists() or not questions2.exists():
            return JsonResponse({"error": "No questions found for one or both QPapers."}, status=404)

        def analyze_questions(questions, course):
            # Group by Topic and calculate the sum of marks
            topic_summary = (
                questions.values('Topic')
                .annotate(total_marks=Sum('Mark'))
                .order_by('Topic')
            )

            # Add module name (module head) based on the topic and syllabus
            topic_summary_with_modules = []
            for item in topic_summary:
                topic = item['Topic']

                def clean_string(s):
                    return re.sub(r'[^A-Za-z0-9]', '', s)

                cleaned_topic = clean_string(topic)

                # Determine the module name
                module_name = "Unknown"
                if cleaned_topic in clean_string(course.module1Syllabus):
                    module_name = f"Module 1 - {course.module1Head}"
                elif cleaned_topic in clean_string(course.module2Syllabus):
                    module_name = f"Module 2 - {course.module2Head}"
                elif cleaned_topic in clean_string(course.module3Syllabus):
                    module_name = f"Module 3 - {course.module3Head}"
                elif cleaned_topic in clean_string(course.module4Syllabus):
                    module_name = f"Module 4 - {course.module4Head}"
                elif cleaned_topic in clean_string(course.module5Syllabus):
                    module_name = f"Module 5 - {course.module5Head}"

                # Add the module info to the topic summary
                topic_summary_with_modules.append({
                    "Topic": topic,
                    "TotalMarks": item['total_marks'],
                    "ModuleName": module_name,
                })

            # Mark-wise breakdown
            mark_wise_split = questions.values('Mark').annotate(question_count=Count('ID'))
            mark_wise_split_down = {f"{item['Mark']}_Marks": item['question_count'] for item in mark_wise_split}

            # Module-wise breakdown
            module_wise_split = questions.values('Module_Number').annotate(total_marks=Sum('Mark'))
            module_wise_split_down = {f"Module{item['Module_Number']}": item['total_marks'] for item in module_wise_split}

            return {
                "TopicSummary": topic_summary_with_modules,
                "MarkWiseSplitDown": mark_wise_split_down,
                "ModuleWiseSplitDown": module_wise_split_down,
            }

        # Analyze both QPapers
        analysis1 = analyze_questions(questions1, course1)
        analysis2 = analyze_questions(questions2, course2)

        # Find common and unique questions
        questions1_set = {f"{q.QuestionText} - [{q.Mark} Marks]" for q in questions1}
        questions2_set = {f"{q.QuestionText} - [{q.Mark} Marks]" for q in questions2}

        common_questions = questions1_set & questions2_set
        unique_questions1 = questions1_set - questions2_set
        unique_questions2 = questions2_set - questions1_set


        # Find similarities and dissimilarities
        topics1 = {item['Topic'] for item in analysis1['TopicSummary']}
        topics2 = {item['Topic'] for item in analysis2['TopicSummary']}

        common_topics = topics1 & topics2
        unique_topics1 = topics1 - topics2
        unique_topics2 = topics2 - topics1

        similarities = {
            "CommonTopics": list(common_topics),
            "TotalCommonTopics": len(common_topics),
            "CommonQuestions": list(common_questions),
            "TotalCommonQuestions": len(common_questions)
        }
        print(similarities)

        dissimilarities = {
            "UniqueToQPaper1": list(unique_topics1),
            "UniqueToQPaper2": list(unique_topics2),
            "UniqueToQPaper1Questions": list(unique_questions1),
            "UniqueToQPaper2Questions": list(unique_questions2)
        }

        # Combine metadata for both QPapers
        metadata1 = {
            "QPaperID": QPaper1ID,
            "CourseCode": course1.coursecode,
            "ExamName": qpaper1.Exam_Name,
            "MonthYear": qpaper1.Month_Year,
            "SubjectName": course1.subjectname,
            "MaxMarks": qpaper1.Max_Marks,
            "ExamType": qpaper1.Exam_Type,
        }

        metadata2 = {
            "QPaperID": QPaper2ID,
            "CourseCode": course2.coursecode,
            "ExamName": qpaper2.Exam_Name,
            "MonthYear": qpaper2.Month_Year,
            "SubjectName": course2.subjectname,
            "MaxMarks": qpaper2.Max_Marks,
            "ExamType": qpaper2.Exam_Type,
        }

        # Prepare the final response
        response_data = {
            "QPaper1": {
                "Metadata": metadata1,
                "Analysis": analysis1,
            },
            "QPaper2": {
                "Metadata": metadata2,
                "Analysis": analysis2,
            },
            "Comparison": {
                "Similarities": similarities,
                "Dissimilarities": dissimilarities,
            },
        }
        print(response_data)

        # Return the comparison as JSON
        return JsonResponse(response_data)

    except QPaper.DoesNotExist:
        return JsonResponse({"error": "One or both QPapers not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
 
@csrf_exempt
def upload_file(request):
    try:
        if request.method == 'POST' and request.FILES.get('excel_file'):
            excel_file = request.FILES['excel_file']
            
            # Define the path to save the file
            upload_path = os.path.join(settings.MEDIA_ROOT, 'Excel_Files', 'Temp_QPapers')
            
            # Create the directory if it doesn't exist
            os.makedirs(upload_path, exist_ok=True)
            
            # Check if the file already exists
            file_path = os.path.join(upload_path, excel_file.name)
            if os.path.exists(file_path):
                return JsonResponse({
                    'status': 300,
                    'status_msg': 'File upload failed. A file with the same name already exists.'
                })
            
            # Save the file
            fs = FileSystemStorage(location=upload_path)
            filename = fs.save(excel_file.name, excel_file)
            
            # Get the file URL (optional)
            file_url = fs.url(filename)
            
            


            return JsonResponse({
                'status': 600,
                'status_msg': 'Successfully uploaded the file.',
                'file_url': file_url,
                'file_name': filename
            })
        
        else:
            return JsonResponse({
                'status': 300,
                'status_msg': 'No file selected or invalid request.'
            })
    
    except Exception as e:
        # Handle any unexpected exceptions
        return JsonResponse({
            'status': 500,
            'status_msg': f'An error occurred during file upload: {str(e)}'
        })
    
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

    return render(request, 'authentication/register.html', {'colleges': colleges})

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
    return render(request, 'students/student_dashboard.html', {'user': request.user})

@login_required
def faculty_dashboard(request):
    return render(request, 'faculty/faculty_dashboard.html', {'user': request.user})

def logout_user(request):
    logout(request)
    return redirect('login')

@login_required
def qPaperUpload(request):
    result = QPaper.objects.select_related('CourseCode').values(
        'QPaper_ID',
        'Exam_Type',
        'CourseCode__coursecode',  # Course Code
        'CourseCode__subjectname',  # Course Name
        'Exam_Name',
        'Month_Year',
    )
    qPaperJSON = {
    } 
    for entry in result:
        examNameUpdated = f"{entry['CourseCode__coursecode']}_{entry['CourseCode__subjectname']}_{entry['Month_Year']}_{entry['Exam_Name']}"
        qPaperJSON[f"{entry['QPaper_ID']}"] = {
            "text_to_display": str(examNameUpdated),
            "QuestionPaper_Name" : entry['Exam_Name'],
            "Course_Code" : entry['CourseCode__coursecode'],
            "Course_Name": entry['CourseCode__subjectname'],
            "Examination_Month": entry['Month_Year'],
        } 
    # print(qPaperJSON)
    return render(request, 'students/question_paper_upload.html', {'user': request.user, 'QPapers': qPaperJSON})

@login_required
def generateQPaper(request):
    try:
        qpaper_course_codes = QPaper.objects.values('CourseCode').distinct()
        privateqpaper_course_codes = PrivateQPaper.objects.values('CourseCode').distinct()
        combined_course_codes = set(code['CourseCode'] for code in qpaper_course_codes) | set(code['CourseCode'] for code in privateqpaper_course_codes)
        return render(request, "faculty/generateQpaper.html", {'course_codes': combined_course_codes})

    except Exception as e:
        # Handle errors
        return HttpResponseServerError(f"An error occurred while fetching the course codes: {str(e)}")

def API_getModuleTopicsFromCourseCode(request, CourseCode):
    try:
        # Convert the CourseCode to a string (just in case it's passed differently)
        course_code_str = str(CourseCode)

        # Fetch the course data using the CourseCode
        course = Course.objects.get(coursecode=course_code_str)



        # Create the response structure for the modules
        module_topics = {
            "1": {
                "Heading": "Module 1 - " + course.module1Head,
                "Syllabus": QPaperModule.topicsFromSyllabus(str(course.module1Syllabus))
            },
            "2": {
                "Heading": "Module 2 - " +  course.module2Head,
                "Syllabus": QPaperModule.topicsFromSyllabus(str(course.module2Syllabus))
            },
            "3": {
                "Heading": "Module 3 - " +  course.module3Head,
                "Syllabus": QPaperModule.topicsFromSyllabus(str(course.module3Syllabus))
            },
            "4": {
                "Heading": "Module 4 - " +  course.module4Head,
                "Syllabus": QPaperModule.topicsFromSyllabus(str(course.module4Syllabus))
            },
            "5": {
                "Heading": "Module 5 - " +  course.module5Head,
                "Syllabus": QPaperModule.topicsFromSyllabus(str(course.module5Syllabus))
            }
        }

        # Return the module topics as a JSON response
        return JsonResponse(module_topics)

    except Exception as e:
        # Handle errors
        return HttpResponseServerError(f"An error occurred while fetching the syllabus and module details using course codes: {str(e)}")


def compareQPapers(request, QPaper1ID, QPaper2ID):
    return render(request,"results/compareQPapers.html", {"QPaperID1": QPaper1ID, "QPaperID2": QPaper2ID })

def FacultyCompareUI(request):
    question_papers = QPaper.objects.select_related('CourseCode').all()
    formatted_data = [
        {
            "formatted_name": f"{qp.CourseCode.coursecode}_{qp.CourseCode.subjectname}_{qp.Month_Year}_{qp.Exam_Name}",
            "qpaper_id": qp.QPaper_ID
        }
        for qp in question_papers
    ]
    print(formatted_data)

    # Pass the formatted data to the template
    return render(request, "faculty/QPaperCompare.html", {"question_papers": formatted_data})


def StudentCompareUI(request):
    question_papers = QPaper.objects.select_related('CourseCode').all()
    formatted_data = [
        {
            "formatted_name": f"{qp.CourseCode.coursecode}_{qp.CourseCode.subjectname}_{qp.Month_Year}_{qp.Exam_Name}",
            "qpaper_id": qp.QPaper_ID
        }
        for qp in question_papers
    ]
    print(formatted_data)

    # Pass the formatted data to the template
    return render(request, "students/QPaperCompare.html", {"question_papers": formatted_data})

@login_required
def createQuiz(request):
    return render(request, "faculty/createQuiz.html")

@csrf_exempt
def create_quiz(request):
    if request.method == 'POST':
        data = request.POST
        quiz = Quiz.objects.create(
            quiz_title=data.get('quiz_title'),
            scheduled_date=data.get('scheduled_date'),
            max_score=data.get('max_score'),
            created_by=Profile.objects.get(user=request.user),
            course_id=Course.objects.first(),
            college_id=College.objects.first(),
        )

        questions = zip(
            request.POST.getlist('question_text'),
            request.POST.getlist('option_1'),
            request.POST.getlist('option_2'),
            request.POST.getlist('option_3'),
            request.POST.getlist('option_4'),
            request.POST.getlist('correct_option'),
            request.POST.getlist('mark')
        )

        for q_text, op1, op2, op3, op4, correct, mark in questions:
            QnA.objects.create(
                quiz=quiz,
                question_text=q_text,
                option_1=op1,
                option_2=op2,
                option_3=op3,
                option_4=op4,
                correct_option=int(correct),
                mark=int(mark)
            )

        return JsonResponse({'message': 'Quiz created successfully!', 'quiz_id': quiz.id})
    return JsonResponse({'error': 'Invalid request'}, status=400)