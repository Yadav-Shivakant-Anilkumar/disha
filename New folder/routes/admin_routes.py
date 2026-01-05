from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from auth import role_required
from database import execute_query
import bcrypt
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def hash_password(password):
    """Hash password"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    """Admin dashboard with statistics"""
    stats = {}
    
    # Get counts
    stats['total_students'] = execute_query(
        "SELECT COUNT(*) as count FROM students s JOIN users u ON s.user_id = u.user_id WHERE u.status = 'active'",
        fetch_one=True
    )['count']
    
    stats['total_teachers'] = execute_query(
        "SELECT COUNT(*) as count FROM teachers t JOIN users u ON t.user_id = u.user_id WHERE u.status = 'active'",
        fetch_one=True
    )['count']
    
    stats['total_courses'] = execute_query(
        "SELECT COUNT(*) as count FROM courses WHERE status = 'active'",
        fetch_one=True
    )['count']
    
    stats['active_batches'] = execute_query(
        "SELECT COUNT(*) as count FROM batches WHERE status = 'ongoing'",
        fetch_one=True
    )['count']
    
    stats['pending_fees'] = execute_query(
        "SELECT COALESCE(SUM(due_amount), 0) as total FROM fees WHERE payment_status IN ('pending', 'partial', 'overdue')",
        fetch_one=True
    )['total']
    
    # Recent enrollments
    recent_enrollments = execute_query(
        """SELECT e.*, s.enrollment_no, u.full_name, c.course_name, b.batch_name
           FROM enrollments e
           JOIN students s ON e.student_id = s.student_id
           JOIN users u ON s.user_id = u.user_id
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           ORDER BY e.created_at DESC LIMIT 5""",
        fetch=True
    )
    
    return render_template('admin/dashboard.html', stats=stats, recent_enrollments=recent_enrollments)

@admin_bp.route('/users')
@role_required('admin')
def manage_users():
    """Manage all users"""
    users = execute_query(
        "SELECT * FROM users ORDER BY created_at DESC",
        fetch=True
    )
    return render_template('admin/manage_users.html', users=users)

@admin_bp.route('/users/create', methods =['GET', 'POST'])
@role_required('admin')
def create_user():
    """Create new user"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Check if user exists
        existing = execute_query(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email),
            fetch_one=True
        )
        
        if existing:
            flash('Username or email already exists.', 'danger')
        else:
            password_hash = hash_password(password)
            user_id = execute_query(
                "INSERT INTO users (username, email, password_hash, role, full_name) VALUES (%s, %s, %s, %s, %s)",
                (username, email, password_hash, role, full_name),
                commit=True
            )
            
            if user_id:
                flash(f'User {username} created successfully!', 'success')
                return redirect(url_for('admin.manage_users'))
            else:
                flash('Failed to create user.', 'danger')
    
    return render_template('admin/create_user.html')

@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    """Edit user"""
    user = execute_query("SELECT * FROM users WHERE user_id = %s", (user_id,), fetch_one=True)
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.manage_users'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        status = request.form.get('status', '')
        
        execute_query(
            "UPDATE users SET full_name = %s, email = %s, status = %s WHERE user_id = %s",
            (full_name, email, status, user_id),
            commit=True
        )
        
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.manage_users'))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    """Delete user"""
    execute_query("DELETE FROM users WHERE user_id = %s", (user_id,), commit=True)
    flash('User deleted successfully!', 'success')
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/students')
@role_required('admin')
def manage_students():
    """Manage students"""
    students = execute_query(
        """SELECT s.*, u.username, u.email, u.full_name, u.status
           FROM students s
           JOIN users u ON s.user_id = u.user_id
           ORDER BY s.admission_date DESC""",
        fetch=True
    )
    return render_template('admin/manage_students.html', students=students)

@admin_bp.route('/teachers')
@role_required('admin')
def manage_teachers():
    """Manage teachers"""
    teachers = execute_query(
        """SELECT t.*, u.username, u.email, u.full_name, u.status
           FROM teachers t
           JOIN users u ON t.user_id = u.user_id
           ORDER BY t.joining_date DESC""",
        fetch=True
    )
    return render_template('admin/manage_teachers.html', teachers=teachers)

@admin_bp.route('/teachers/create', methods=['GET', 'POST'])
@role_required('admin')
def create_teacher():
    """Create new teacher"""
    if request.method == 'POST':
        # User data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Teacher data
        employee_id = request.form.get('employee_id', '').strip()
        qualification = request.form.get('qualification', '').strip()
        specialization = request.form.get('specialization', '').strip()
        experience_years = request.form.get('experience_years', 0)
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        joining_date = request.form.get('joining_date', '')
        
        # Create user first
        password_hash = hash_password(password)
        user_id = execute_query(
            "INSERT INTO users (username, email, password_hash, role, full_name) VALUES (%s, %s, %s, 'teacher', %s)",
            (username, email, password_hash, full_name),
            commit=True
        )
        
        if user_id:
            # Create teacher record
            execute_query(
                """INSERT INTO teachers (user_id, employee_id, qualification, specialization,
                   experience_years, contact, address, joining_date)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, employee_id, qualification, specialization, experience_years,
                 contact, address, joining_date),
                commit=True
            )
            flash(f'Teacher {full_name} created successfully!', 'success')
            return redirect(url_for('admin.manage_teachers'))
        else:
            flash('Failed to create teacher.', 'danger')
    
    return render_template('admin/create_teacher.html')

@admin_bp.route('/courses')
@role_required('admin')
def manage_courses():
    """Manage courses"""
    courses = execute_query("SELECT * FROM courses ORDER BY created_at DESC", fetch=True)
    return render_template('admin/manage_courses.html', courses=courses)

@admin_bp.route('/courses/create', methods=['GET', 'POST'])
@role_required('admin')
def create_course():
    """Create new course"""
    if request.method == 'POST':
        course_code = request.form.get('course_code', '').strip()
        course_name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        duration_months = request.form.get('duration_months', 0)
        fees = request.form.get('fees', 0)
        category = request.form.get('category', '').strip()
        level = request.form.get('level', 'beginner')
        
        course_id = execute_query(
            """INSERT INTO courses (course_code, course_name, description, duration_months,
               fees, category, level, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'active')""",
            (course_code, course_name, description, duration_months, fees, category, level),
            commit=True
        )
        
        if course_id:
            flash(f'Course {course_name} created successfully!', 'success')
            return redirect(url_for('admin.manage_courses'))
        else:
            flash('Failed to create course.', 'danger')
    
    return render_template('admin/create_course.html')

@admin_bp.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_course(course_id):
    """Edit course"""
    course = execute_query("SELECT * FROM courses WHERE course_id = %s", (course_id,), fetch_one=True)
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('admin.manage_courses'))
    
    if request.method == 'POST':
        course_name = request.form.get('course_name', '').strip()
        description = request.form.get('description', '').strip()
        duration_months = request.form.get('duration_months', 0)
        fees = request.form.get('fees', 0)
        category = request.form.get('category', '').strip()
        level = request.form.get('level', 'beginner')
        status = request.form.get('status', 'active')
        
        execute_query(
            """UPDATE courses SET course_name = %s, description = %s, duration_months = %s,
               fees = %s, category = %s, level = %s, status = %s
               WHERE course_id = %s""",
            (course_name, description, duration_months, fees, category, level, status, course_id),
            commit=True
        )
        
        flash('Course updated successfully!', 'success')
        return redirect(url_for('admin.manage_courses'))
    
    return render_template('admin/edit_course.html', course=course)

@admin_bp.route('/batches')
@role_required('admin')
def manage_batches():
    """Manage batches"""
    batches = execute_query(
        """SELECT b.*, c.course_name, t.employee_id, u.full_name as teacher_name
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN teachers t ON b.teacher_id = t.teacher_id
           LEFT JOIN users u ON t.user_id = u.user_id
           ORDER BY b.start_date DESC""",
        fetch=True
    )
    return render_template('admin/manage_batches.html', batches=batches)

@admin_bp.route('/batches/create', methods=['GET', 'POST'])
@role_required('admin')
def create_batch():
    """Create new batch"""
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        batch_name = request.form.get('batch_name', '').strip()
        teacher_id = request.form.get('teacher_id') or None
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date') or None
        schedule = request.form.get('schedule', '').strip()
        timing = request.form.get('timing', '').strip()
        max_students = request.form.get('max_students', 30)
        classroom = request.form.get('classroom', '').strip()
        
        batch_id = execute_query(
            """INSERT INTO batches (course_id, batch_name, teacher_id, start_date, end_date,
               schedule, timing, max_students, classroom, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'upcoming')""",
            (course_id, batch_name, teacher_id, start_date, end_date, schedule, timing,
             max_students, classroom),
            commit=True
        )
        
        if batch_id:
            flash(f'Batch {batch_name} created successfully!', 'success')
            return redirect(url_for('admin.manage_batches'))
        else:
            flash('Failed to create batch.', 'danger')
    
    # Get courses and teachers for dropdown
    courses = execute_query("SELECT * FROM courses WHERE status = 'active'", fetch=True)
    teachers = execute_query(
        """SELECT t.teacher_id, u.full_name, t.specialization
           FROM teachers t
           JOIN users u ON t.user_id = u.user_id
           WHERE u.status = 'active'""",
        fetch=True
    )
    
    return render_template('admin/create_batch.html', courses=courses, teachers=teachers)

@admin_bp.route('/reports')
@role_required('admin')
def reports():
    """View reports"""
    # Fee collection report
    fee_summary = execute_query(
        """SELECT 
               SUM(total_amount) as total_fees,
               SUM(paid_amount) as collected,
               SUM(due_amount) as pending
           FROM fees""",
        fetch_one=True
    )
    
    # Enrollment trends (last 6 months)
    enrollment_trends = execute_query(
        """SELECT 
               DATE_FORMAT(enrollment_date, '%Y-%m') as month,
               COUNT(*) as enrollments
           FROM enrollments
           WHERE enrollment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
           GROUP BY month
           ORDER BY month""",
        fetch=True
    )
    
    # Course popularity
    course_popularity = execute_query(
        """SELECT c.course_name, COUNT(e.enrollment_id) as enrollment_count
           FROM courses c
           LEFT JOIN batches b ON c.course_id = b.course_id
           LEFT JOIN enrollments e ON b.batch_id = e.batch_id
           GROUP BY c.course_id
           ORDER BY enrollment_count DESC""",
        fetch=True
    )
    
    return render_template('admin/reports.html',
                         fee_summary=fee_summary,
                         enrollment_trends=enrollment_trends,
                         course_popularity=course_popularity)
