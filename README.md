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


## **2. POST /api/QuestionsToTopic/` **

---

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

