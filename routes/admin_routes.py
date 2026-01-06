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

@admin_bp.route('/students/create', methods=['GET', 'POST'])
@role_required('admin')
def create_student():
    """Create new student"""
    if request.method == 'POST':
        # User data
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        full_name = request.form.get('full_name', '').strip()
        
        # Student data
        enrollment_no = request.form.get('enrollment_no', '').strip()
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_contact = request.form.get('guardian_contact', '').strip()
        guardian_email = request.form.get('guardian_email', '').strip()
        admission_date = request.form.get('admission_date', '')
        
        # Check if user exists
        existing = execute_query(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email),
            fetch_one=True
        )
        
        if existing:
            flash('Username or email already exists.', 'danger')
        else:
            # Create user first
            password_hash = hash_password(password)
            user_id = execute_query(
                "INSERT INTO users (username, email, password_hash, role, full_name) VALUES (%s, %s, %s, 'student', %s)",
                (username, email, password_hash, full_name),
                commit=True
            )
            
            if user_id:
                # Create student record
                execute_query(
                    """INSERT INTO students (user_id, enrollment_no, dob, gender, contact, 
                       address, guardian_name, guardian_contact, guardian_email, admission_date)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (user_id, enrollment_no, dob if dob else None, gender, contact, 
                     address, guardian_name, guardian_contact, guardian_email, admission_date if admission_date else None),
                    commit=True
                )
                flash(f'Student {full_name} created successfully!', 'success')
                return redirect(url_for('admin.manage_students'))
            else:
                flash('Failed to create student.', 'danger')
    
    return render_template('admin/create_student.html')

@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_student(student_id):
    """Edit student"""
    student = execute_query(
        """SELECT s.*, u.username, u.email, u.full_name, u.status
           FROM students s
           JOIN users u ON s.user_id = u.user_id
           WHERE s.student_id = %s""",
        (student_id,),
        fetch_one=True
    )
    
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.manage_students'))
    
    if request.method == 'POST':
        # User data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        status = request.form.get('status', '')
        
        # Student data
        dob = request.form.get('dob', '')
        gender = request.form.get('gender', '')
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        guardian_name = request.form.get('guardian_name', '').strip()
        guardian_contact = request.form.get('guardian_contact', '').strip()
        guardian_email = request.form.get('guardian_email', '').strip()
        admission_date = request.form.get('admission_date', '')
        
        # Update user
        execute_query(
            "UPDATE users SET full_name = %s, email = %s, status = %s WHERE user_id = %s",
            (full_name, email, status, student['user_id']),
            commit=True
        )
        
        # Update student
        execute_query(
            """UPDATE students SET dob = %s, gender = %s, contact = %s, address = %s,
               guardian_name = %s, guardian_contact = %s, guardian_email = %s, admission_date = %s
               WHERE student_id = %s""",
            (dob if dob else None, gender, contact, address, guardian_name, 
             guardian_contact, guardian_email, admission_date if admission_date else None, student_id),
            commit=True
        )
        
        flash('Student updated successfully!', 'success')
        return redirect(url_for('admin.manage_students'))
    
    return render_template('admin/edit_student.html', student=student)

@admin_bp.route('/students/view/<int:student_id>')
@role_required('admin')
def view_student(student_id):
    """View student details"""
    student = execute_query(
        """SELECT s.*, u.username, u.email, u.full_name, u.status
           FROM students s
           JOIN users u ON s.user_id = u.user_id
           WHERE s.student_id = %s""",
        (student_id,),
        fetch_one=True
    )
    
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('admin.manage_students'))
    
    # Get enrollments
    enrollments = execute_query(
        """SELECT e.*, b.batch_name, c.course_name, c.course_code, b.start_date, b.end_date
           FROM enrollments e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE e.student_id = %s
           ORDER BY e.enrollment_date DESC""",
        (student_id,),
        fetch=True
    )
    
    # Get fee summary
    fees = execute_query(
        """SELECT f.*, c.course_name
           FROM fees f
           JOIN courses c ON f.course_id = c.course_id
           WHERE f.student_id = %s
           ORDER BY f.created_at DESC""",
        (student_id,),
        fetch=True
    )
    
    # Get certificates
    certificates = execute_query(
        """SELECT cert.*, c.course_name
           FROM certificates cert
           JOIN courses c ON cert.course_id = c.course_id
           WHERE cert.student_id = %s
           ORDER BY cert.issue_date DESC""",
        (student_id,),
        fetch=True
    )
    
    return render_template('admin/view_student.html', 
                         student=student, 
                         enrollments=enrollments,
                         fees=fees,
                         certificates=certificates)

@admin_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@role_required('admin')
def delete_student(student_id):
    """Delete student (soft delete by setting status to inactive)"""
    student = execute_query(
        "SELECT user_id FROM students WHERE student_id = %s",
        (student_id,),
        fetch_one=True
    )
    
    if student:
        execute_query(
            "UPDATE users SET status = 'inactive' WHERE user_id = %s",
            (student['user_id'],),
            commit=True
        )
        flash('Student deleted successfully!', 'success')
    else:
        flash('Student not found.', 'danger')
    
    return redirect(url_for('admin.manage_students'))

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

@admin_bp.route('/teachers/edit/<int:teacher_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_teacher(teacher_id):
    """Edit teacher"""
    teacher = execute_query(
        """SELECT t.*, u.username, u.email, u.full_name, u.status
           FROM teachers t
           JOIN users u ON t.user_id = u.user_id
           WHERE t.teacher_id = %s""",
        (teacher_id,),
        fetch_one=True
    )
    
    if not teacher:
        flash('Teacher not found.', 'danger')
        return redirect(url_for('admin.manage_teachers'))
    
    if request.method == 'POST':
        # User data
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        status = request.form.get('status', '')
        
        # Teacher data
        qualification = request.form.get('qualification', '').strip()
        specialization = request.form.get('specialization', '').strip()
        experience_years = request.form.get('experience_years', 0)
        contact = request.form.get('contact', '').strip()
        address = request.form.get('address', '').strip()
        joining_date = request.form.get('joining_date', '')
        
        # Update user
        execute_query(
            "UPDATE users SET full_name = %s, email = %s, status = %s WHERE user_id = %s",
            (full_name, email, status, teacher['user_id']),
            commit=True
        )
        
        # Update teacher
        execute_query(
            """UPDATE teachers SET qualification = %s, specialization = %s, 
               experience_years = %s, contact = %s, address = %s, joining_date = %s
               WHERE teacher_id = %s""",
            (qualification, specialization, experience_years, contact, 
             address, joining_date if joining_date else None, teacher_id),
            commit=True
        )
        
        flash('Teacher updated successfully!', 'success')
        return redirect(url_for('admin.manage_teachers'))
    
    return render_template('admin/edit_teacher.html', teacher=teacher)

@admin_bp.route('/teachers/view/<int:teacher_id>')
@role_required('admin')
def view_teacher(teacher_id):
    """View teacher details"""
    teacher = execute_query(
        """SELECT t.*, u.username, u.email, u.full_name, u.status
           FROM teachers t
           JOIN users u ON t.user_id = u.user_id
           WHERE t.teacher_id = %s""",
        (teacher_id,),
        fetch_one=True
    )
    
    if not teacher:
        flash('Teacher not found.', 'danger')
        return redirect(url_for('admin.manage_teachers'))
    
    # Get assigned batches
    batches = execute_query(
        """SELECT b.*, c.course_name, c.course_code
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.teacher_id = %s
           ORDER BY b.start_date DESC""",
        (teacher_id,),
        fetch=True
    )
    
    return render_template('admin/view_teacher.html', teacher=teacher, batches=batches)

@admin_bp.route('/teachers/delete/<int:teacher_id>', methods=['POST'])
@role_required('admin')
def delete_teacher(teacher_id):
    """Delete teacher (soft delete by setting status to inactive)"""
    teacher = execute_query(
        "SELECT user_id FROM teachers WHERE teacher_id = %s",
        (teacher_id,),
        fetch_one=True
    )
    
    if teacher:
        execute_query(
            "UPDATE users SET status = 'inactive' WHERE user_id = %s",
            (teacher['user_id'],),
            commit=True
        )
        flash('Teacher deleted successfully!', 'success')
    else:
        flash('Teacher not found.', 'danger')
    
    return redirect(url_for('admin.manage_teachers'))

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

@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@role_required('admin')
def delete_course(course_id):
    """Delete course (soft delete by setting status to inactive)"""
    course = execute_query(
        "SELECT * FROM courses WHERE course_id = %s",
        (course_id,),
        fetch_one=True
    )
    
    if course:
        execute_query(
            "UPDATE courses SET status = 'inactive' WHERE course_id = %s",
            (course_id,),
            commit=True
        )
        flash('Course deleted successfully!', 'success')
    else:
        flash('Course not found.', 'danger')
    
    return redirect(url_for('admin.manage_courses'))

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

@admin_bp.route('/batches/edit/<int:batch_id>', methods=['GET', 'POST'])
@role_required('admin')
def edit_batch(batch_id):
    """Edit batch"""
    batch = execute_query(
        """SELECT b.*, c.course_name
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.batch_id = %s""",
        (batch_id,),
        fetch_one=True
    )
    
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('admin.manage_batches'))
    
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
        status = request.form.get('status', 'upcoming')
        
        execute_query(
            """UPDATE batches SET course_id = %s, batch_name = %s, teacher_id = %s,
               start_date = %s, end_date = %s, schedule = %s, timing = %s,
               max_students = %s, classroom = %s, status = %s
               WHERE batch_id = %s""",
            (course_id, batch_name, teacher_id, start_date, end_date, schedule, timing,
             max_students, classroom, status, batch_id),
            commit=True
        )
        
        flash('Batch updated successfully!', 'success')
        return redirect(url_for('admin.manage_batches'))
    
    # Get courses and teachers for dropdown
    courses = execute_query("SELECT * FROM courses WHERE status = 'active'", fetch=True)
    teachers = execute_query(
        """SELECT t.teacher_id, u.full_name, t.specialization
           FROM teachers t
           JOIN users u ON t.user_id = u.user_id
           WHERE u.status = 'active'""",
        fetch=True
    )
    
    return render_template('admin/edit_batch.html', batch=batch, courses=courses, teachers=teachers)

@admin_bp.route('/batches/view/<int:batch_id>')
@role_required('admin')
def view_batch(batch_id):
    """View batch details"""
    batch = execute_query(
        """SELECT b.*, c.course_name, u.full_name as teacher_name
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN teachers t ON b.teacher_id = t.teacher_id
           LEFT JOIN users u ON t.user_id = u.user_id
           WHERE b.batch_id = %s""",
        (batch_id,),
        fetch_one=True
    )
    
    if not batch:
        flash('Batch not found.', 'danger')
        return redirect(url_for('admin.manage_batches'))
    
    # Get enrolled students
    enrollments = execute_query(
        """SELECT e.*, s.enrollment_no, u.full_name as student_name, u.email
           FROM enrollments e
           JOIN students s ON e.student_id = s.student_id
           JOIN users u ON s.user_id = u.user_id
           WHERE e.batch_id = %s
           ORDER BY e.enrollment_date DESC""",
        (batch_id,),
        fetch=True
    )
    
    return render_template('admin/view_batch.html', batch=batch, enrollments=enrollments)

@admin_bp.route('/batches/delete/<int:batch_id>', methods=['POST'])
@role_required('admin')
def delete_batch(batch_id):
    """Delete batch (soft delete by setting status to completed)"""
    batch = execute_query(
        "SELECT * FROM batches WHERE batch_id = %s",
        (batch_id,),
        fetch_one=True
    )
    
    if batch:
        execute_query(
            "UPDATE batches SET status = 'completed' WHERE batch_id = %s",
            (batch_id,),
            commit=True
        )
        flash('Batch deleted successfully!', 'success')
    else:
        flash('Batch not found.', 'danger')
    
    return redirect(url_for('admin.manage_batches'))

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
