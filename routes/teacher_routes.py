from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth import role_required
from database import execute_query
from datetime import datetime, date

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@teacher_bp.route('/dashboard')
@role_required('teacher')
def dashboard():
    """Teacher dashboard"""
    teacher_id = session.get('teacher_id')
    
    # Get teacher's batches
    batches = execute_query(
        """SELECT b.*, c.course_name, COUNT(DISTINCT e.student_id) as student_count
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN enrollments e ON b.batch_id = e.batch_id AND e.status = 'active'
           WHERE b.teacher_id = %s
           GROUP BY b.batch_id
           ORDER BY b.start_date DESC""",
        (teacher_id,),
        fetch=True
    )
    
    # Get recent attendance records
    recent_attendance = execute_query(
        """SELECT a.*, s.enrollment_no, u.full_name, c.course_name, b.batch_name
           FROM attendance a
           JOIN students s ON a.student_id = s.student_id
           JOIN users u ON s.user_id = u.user_id
           JOIN batches b ON a.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE a.marked_by = %s
           ORDER BY a.attendance_date DESC, a.created_at DESC
           LIMIT 10""",
        (session.get('user_id'),),
        fetch=True
    )
    
    stats = {
        'total_batches': len(batches),
        'active_batches': len([b for b in batches if b['status'] == 'ongoing']),
        'total_students': sum(b['student_count'] for b in batches)
    }
    
    return render_template('teacher/dashboard.html', stats=stats, batches=batches, recent_attendance=recent_attendance)

@teacher_bp.route('/batches')
@role_required('teacher')
def batches():
    """View all assigned batches"""
    teacher_id = session.get('teacher_id')
    
    batches = execute_query(
        """SELECT b.*, c.course_name, c.course_code,
               COUNT(DISTINCT e.student_id) as enrolled_students
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN enrollments e ON b.batch_id = e.batch_id AND e.status = 'active'
           WHERE b.teacher_id = %s
           GROUP BY b.batch_id
           ORDER BY b.start_date DESC""",
        (teacher_id,),
        fetch=True
    )
    
    return render_template('teacher/batches.html', batches=batches)

@teacher_bp.route('/batch/<int:batch_id>/students')
@role_required('teacher')
def batch_students(batch_id):
    """View students in a batch"""
    # Verify teacher has access to this batch
    batch = execute_query(
        """SELECT b.*, c.course_name FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.batch_id = %s AND b.teacher_id = %s""",
        (batch_id, session.get('teacher_id')),
        fetch_one=True
    )
    
    if not batch:
        flash('Batch not found or access denied.', 'danger')
        return redirect(url_for('teacher.batches'))
    
    # Get enrolled students
    students = execute_query(
        """SELECT s.student_id, s.enrollment_no, u.full_name, u.email, s.contact,
               e.enrollment_date, e.status
           FROM enrollments e
           JOIN students s ON e.student_id = s.student_id
           JOIN users u ON s.user_id = u.user_id
           WHERE e.batch_id = %s
           ORDER BY u.full_name""",
        (batch_id,),
        fetch=True
    )
    
    return render_template('teacher/batch_students.html', batch=batch, students=students)

@teacher_bp.route('/attendance', methods=['GET', 'POST'])
@role_required('teacher')
def attendance():
    """Mark attendance"""
    teacher_id = session.get('teacher_id')
    
    if request.method == 'POST':
        batch_id = request.form.get('batch_id')
        attendance_date = request.form.get('attendance_date')
        student_ids = request.form.getlist('student_ids')
        statuses = request.form.getlist('statuses')
        
        # Insert attendance records
        for i, student_id in enumerate(student_ids):
            status = statuses[i] if i < len(statuses) else 'absent'
            
            # Check if attendance already exists
            existing = execute_query(
                """SELECT attendance_id FROM attendance
                   WHERE batch_id = %s AND student_id = %s AND attendance_date = %s""",
                (batch_id, student_id, attendance_date),
                fetch_one=True
            )
            
            if existing:
                # Update existing
                execute_query(
                    """UPDATE attendance SET status = %s, marked_by = %s
                       WHERE attendance_id = %s""",
                    (status, session.get('user_id'), existing['attendance_id']),
                    commit=True
                )
            else:
                # Insert new
                execute_query(
                    """INSERT INTO attendance (batch_id, student_id, attendance_date, status, marked_by)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (batch_id, student_id, attendance_date, status, session.get('user_id')),
                    commit=True
                )
        
        flash('Attendance marked successfully!', 'success')
        return redirect(url_for('teacher.attendance'))
    
    # Get teacher's batches for dropdown
    batches = execute_query(
        """SELECT b.batch_id, b.batch_name, c.course_name
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.teacher_id = %s AND b.status IN ('upcoming', 'ongoing')
           ORDER BY b.batch_name""",
        (teacher_id,),
        fetch=True
    )
    
    # If batch selected, get students
    selected_batch = request.args.get('batch_id', type=int)
    students = []
    selected_date = request.args.get('date', date.today().isoformat())
    existing_attendance = {}
    
    if selected_batch:
        students = execute_query(
            """SELECT s.student_id, s.enrollment_no, u.full_name
               FROM enrollments e
               JOIN students s ON e.student_id = s.student_id
               JOIN users u ON s.user_id = u.user_id
               WHERE e.batch_id = %s AND e.status = 'active'
               ORDER BY u.full_name""",
            (selected_batch,),
            fetch=True
        )
        
        # Get existing attendance for the date
        attendance_records = execute_query(
            """SELECT student_id, status FROM attendance
               WHERE batch_id = %s AND attendance_date = %s""",
            (selected_batch, selected_date),
            fetch=True
        )
        
        for record in attendance_records:
            existing_attendance[record['student_id']] = record['status']
    
    return render_template('teacher/attendance.html',
                         batches=batches,
                         students=students,
                         selected_batch=selected_batch,
                         selected_date=selected_date,
                         existing_attendance=existing_attendance)

@teacher_bp.route('/materials', methods=['GET', 'POST'])
@role_required('teacher')
def materials():
    """Upload and manage learning materials"""
    teacher_id = session.get('teacher_id')
    
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        batch_id = request.form.get('batch_id') or None
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        material_type = request.form.get('material_type', 'document')
        
        # For simplicity, storing file path (in real app, handle file upload)
        file_path = request.form.get('file_path', '').strip()
        
        execute_query(
            """INSERT INTO learning_materials (course_id, batch_id, title, description,
               material_type, file_path, uploaded_by)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (course_id, batch_id, title, description, material_type, file_path, session.get('user_id')),
            commit=True
        )
        
        flash('Learning material uploaded successfully!', 'success')
        return redirect(url_for('teacher.materials'))
    
    # Get courses taught by teacher
    courses = execute_query(
        """SELECT DISTINCT c.course_id, c.course_name
           FROM courses c
           JOIN batches b ON c.course_id = b.course_id
           WHERE b.teacher_id = %s""",
        (teacher_id,),
        fetch=True
    )
    
    # Get all materials uploaded by teacher
    uploaded_materials = execute_query(
        """SELECT m.*, c.course_name, b.batch_name
           FROM learning_materials m
           JOIN courses c ON m.course_id = c.course_id
           LEFT JOIN batches b ON m.batch_id = b.batch_id
           WHERE m.uploaded_by = %s
           ORDER BY m.upload_date DESC""",
        (session.get('user_id'),),
        fetch=True
    )
    
    return render_template('teacher/materials.html', courses=courses, materials=uploaded_materials)

@teacher_bp.route('/exams', methods=['GET', 'POST'])
@role_required('teacher')
def exams():
    """Manage exams and enter marks"""
    teacher_id = session.get('teacher_id')
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'create_exam':
            batch_id = request.form.get('batch_id')
            exam_name = request.form.get('exam_name', '').strip()
            exam_type = request.form.get('exam_type', 'theory')
            exam_date = request.form.get('exam_date')
            total_marks = request.form.get('total_marks', 100)
            passing_marks = request.form.get('passing_marks', 40)
            duration_minutes = request.form.get('duration_minutes', 60)
            description = request.form.get('description', '').strip()
            
            execute_query(
                """INSERT INTO exams (batch_id, exam_name, exam_type, exam_date, total_marks,
                   passing_marks, duration_minutes, description, created_by)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (batch_id, exam_name, exam_type, exam_date, total_marks, passing_marks,
                 duration_minutes, description, session.get('user_id')),
                commit=True
            )
            
            flash('Exam created successfully!', 'success')
        
        elif action == 'enter_marks':
            exam_id = request.form.get('exam_id')
            student_ids = request.form.getlist('student_ids')
            marks_list = request.form.getlist('marks')
            
            # Get exam details for pass/fail calculation
            exam = execute_query(
                "SELECT total_marks, passing_marks FROM exams WHERE exam_id = %s",
                (exam_id,),
                fetch_one=True
            )
            
            for i, student_id in enumerate(student_ids):
                if i < len(marks_list) and marks_list[i]:
                    marks = int(marks_list[i])
                    result_status = 'pass' if marks >= exam['passing_marks'] else 'fail'
                    
                    # Calculate grade
                    percentage = (marks / exam['total_marks']) * 100
                    if percentage >= 90:
                        grade = 'A+'
                    elif percentage >= 80:
                        grade = 'A'
                    elif percentage >= 70:
                        grade = 'B+'
                    elif percentage >= 60:
                        grade = 'B'
                    elif percentage >= 50:
                        grade = 'C'
                    else:
                        grade = 'F'
                    
                    # Insert or update result
                    existing = execute_query(
                        "SELECT result_id FROM exam_results WHERE exam_id = %s AND student_id = %s",
                        (exam_id, student_id),
                        fetch_one=True
                    )
                    
                    if existing:
                        execute_query(
                            """UPDATE exam_results SET marks_obtained = %s, grade = %s,
                               result_status = %s, entered_by = %s
                               WHERE result_id = %s""",
                            (marks, grade, result_status, session.get('user_id'), existing['result_id']),
                            commit=True
                        )
                    else:
                        execute_query(
                            """INSERT INTO exam_results (exam_id, student_id, marks_obtained,
                               grade, result_status, entered_by)
                               VALUES (%s, %s, %s, %s, %s, %s)""",
                            (exam_id, student_id, marks, grade, result_status, session.get('user_id')),
                            commit=True
                        )
            
            flash('Marks entered successfully!', 'success')
        
        return redirect(url_for('teacher.exams'))
    
    # Get teacher's batches
    batches = execute_query(
        """SELECT b.batch_id, b.batch_name, c.course_name
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.teacher_id = %s
           ORDER BY b.batch_name""",
        (teacher_id,),
        fetch=True
    )
    
    # Get all exams for teacher's batches
    exams_list = execute_query(
        """SELECT e.*, b.batch_name, c.course_name
           FROM exams e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.teacher_id = %s
           ORDER BY e.exam_date DESC""",
        (teacher_id,),
        fetch=True
    )
    
    return render_template('teacher/exams.html', batches=batches, exams=exams_list)

@teacher_bp.route('/exam/<int:exam_id>/enter-marks')
@role_required('teacher')
def enter_marks(exam_id):
    """Enter marks for an exam"""
    # Get exam details
    exam = execute_query(
        """SELECT e.*, b.batch_name, c.course_name
           FROM exams e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE e.exam_id = %s""",
        (exam_id,),
        fetch_one=True
    )
    
    if not exam:
        flash('Exam not found.', 'danger')
        return redirect(url_for('teacher.exams'))
    
    # Get students and their marks
    students = execute_query(
        """SELECT s.student_id, s.enrollment_no, u.full_name,
               er.marks_obtained, er.grade, er.result_status
           FROM enrollments e
           JOIN students s ON e.student_id = s.student_id
           JOIN users u ON s.user_id = u.user_id
           LEFT JOIN exam_results er ON er.student_id = s.student_id AND er.exam_id = %s
           WHERE e.batch_id = %s AND e.status = 'active'
           ORDER BY u.full_name""",
        (exam_id, exam['batch_id']),
        fetch=True
    )
    
    return render_template('teacher/enter_marks.html', exam=exam, students=students)
