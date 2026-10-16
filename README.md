# Attendance Management System (AMS)

A web-based Attendance Management System developed as a college mini-project. It helps manage student attendance digitally and provides separate access for Admin, Faculty, and Students.

## Features

- **Admin:** Manage users, subjects, attendance records, and reports.
- **Faculty:** View assigned students, mark attendance, and manage attendance records.
- **Students:** View personal attendance records and subject-wise attendance percentages.
- **Attendance Tracking:** Record attendance by subject and date.
- **Reports:** Generate attendance reports and identify students with attendance below 75%.
- **Authentication:** Login and logout functionality with role-based access.

## Technologies Used

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python and Flask
- **Database:** SQLite

## Project Structure

```text
Project-AMS/
├── app.py
├── config.py
├── database.py
├── models.py
├── requirements.txt
├── test_system.py
├── wsgi.py
├── attendance_system.db
├── static/
├── templates/
├── README.md
├── PROJECT_EXPLANATION.md
├── PROJECT_PROGRESS.md
└── SEPM_PROJECT_REPORT.md
```

## Installation and Setup (Windows)

Open the project folder in VS Code and open a PowerShell terminal.

### 1. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 2. Run the application

```powershell
python app.py
```

### 3. Open the application

Visit:

http://127.0.0.1:5000

## Run Tests

```powershell
python test_system.py
```

## Project Objective

To develop a web-based system that simplifies attendance recording, monitoring, percentage calculation, and report generation for Admin, Faculty, and Students.

## Project Type

Software Engineering and Project Management (SEPM) Micro-Project.
