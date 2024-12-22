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
    "Head": "Introduction to Python",
    "Syllabus": "Basics of Python, variables, data types, and more."
}
