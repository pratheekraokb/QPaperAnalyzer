# Course Syllabus API Documentation

This project provides a robust API system to manage and retrieve course syllabus information efficiently. It supports multiple operations related to course syllabus management.

---

## **API Overview**

This API system includes the following endpoints:

1. [Get Topics for a Module](#1-get-topics-for-a-module)

---

## **1. Get Topics for a Module**

### **Description**
Retrieve the head and syllabus of a specific module for a given course.

- **URL**: `/api/getTopicsSyllabus/<str:CourseCode>/<int:Module>/`
- **Method**: `GET`
- **Description**: Returns the head and syllabus for the given course code and module number.

---

### **Parameters**

| Parameter    | Type    | Required | Description                          |
|--------------|---------|----------|--------------------------------------|
| `CourseCode` | String  | Yes      | Unique identifier for the course.    |
| `Module`     | Integer | Yes      | Module number (1-5).                |

---

### **Response**

#### **Success Response**

- **Status Code**: `200 OK`
- **Format**: JSON
- **Example**:

<!-- #### Example Request Body -->
<!-- ```json -->
```json
{
    "CourseCode": "CS101",
    "Module": 1,
    "SubjectName": "Programming In Python",
    "Heading": "Introduction to Python",
    "Syllabus": "The os and sys modules, NumPy - Basics, Creating arrays, Arithmetic, Slicing, Matrix Operations, Random numbers. Plotting and visualization. Matplotlib - Basic plot, Ticks, Labels, and Legends. Working with CSV files. – Pandas - Reading, Manipulating, and Processing Data. Introduction to Micro services using Flask.",
    "Topics": [
        "The os and sys modules, NumPy - Basics, Creating arrays, Arithmetic, Slicing, Matrix Operations, Random numbers",
        "Plotting and visualization",
        "Matplotlib - Basic plot, Ticks, Labels, and Legends",
        "Working with CSV files",
        "Pandas - Reading, Manipulating, and Processing Data",
        "Introduction to Micro services using Flask"
    ]
}
```

## 2. POST /api/QuestionsToTopic/ 



## **Request Format**

### **Headers**
- `Content-Type: application/json`

### **Body**
The request body should contain the following fields:

| Field         | Type   | Description                                            |
|---------------|--------|--------------------------------------------------------|
| `course_code` | String | The course code for which the questions are provided.  |
| `questions`   | Array  | A list of questions to map to topics.                  |
| `module_info` | Array  | A list of module numbers corresponding to each question. |
| `marks_info`  | Array  | A list of marks corresponding to each question.        |

#### Example Request Body
```json
{
  "course_code": "CST205",
  "questions": [
    "What is polymorphism in OOP?",
    "Explain the concept of inheritance with an example."
  ],
  "module_info": [1, 1],
  "marks_info": [5, 10]
}
```

## 3. GET /addCoursesThroughCSV/
### Add Courses Through CSV
- **URL:** `/addCoursesThroughCSV/`
- **Method:** `GET`
- **Description:** This endpoint processes a predefined CSV file containing course details and saves the courses into the database.
- **Response:** 
  - **Success:** Returns `Success` upon successful processing and saving.
  - **Error:** Logs errors in the server console if any occur during processing.

---

## CSV File Format
Save the csv file in "QPaperAnalyzerProject/dataEntry/Syllabus_Dataset.csv"
The file should be a CSV with the following structure:

| Column Name           | Description                                                        |
|-----------------------|--------------------------------------------------------------------|
| Semester              | The semester in which the course is offered (e.g., `S6`).         |
| Sl No                 | Serial number of the course in the semester.                      |
| Course_Code           | Unique code for the course (e.g., `CSL 362`).                     |
| Subject Name          | The name of the course (e.g., `Programming In Python`).           |
| Module1 Heading       | Title of the first module.                                        |
| Module1 Syllabus      | Detailed syllabus of the first module.                           |
| Module2 Heading       | Title of the second module.                                       |
| Module2 Syllabus      | Detailed syllabus of the second module.                          |
| Module3 Heading       | Title of the third module.                                        |
| Module3 Syllabus      | Detailed syllabus of the third module.                           |
| Module4 Heading       | Title of the fourth module.                                       |
| Module4 Syllabus      | Detailed syllabus of the fourth module.                          |
| Module5 Heading       | Title of the fifth module.                                        |
| Module5 Syllabus      | Detailed syllabus of the fifth module.                           |
| Module6 Heading       | Title of the sixth module (optional).                            |
| Module6 Syllabus      | Detailed syllabus of the sixth module (optional).                |

---

## Example CSV File
```csv
Semester,Sl No,Course_Code,Subject Name,Module1 Heading,Module1 Syllabus,Module2 Heading,Module2 Syllabus,Module3 Heading,Module3 Syllabus,Module4 Heading,Module4 Syllabus,Module5 Heading,Module5 Syllabus,Module6 Heading,Module6 Syllabus
S6,1,CSL 362,Programming In Python,Programming Environment and Python Basics,"Getting started with Python programming – Interactive shell, IDLE...",Building Python Programs,"Strings and text files – Accessing characters, substrings...",Graphics,"Graphics – Terminal-based programs, Simple Graphics...",Object Oriented Programming,"Design with classes - Objects and Classes...",Data Processing,"The os and sys modules, NumPy - Basics, Creating arrays...",,
```

## 4. POST /api/QPaperExcelToDB/
### QPaper Excel to Database

## **Description**
This API processes a provided Excel file containing question paper data, extracts information, and stores it in the database.

---

## **Headers**

| Header         | Value             |
|-----------------|-------------------|
| Content-Type    | `application/json` |

---

## Request Body

The request body should be in JSON format and contain the following field:

| Field      | Type   | Description                                             |
|------------|--------|---------------------------------------------------------|
| `filename` | String | The name of the Excel file to process, including the extension. |

### Example Request Body
```json
{
  "filename": "CST204_Regular_July_2021.xlsx"
}
```
### Success Response

```json
{
  "message": "File processed successfully and data stored in the database."
}

```
### Error Responses
1. 400 Bad Request: Missing or invalid input.
```json
{
  "error": "Filename is required."
}
```
2. 404 Not Found: File not found in the specified directory.
```json
{
  "error": "FileNotFoundError: [file_path] not found."
}
```
3. 400 Bad Request: Missing key in extracted JSON data.
```json
{
  "error": "KeyError: Missing key [key_name] in JSON data."
}

```

4. 500 Internal Server Error: Any other unexpected error during processing.
```json
{
  "error": "An unexpected error occurred: [error details]."
}

```

5. 405 Method Not Allowed: For HTTP methods other than POST.
```json
{
  "error": "Only POST method is allowed."
}
```
