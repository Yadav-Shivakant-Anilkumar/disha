# Disha Computer Classes Management System

A comprehensive web-based management system for computer training institutes built with Python Flask and MySQL.

## 🎯 Features

### 👥 Four User Roles

1. **Admin** - Full system control and management
2. **Teacher** - Manage batches, attendance, exams, and materials
3. **Student** - View courses, attendance, results, pay fees
4. **Visitor** - Browse courses and register

### 📚 Core Functionality

- **Student Management**: Online registration, enrollment, profile management
- **Course Management**: Create and manage courses with different levels
- **Batch Scheduling**: Organize batches with teachers and timings
- **Attendance Tracking**: Digital attendance marking and reporting
- **Exam Management**: Create exams, enter marks, generate results
- **Certificate Generation**: Issue course completion certificates
- **Fee Management**: Online payment tracking, receipt generation
- **Learning Materials**: Upload and share course materials
- **Feedback System**: Student feedback collection and analysis

## 🛠️ Technology Stack

- **Backend**: Python 3.x, Flask Web Framework
- **Database**: MySQL (via XAMPP)
- **Frontend**: HTML5, CSS3, JavaScript
- **Authentication**: Flask Sessions with bcrypt password hashing

## 📋 Prerequisites

Before you begin, ensure you have installed:

- **Python 3.7+** - [Download Python](https://www.python.org/downloads/)
- **XAMPP** - For MySQL database (already installed as per your requirement)
- **Git** (optional) - For version control

## 🚀 Installation & Setup

### Step 1: Install Python Dependencies

Open Command Prompt in the project folder and run:

```bash
pip install -r requirements.txt
```

This will install:
- Flask
- mysql-connector-python
- bcrypt
- python-dotenv
- Werkzeug

### Step 2: Start XAMPP MySQL

1. Open XAMPP Control Panel
2. Start **Apache** and **MySQL** services
3. Click **Admin** button next to MySQL to open phpMyAdmin

### Step 3: Create Database

1. In phpMyAdmin, click on **SQL** tab
2. Copy the entire content from `database_schema.sql`
3. Paste it in the SQL query box
4. Click **Go** to execute

This will:
- Create the `disha_computer` database
- Create all 14 tables with relationships
- Insert a default admin account
- Insert sample courses

### Step 4: Verify Database Configuration

The system is pre-configured for XAMPP default settings:
- Host: `localhost`
- Port: `3306`
- Username: `root`
- Password: `` (empty)
- Database: `disha_computer`

If your XAMPP has different settings, edit `config.py`:

```python
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''  # Change if you set a password
DB_NAME = 'disha_computer'
DB_PORT = 3306
```

### Step 5: Run the Application

In the project folder, run:

```bash
python app.py
```

You should see:

```
============================================================
Disha Computer Classes Management System
============================================================
Server starting...
Access the application at: http://localhost:5000
Default admin login:
  Username: admin
  Password: admin123
============================================================
```

### Step 6: Access the System

Open your web browser and go to:
- **Homepage**: http://localhost:5000
- **Login**: http://localhost:5000/login
- **Student Registration**: http://localhost:5000/register

## 👤 Default Login Credentials

### Admin Account
- **Username**: `admin`
- **Password**: `admin123`

Use this account to:
- Create teachers
- Manage students
- Create courses and batches
- View reports
- Manage all system settings

## 📖 User Guide

### For Administrators

1. **Login** with admin credentials
2. **Dashboard** shows system statistics
3. **Manage Users**: Create/edit/delete users
4. **Manage Teachers**: Add teachers with qualifications
5. **Manage Students**: View all student records
6. **Manage Courses**: Create courses with fees and duration
7. **Manage Batches**: Schedule batches, assign teachers
8. **Reports**: View enrollment trends, fee collection, course popularity

### For Teachers

1. **Login** with assigned credentials (create via Admin panel)
2. **Dashboard** shows assigned batches
3. **Batches**: View all assigned batches and students
4. **Attendance**: Mark daily attendance for students
5. **Materials**: Upload learning resources
6. **Exams**: Create exams and enter marks

### For Students

1. **Register** online via registration form
2. **Login** with your credentials
3. **Dashboard** shows enrolled courses and fee status
4. **Enroll**: Browse and enroll in new courses
5. **Attendance**: View your attendance records
6. **Results**: Check exam results
7. **Fees**: View fee status and make payments
8. **Certificates**: Download course completion certificates
9. **Feedback**: Submit feedback about courses

### For Visitors

- **Browse** available courses
- **View** course details
- **Register** as a student
- **Contact** the institute

## 📁 Project Structure

```
project/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── database.py                 # Database utilities
├── auth.py                     # Authentication module
├── requirements.txt            # Python dependencies
├── database_schema.sql         # MySQL database schema
├── routes/
│   ├── admin_routes.py         # Admin functionality
│   ├── teacher_routes.py       # Teacher functionality
│   ├── student_routes.py       # Student functionality
│   └── visitor_routes.py       # Public pages
├── templates/
│   ├── base.html               # Base template
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   ├── admin/                  # Admin templates
│   ├── teacher/                # Teacher templates
│   ├── student/                # Student templates
│   └── visitor/                # Visitor templates
├── static/
│   ├── css/
│   │   └── style.css           # Main stylesheet
│   └── js/
│       └── main.js             # JavaScript utilities
└── uploads/                    # File uploads (auto-created)
    ├── materials/
    ├── certificates/
    └── photos/
```

## 🗄️ Database Schema

The system uses 14 interconnected tables:

1. **users** - Base user authentication
2. **students** - Student details
3. **teachers** - Teacher details
4. **courses** - Course information
5. **batches** - Batch scheduling
6. **enrollments** - Student course enrollments
7. **attendance** - Attendance records
8. **exams** - Exam details
9. **exam_results** - Student exam results
10. **certificates** - Course certificates
11. **fees** - Fee records
12. **fee_transactions** - Payment transactions
13. **learning_materials** - Course materials
14. **feedback** - Student feedback

## 🔐 Security Features

- **Password Hashing**: bcrypt for secure password storage
- **Session Management**: Flask sessions with secure cookies
- **Role-Based Access Control**: Proper authorization checks
- **SQL Injection Prevention**: Parameterized queries
- **Input Validation**: Form validation on client and server side

## 🎨 Design Features

- **Modern UI**: Clean, professional interface
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Vibrant Colors**: Educational theme with gradients
- **Interactive Elements**: Smooth animations and transitions
- **User-Friendly**: Intuitive navigation and forms

## ⚠️ Troubleshooting

### Database Connection Error

If you see "Could not connect to database":
1. Ensure XAMPP MySQL is running
2. Check database name is `disha_computer`
3. Verify credentials in `config.py`

### Import Error

If Python packages are missing:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Port Already in Use

If port 5000 is busy, edit `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port
```

### Template Not Found

Ensure all templates are in the `templates/` folder with correct subfolder structure.

## 📝 License

This project is created for educational purposes.

## 🤝 Support

For issues or questions, please check:
1. Ensure all prerequisites are installed
2. Verify database is properly set up
3. Check XAMPP services are running
4. Review error messages in the console

## 🔄 Future Enhancements

Potential features to add:
- Email notifications
- SMS alerts
- Online exam system
- Video lectures integration
- Mobile app
- Payment gateway integration
- Advanced analytics dashboard

---

**Disha Computer Classes Management System** - Empowering Education Through Technology
