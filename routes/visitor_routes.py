from flask import Blueprint, render_template, request, flash
from database import execute_query

visitor_bp = Blueprint('visitor', __name__)

@visitor_bp.route('/')
def home():
    """Homepage for visitors"""
    # Get featured courses
    featured_courses = execute_query(
        """SELECT * FROM courses
           WHERE status = 'active'
           ORDER BY created_at DESC
           LIMIT 6""",
        fetch=True
    )
    
    # Get upcoming batches
    upcoming_batches = execute_query(
        """SELECT b.*, c.course_name, c.fees,
               (b.max_students - b.current_students) as available_seats
           FROM batches b
           JOIN courses c ON b.course_id = c.course_id
           WHERE b.status = 'upcoming'
               AND b.current_students < b.max_students
           ORDER BY b.start_date
           LIMIT 4""",
        fetch=True
    )
    
    # Get statistics
    stats = {
        'total_students': execute_query("SELECT COUNT(*) as count FROM students", fetch_one=True)['count'],
        'total_courses': execute_query("SELECT COUNT(*) as count FROM courses WHERE status='active'", fetch_one=True)['count'],
        'total_teachers': execute_query("SELECT COUNT(*) as count FROM teachers", fetch_one=True)['count']
    }
    
    return render_template('visitor/home.html',
                         featured_courses=featured_courses,
                         upcoming_batches=upcoming_batches,
                         stats=stats)

@visitor_bp.route('/about')
def about():
    """About page"""
    return render_template('visitor/about.html')

@visitor_bp.route('/courses')
def courses():
    """Course catalog"""
    # Get all active courses
    all_courses = execute_query(
        """SELECT c.*,
               COUNT(DISTINCT b.batch_id) as total_batches,
               COUNT(DISTINCT e.student_id) as total_students
           FROM courses c
           LEFT JOIN batches b ON c.course_id = b.course_id
           LEFT JOIN enrollments e ON b.batch_id = e.batch_id
           WHERE c.status = 'active'
           GROUP BY c.course_id
           ORDER BY c.course_name""",
        fetch=True
    )
    
    # Group by category
    categories = {}
    for course in all_courses:
        cat = course['category'] or 'Other'
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(course)
    
    return render_template('visitor/courses.html',
                         courses=all_courses,
                         categories=categories)

@visitor_bp.route('/course/<int:course_id>')
def course_detail(course_id):
    """Course detail page"""
    course = execute_query(
        "SELECT * FROM courses WHERE course_id = %s AND status = 'active'",
        (course_id,),
        fetch_one=True
    )
    
    if not course:
        flash('Course not found.', 'danger')
        return redirect(url_for('visitor.courses'))
    
    # Get available batches for this course
    batches = execute_query(
        """SELECT b.*, u.full_name as teacher_name, t.qualification,
               (b.max_students - b.current_students) as available_seats
           FROM batches b
           LEFT JOIN teachers t ON b.teacher_id = t.teacher_id
           LEFT JOIN users u ON t.user_id = u.user_id
           WHERE b.course_id = %s
               AND b.status IN ('upcoming', 'ongoing')
               AND b.current_students < b.max_students
           ORDER BY b.start_date""",
        (course_id,),
        fetch=True
    )
    
    return render_template('visitor/course_detail.html',
                         course=course,
                         batches=batches)

@visitor_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # In a real application, you would save this to a database or send an email
        # For now, just show a success message
        flash('Thank you for contacting us! We will get back to you soon.', 'success')
        
        # Could save to a contacts/inquiries table
        # execute_query(
        #     """INSERT INTO inquiries (name, email, phone, subject, message)
        #        VALUES (%s, %s, %s, %s, %s)""",
        #     (name, email, phone, subject, message),
        #     commit=True
        # )
    
    return render_template('visitor/contact.html')

@visitor_bp.route('/enquiry', methods=['GET', 'POST'])
def enquiry():
    """Course enquiry form"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        course_id = request.form.get('course_id')
        message = request.form.get('message', '').strip()
        
        flash('Your enquiry has been submitted successfully! We will contact you soon.', 'success')
        
        # Could save to database
        # execute_query(
        #     """INSERT INTO course_enquiries (name, email, phone, course_id, message)
        #        VALUES (%s, %s, %s, %s, %s)""",
        #     (name, email, phone, course_id, message),
        #     commit=True
        # )
    
    # Get courses for dropdown
    courses = execute_query(
        "SELECT course_id, course_name FROM courses WHERE status = 'active'",
        fetch=True
    )
    
    return render_template('visitor/enquiry.html', courses=courses)
