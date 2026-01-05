from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from auth import role_required
from database import execute_query
from datetime import datetime

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@role_required('student')
def dashboard():
    """Student dashboard"""
    student_id = session.get('student_id')
    
    # Get enrolled courses
    enrollments = execute_query(
        """SELECT e.*, c.course_name, b.batch_name, b.start_date, b.end_date,
               b.schedule, b.timing
           FROM enrollments e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE e.student_id = %s AND e.status = 'active'
           ORDER BY e.enrollment_date DESC""",
        (student_id,),
        fetch=True
    )
    
    # Get recent attendance
    recent_attendance = execute_query(
        """SELECT a.*, b.batch_name, c.course_name
           FROM attendance a
           JOIN batches b ON a.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE a.student_id = %s
           ORDER BY a.attendance_date DESC
           LIMIT 10""",
        (student_id,),
        fetch=True
    )
    
    # Get fee status
    fee_summary = execute_query(
        """SELECT COALESCE(SUM(total_amount), 0) as total,
               COALESCE(SUM(paid_amount), 0) as paid,
               COALESCE(SUM(due_amount), 0) as due
           FROM fees
           WHERE student_id = %s""",
        (student_id,),
        fetch_one=True
    )
    
    stats = {
        'total_courses': len(enrollments),
        'total_fees': fee_summary['total'],
        'paid_amount': fee_summary['paid'],
        'due_amount': fee_summary['due']
    }
    
    return render_template('student/dashboard.html',
                         stats=stats,
                         enrollments=enrollments,
                         recent_attendance=recent_attendance)

@student_bp.route('/courses')
@role_required('student')
def courses():
    """View enrolled courses"""
    student_id = session.get('student_id')
    
    enrollments = execute_query(
        """SELECT e.*, c.course_id, c.course_name, c.description, c.duration_months,
               b.batch_name, b.start_date, b.end_date, b.schedule, b.timing,
               u.full_name as teacher_name, t.contact as teacher_contact
           FROM enrollments e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN teachers t ON b.teacher_id = t.teacher_id
           LEFT JOIN users u ON t.user_id = u.user_id
           WHERE e.student_id = %s
           ORDER BY e.enrollment_date DESC""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/courses.html', enrollments=enrollments)

@student_bp.route('/enroll', methods=['GET', 'POST'])
@role_required('student')
def enroll():
    """Enroll in a new course/batch"""
    student_id = session.get('student_id')
    
    if request.method == 'POST':
        batch_id = request.form.get('batch_id')
        
        # Check if already enrolled
        existing = execute_query(
            "SELECT enrollment_id FROM enrollments WHERE student_id = %s AND batch_id = %s",
            (student_id, batch_id),
            fetch_one=True
        )
        
        if existing:
            flash('You are already enrolled in this batch.', 'warning')
        else:
            # Get batch and course info
            batch = execute_query(
                """SELECT b.*, c.fees FROM batches b
                   JOIN courses c ON b.course_id = c.course_id
                   WHERE b.batch_id = %s""",
                (batch_id,),
                fetch_one=True
            )
            
            if batch and batch['current_students'] < batch['max_students']:
                # Create enrollment
                enrollment_id = execute_query(
                    """INSERT INTO enrollments (student_id, batch_id, enrollment_date, status)
                       VALUES (%s, %s, CURDATE(), 'active')""",
                    (student_id, batch_id),
                    commit=True
                )
                
                if enrollment_id:
                    # Update batch student count
                    execute_query(
                        "UPDATE batches SET current_students = current_students + 1 WHERE batch_id = %s",
                        (batch_id,),
                        commit=True
                    )
                    
                    # Create fee record
                    execute_query(
                        """INSERT INTO fees (student_id, course_id, total_amount, due_amount, payment_status)
                           VALUES (%s, %s, %s, %s, 'pending')""",
                        (student_id, batch['course_id'], batch['fees'], batch['fees']),
                        commit=True
                    )
                    
                    flash('Successfully enrolled in the course!', 'success')
                    return redirect(url_for('student.courses'))
            else:
                flash('Batch is full or not available.', 'danger')
    
    # Get available batches
    available_batches = execute_query(
        """SELECT b.*, c.course_name, c.description, c.fees, c.duration_months,
               (b.max_students - b.current_students) as available_seats,
               u.full_name as teacher_name
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN teachers t ON b.teacher_id = t.teacher_id
           LEFT JOIN users u ON t.user_id = u.user_id
           WHERE b.status IN ('upcoming', 'ongoing')
               AND b.current_students < b.max_students
               AND NOT EXISTS (
                   SELECT 1 FROM enrollments e
                   WHERE e.student_id = %s AND e.batch_id = b.batch_id
               )
           ORDER BY b.start_date""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/enroll.html', batches=available_batches)

@student_bp.route('/materials')
@role_required('student')
def materials():
    """Access learning materials"""
    student_id = session.get('student_id')
    
    # Get materials for enrolled courses
    materials = execute_query(
        """SELECT DISTINCT m.*, c.course_name, b.batch_name
           FROM learning_materials m
           JOIN courses c ON m.course_id = c.course_id
           LEFT JOIN batches b ON m.batch_id = b.batch_id
           JOIN enrollments e ON (e.batch_id = m.batch_id OR (m.batch_id IS NULL AND e.batch_id IN (
               SELECT batch_id FROM batches WHERE course_id = m.course_id
           )))
           WHERE e.student_id = %s AND e.status = 'active' AND m.is_active = TRUE
           ORDER BY m.upload_date DESC""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/materials.html', materials=materials)

@student_bp.route('/attendance')
@role_required('student')
def attendance():
    """View attendance records"""
    student_id = session.get('student_id')
    
    # Get attendance by batch
    attendance_data = execute_query(
        """SELECT b.batch_id, b.batch_name, c.course_name,
               COUNT(a.attendance_id) as total_classes,
               SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_count,
               SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_count,
               SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_count,
               ROUND(SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) * 100.0 / COUNT(a.attendance_id), 2) as attendance_percentage
           FROM enrollments e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           LEFT JOIN attendance a ON a.batch_id = b.batch_id AND a.student_id = e.student_id
           WHERE e.student_id = %s AND e.status = 'active'
           GROUP BY b.batch_id
           ORDER BY b.batch_name""",
        (student_id,),
        fetch=True
    )
    
    # Get recent attendance records
    recent_records = execute_query(
        """SELECT a.*, b.batch_name, c.course_name
           FROM attendance a
           JOIN batches b ON a.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE a.student_id = %s
           ORDER BY a.attendance_date DESC
           LIMIT 20""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/attendance.html',
                         attendance_data=attendance_data,
                         recent_records=recent_records)

@student_bp.route('/results')
@role_required('student')
def results():
    """View exam results"""
    student_id = session.get('student_id')
    
    # Get all exam results
    exam_results = execute_query(
        """SELECT er.*, e.exam_name, e.exam_type, e.exam_date, e.total_marks,
               b.batch_name, c.course_name
           FROM exam_results er
           JOIN exams e ON er.exam_id = e.exam_id
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE er.student_id = %s
           ORDER BY e.exam_date DESC""",
        (student_id,),
        fetch=True
    )
    
    # Calculate average performance
    if exam_results:
        total_percentage = sum((r['marks_obtained'] / r['total_marks']) * 100 for r in exam_results)
        avg_percentage = total_percentage / len(exam_results)
    else:
        avg_percentage = 0
    
    return render_template('student/results.html',
                         exam_results=exam_results,
                         avg_percentage=avg_percentage)

@student_bp.route('/certificates')
@role_required('student')
def certificates():
    """View and download certificates"""
    student_id = session.get('student_id')
    
    certificates = execute_query(
        """SELECT c.*, co.course_name, co.course_code, u.full_name as issued_by_name
           FROM certificates c
           JOIN courses co ON c.course_id = co.course_id
           JOIN users u ON c.issued_by = u.user_id
           WHERE c.student_id = %s
           ORDER BY c.issue_date DESC""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/certificates.html', certificates=certificates)

@student_bp.route('/fees')
@role_required('student')
def fees():
    """View fee status and payment history"""
    student_id = session.get('student_id')
    
    # Get fee details
    fee_records = execute_query(
        """SELECT f.*, c.course_name, c.course_code
           FROM fees f
           JOIN courses c ON f.course_id = c.course_id
           WHERE f.student_id = %s
           ORDER BY f.created_at DESC""",
        (student_id,),
        fetch=True
    )
    
    # Get payment transactions
    transactions = execute_query(
        """SELECT ft.*, c.course_name
           FROM fee_transactions ft
           JOIN fees f ON ft.fee_id = f.fee_id
           JOIN courses c ON f.course_id = c.course_id
           WHERE f.student_id = %s
           ORDER BY ft.payment_date DESC""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/fees.html',
                         fee_records=fee_records,
                         transactions=transactions)

@student_bp.route('/fees/pay/<int:fee_id>', methods=['GET', 'POST'])
@role_required('student')
def pay_fee(fee_id):
    """Make fee payment"""
    student_id = session.get('student_id')
    
    # Verify fee belongs to student
    fee = execute_query(
        """SELECT f.*, c.course_name FROM fees f
           JOIN courses c ON f.course_id = c.course_id
           WHERE f.fee_id = %s AND f.student_id = %s""",
        (fee_id, student_id),
        fetch_one=True
    )
    
    if not fee:
        flash('Fee record not found.', 'danger')
        return redirect(url_for('student.fees'))
    
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        payment_method = request.form.get('payment_method', 'cash')
        transaction_ref = request.form.get('transaction_ref', '').strip()
        
        if amount > 0 and amount <= fee['due_amount']:
            # Generate receipt number
            import random
            receipt_no = f"RCP{datetime.now().year}{random.randint(10000, 99999)}"
            
            # Record transaction
            execute_query(
                """INSERT INTO fee_transactions (fee_id, amount, payment_date, payment_method,
                   transaction_ref, receipt_no, received_by)
                   VALUES (%s, %s, CURDATE(), %s, %s, %s, %s)""",
                (fee_id, amount, payment_method, transaction_ref or None, receipt_no, session.get('user_id')),
                commit=True
            )
            
            # Update fee record
            new_paid = fee['paid_amount'] + amount
            new_due = fee['total_amount'] - new_paid
            new_status = 'paid' if new_due == 0 else 'partial'
            
            execute_query(
                """UPDATE fees SET paid_amount = %s, due_amount = %s,
                   payment_status = %s WHERE fee_id = %s""",
                (new_paid, new_due, new_status, fee_id),
                commit=True
            )
            
            flash(f'Payment of ₹{amount} recorded successfully! Receipt No: {receipt_no}', 'success')
            return redirect(url_for('student.fees'))
        else:
            flash('Invalid payment amount.', 'danger')
    
    return render_template('student/pay_fee.html', fee=fee)

@student_bp.route('/feedback', methods=['GET', 'POST'])
@role_required('student')
def feedback():
    """Submit feedback"""
    student_id = session.get('student_id')
    
    if request.method == 'POST':
        course_id = request.form.get('course_id') or None
        teacher_id = request.form.get('teacher_id') or None
        rating = request.form.get('rating', 0)
        category = request.form.get('category', 'overall')
        comments = request.form.get('comments', '').strip()
        is_anonymous = request.form.get('is_anonymous') == 'on'
        
        execute_query(
            """INSERT INTO feedback (student_id, course_id, teacher_id, rating,
               category, comments, is_anonymous)
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            (student_id, course_id, teacher_id, rating, category, comments, is_anonymous),
            commit=True
        )
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('student.feedback'))
    
    # Get enrolled courses for dropdown
    enrolled_courses = execute_query(
        """SELECT DISTINCT c.course_id, c.course_name
           FROM enrollments e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN courses c ON b.course_id = c.course_id
           WHERE e.student_id = %s AND e.status = 'active'""",
        (student_id,),
        fetch=True
    )
    
    # Get teachers for enrolled courses
    teachers = execute_query(
        """SELECT DISTINCT t.teacher_id, u.full_name
           FROM enrollments e
           JOIN batches b ON e.batch_id = b.batch_id
           JOIN teachers t ON b.teacher_id = t.teacher_id
           JOIN users u ON t.user_id = u.user_id
           WHERE e.student_id = %s AND e.status = 'active'""",
        (student_id,),
        fetch=True
    )
    
    # Get submitted feedback
    submitted_feedback = execute_query(
        """SELECT f.*, c.course_name, u.full_name as teacher_name
           FROM feedback f
           LEFT JOIN courses c ON f.course_id = c.course_id
           LEFT JOIN teachers t ON f.teacher_id = t.teacher_id
           LEFT JOIN users u ON t.user_id = u.user_id
           WHERE f.student_id = %s
           ORDER BY f.feedback_date DESC""",
        (student_id,),
        fetch=True
    )
    
    return render_template('student/feedback.html',
                         enrolled_courses=enrolled_courses,
                         teachers=teachers,
                         submitted_feedback=submitted_feedback)

@student_bp.route('/profile')
@role_required('student')
def profile():
    """View and edit profile"""
    student_id = session.get('student_id')
    
    student_info = execute_query(
        """SELECT s.*, u.username, u.email, u.full_name
           FROM students s
           JOIN users u ON s.user_id = u.user_id
           WHERE s.student_id = %s""",
        (student_id,),
        fetch_one=True
    )
    
    return render_template('student/profile.html', student=student_info)
