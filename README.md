# Flask Auth & RBAC Project

A production-ready Flask application featuring user authentication, Role-Based Access Control (RBAC), and a complete admin dashboard.

---

## 🚀 Live Demo

You can view the live, deployed application here:

**[https://drun16.pythonanywhere.com/](https://drun16.pythonanywhere.com/)**



---

## Description

This project is a boilerplate Flask application that provides a solid foundation for building web applications that require user management. It includes user registration, login/logout, password hashing, and role management ('User' and 'Admin'). The admin dashboard, built with Flask-Admin, allows administrators to perform CRUD operations on users and roles.

---

## Features

* **User Authentication**: Secure user registration, login, and logout.
* **Password Hashing**: Passwords are never stored in plaintext, using Bcrypt for strong hashing.
* **Role-Based Access Control (RBAC)**: Two user roles (`User` and `Admin`) with protected routes.
* **Admin Dashboard**: A full-featured admin panel (`/admin`) for managing users and roles.
* **Database Migrations**: Uses Flask-Migrate to handle database schema changes.
* **Automated Tests**: Includes a suite of tests written with `pytest`.

---

## Technology Stack

* **Backend**: Flask
* **Database**: Flask-SQLAlchemy (defaults to SQLite, configurable for production)
* **Authentication**: Flask-Login
* **Admin Interface**: Flask-Admin
* **Password Hashing**: Flask-Bcrypt
* **Forms**: Flask-WTF
* **Database Migrations**: Flask-Migrate
* **Testing**: Pytest

---

## Deployment

This application is deployed on **PythonAnywhere**. The production environment is configured to use a **MySQL** database and is served by a production-grade WSGI server.

---

## Setup and Installation (Local)

Follow these steps to get the application running on your local machine.

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd flask_rbac_project
```

### 2. Create and Activate a Virtual Environment
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the Database
```bash
# Initialize migration history
flask db init

# Generate the initial migration
flask db migrate -m "Initial migration"

# Apply the migration to the database
flask db upgrade
```

### 5. Create Initial Roles and an Admin User
Run the flask shell to set up the necessary user roles and create your first admin user.

```bash
flask shell
```
Inside the shell, run the appropriate Python commands to create `Role` and `User` objects.

---

## Running the Application

### Local Development
To run the Flask development server on your machine:
```bash
python run.py
```
The application will be available at `http://127.0.0.1:5000`.

---

## Running Tests

To run the automated tests, execute the following command from the root directory:
```bash
pytest
```