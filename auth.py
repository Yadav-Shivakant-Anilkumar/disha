from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
import bcrypt
from database import execute_query
import re

auth_bp = Blueprint('auth', __name__)

def hash_password(password):
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login'))
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html')
        
        # Get user from database
        user = execute_query(
            "SELECT * FROM users WHERE username = %s AND status = 'active'",
            (username,),
            fetch_one=True
        )
        
        if user and verify_password(password, user['password_hash']):
            # Set session variables
            session['user_id'] = user['user_id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            session['email'] = user['email']
            
            # Get role-specific ID
            if user['role'] == 'student':
                student = execute_query(
                    "SELECT student_id FROM students WHERE user_id = %s",
                    (user['user_id'],),
                    fetch_one=True
                )
                if student:
                    session['student_id'] = student['student_id']
            elif user['role'] == 'teacher':
                teacher = execute_query(
                    "SELECT teacher_id FROM teachers WHERE user_id = %s",
                    (user['user_id'],),
                    fetch_one=True
                )
                if teacher:
                    session['teacher_id'] = teacher['teacher_id']
            
            flash(f'Welcome back, {user["full_name"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('visitor.home'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Student registration"""
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_contact = request.form.get('guardian_contact', '').strip()
        guardian_email = request.form.get('guardian_email', '').strip()
        
        # Validation
        errors = []
        
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        
        if not email or not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Please enter a valid email address.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not full_name:
            errors.append('Full name is required.')
        
        if not contact or not re.match(r'^\d{10}$', contact):
            errors.append('Please enter a valid 10-digit contact number.')
        
        # Check if username or email already exists
        existing_user = execute_query(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email),
            fetch_one=True
        )
        if existing_user:
            errors.append('Username or email already exists.')
        
        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('register.html')
        
        # Create user
        password_hash = hash_password(password)
        user_id = execute_query(
            """INSERT INTO users (username, email, password_hash, role, full_name, status)
               VALUES (%s, %s, %s, 'student', %s, 'active')""",
            (username, email, password_hash, full_name),
            commit=True
        )
        
        if user_id:
            # Generate enrollment number
            import datetime
            enrollment_no = f"DSH{datetime.datetime.now().year}{user_id:05d}"
            
            # Create student record
            execute_query(
                """INSERT INTO students (user_id, enrollment_no, dob, gender, contact, address,
                   guardian_name, guardian_contact, guardian_email, admission_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, CURDATE())""",
                (user_id, enrollment_no, dob or None, gender, contact, address,
                 guardian_name, guardian_contact, guardian_email),
                commit=True
            )
            
            flash('Registration successful! Please log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('register.html')

@auth_bp.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect to role-specific dashboard"""
    role = session.get('role')
    if role == 'admin':
        return redirect(url_for('admin.dashboard'))
    elif role == 'teacher':
        return redirect(url_for('teacher.dashboard'))
    elif role == 'student':
        return redirect(url_for('student.dashboard'))
    else:
        return redirect(url_for('visitor.home'))
