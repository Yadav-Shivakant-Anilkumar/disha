-- Disha Computer Classes Management System
-- Database Schema for MySQL
-- Database: disha_computer

-- Drop tables if they exist (in reverse order of dependencies)
DROP TABLE IF EXISTS feedback;
DROP TABLE IF EXISTS learning_materials;
DROP TABLE IF EXISTS fee_transactions;
DROP TABLE IF EXISTS fees;
DROP TABLE IF EXISTS certificates;
DROP TABLE IF EXISTS exam_results;
DROP TABLE IF EXISTS exams;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS batches;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS teachers;
DROP TABLE IF EXISTS students;
DROP TABLE IF EXISTS users;

-- Users table (base table for all user types)
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'teacher', 'student', 'visitor') NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    status ENUM('active', 'inactive', 'suspended') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Students table (extended info for students)
CREATE TABLE students (
    student_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    enrollment_no VARCHAR(50) UNIQUE NOT NULL,
    dob DATE,
    gender ENUM('male', 'female', 'other'),
    contact VARCHAR(15),
    address TEXT,
    guardian_name VARCHAR(100),
    guardian_contact VARCHAR(15),
    guardian_email VARCHAR(100),
    admission_date DATE,
    photo_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_enrollment (enrollment_no)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Teachers table (extended info for teachers)
CREATE TABLE teachers (
    teacher_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNIQUE NOT NULL,
    employee_id VARCHAR(50) UNIQUE NOT NULL,
    qualification VARCHAR(255),
    specialization VARCHAR(255),
    experience_years INT,
    contact VARCHAR(15),
    address TEXT,
    joining_date DATE,
    photo_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_employee (employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Courses table
CREATE TABLE courses (
    course_id INT AUTO_INCREMENT PRIMARY KEY,
    course_code VARCHAR(20) UNIQUE NOT NULL,
    course_name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_months INT NOT NULL,
    fees DECIMAL(10, 2) NOT NULL,
    category VARCHAR(50),
    level ENUM('beginner', 'intermediate', 'advanced') DEFAULT 'beginner',
    status ENUM('active', 'inactive') DEFAULT 'active',
    syllabus_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_course_code (course_code),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Batches table
CREATE TABLE batches (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    batch_name VARCHAR(100) NOT NULL,
    teacher_id INT,
    start_date DATE NOT NULL,
    end_date DATE,
    schedule VARCHAR(255),
    timing VARCHAR(50),
    max_students INT DEFAULT 30,
    current_students INT DEFAULT 0,
    status ENUM('upcoming', 'ongoing', 'completed') DEFAULT 'upcoming',
    classroom VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Enrollments table
CREATE TABLE enrollments (
    enrollment_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    batch_id INT NOT NULL,
    enrollment_date DATE NOT NULL,
    status ENUM('active', 'completed', 'dropped', 'suspended') DEFAULT 'active',
    completion_date DATE,
    completion_status ENUM('passed', 'failed', 'in_progress') DEFAULT 'in_progress',
    final_grade VARCHAR(5),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id) ON DELETE CASCADE,
    UNIQUE KEY unique_enrollment (student_id, batch_id),
    INDEX idx_student (student_id),
    INDEX idx_batch (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Attendance table
CREATE TABLE attendance (
    attendance_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    student_id INT NOT NULL,
    attendance_date DATE NOT NULL,
    status ENUM('present', 'absent', 'late', 'excused') NOT NULL,
    marked_by INT NOT NULL,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (marked_by) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_attendance (batch_id, student_id, attendance_date),
    INDEX idx_date (attendance_date),
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Exams table
CREATE TABLE exams (
    exam_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT NOT NULL,
    exam_name VARCHAR(100) NOT NULL,
    exam_type ENUM('theory', 'practical', 'assignment', 'final') DEFAULT 'theory',
    exam_date DATE NOT NULL,
    total_marks INT NOT NULL,
    passing_marks INT NOT NULL,
    duration_minutes INT,
    description TEXT,
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_batch (batch_id),
    INDEX idx_date (exam_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Exam Results table
CREATE TABLE exam_results (
    result_id INT AUTO_INCREMENT PRIMARY KEY,
    exam_id INT NOT NULL,
    student_id INT NOT NULL,
    marks_obtained INT NOT NULL,
    grade VARCHAR(5),
    result_status ENUM('pass', 'fail') NOT NULL,
    remarks TEXT,
    entered_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (exam_id) REFERENCES exams(exam_id) ON DELETE CASCADE,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (entered_by) REFERENCES users(user_id) ON DELETE CASCADE,
    UNIQUE KEY unique_result (exam_id, student_id),
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Certificates table
CREATE TABLE certificates (
    certificate_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    certificate_no VARCHAR(50) UNIQUE NOT NULL,
    issue_date DATE NOT NULL,
    grade VARCHAR(5),
    certificate_path VARCHAR(255),
    issued_by INT NOT NULL,
    verification_code VARCHAR(50) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (issued_by) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_certificate_no (certificate_no),
    INDEX idx_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fees table
CREATE TABLE fees (
    fee_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    paid_amount DECIMAL(10, 2) DEFAULT 0.00,
    due_amount DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0.00,
    payment_status ENUM('pending', 'partial', 'paid', 'overdue') DEFAULT 'pending',
    due_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    INDEX idx_student (student_id),
    INDEX idx_status (payment_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Fee Transactions table
CREATE TABLE fee_transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    fee_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date DATE NOT NULL,
    payment_method ENUM('cash', 'card', 'upi', 'netbanking', 'cheque') NOT NULL,
    transaction_ref VARCHAR(100),
    receipt_no VARCHAR(50) UNIQUE,
    received_by INT NOT NULL,
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fee_id) REFERENCES fees(fee_id) ON DELETE CASCADE,
    FOREIGN KEY (received_by) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_fee (fee_id),
    INDEX idx_date (payment_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Learning Materials table
CREATE TABLE learning_materials (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    course_id INT NOT NULL,
    batch_id INT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    material_type ENUM('pdf', 'video', 'document', 'link', 'assignment') NOT NULL,
    file_path VARCHAR(255),
    file_size INT,
    uploaded_by INT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (batch_id) REFERENCES batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (uploaded_by) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_course (course_id),
    INDEX idx_batch (batch_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Feedback table
CREATE TABLE feedback (
    feedback_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    course_id INT,
    teacher_id INT,
    rating INT CHECK (rating >= 1 AND rating <= 5),
    category ENUM('course_content', 'teaching', 'facilities', 'overall', 'other') DEFAULT 'overall',
    comments TEXT,
    feedback_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_anonymous BOOLEAN DEFAULT FALSE,
    status ENUM('pending', 'reviewed', 'resolved') DEFAULT 'pending',
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    FOREIGN KEY (course_id) REFERENCES courses(course_id) ON DELETE CASCADE,
    FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id) ON DELETE CASCADE,
    INDEX idx_student (student_id),
    INDEX idx_course (course_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user
-- Password: admin123 (hashed using bcrypt)
INSERT INTO users (username, email, password_hash, role, full_name, status) 
VALUES ('admin', 'admin@dishacomputer.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5yvMZvM8kQjzi', 'admin', 'System Administrator', 'active');

-- Insert sample courses
INSERT INTO courses (course_code, course_name, description, duration_months, fees, category, level, status) VALUES
('CCC001', 'Basic Computer Course', 'Fundamentals of computer operations, MS Office, and internet basics', 3, 5000.00, 'Basic Computing', 'beginner', 'active'),
('WEB001', 'Web Development', 'HTML, CSS, JavaScript, and responsive web design', 6, 15000.00, 'Programming', 'intermediate', 'active'),
('PY001', 'Python Programming', 'Python fundamentals, data structures, and applications', 4, 12000.00, 'Programming', 'beginner', 'active'),
('ADPH001', 'Advanced Photoshop', 'Professional image editing and graphic design', 3, 8000.00, 'Design', 'advanced', 'active'),
('DM001', 'Digital Marketing', 'SEO, social media marketing, and online advertising', 4, 10000.00, 'Marketing', 'intermediate', 'active');

-- Create views for easy reporting
CREATE VIEW student_details AS
SELECT 
    u.user_id,
    u.username,
    u.email,
    u.full_name,
    u.status AS user_status,
    s.student_id,
    s.enrollment_no,
    s.dob,
    s.gender,
    s.contact,
    s.guardian_name,
    s.guardian_contact,
    s.admission_date
FROM users u
INNER JOIN students s ON u.user_id = s.user_id
WHERE u.role = 'student';

CREATE VIEW teacher_details AS
SELECT 
    u.user_id,
    u.username,
    u.email,
    u.full_name,
    u.status AS user_status,
    t.teacher_id,
    t.employee_id,
    t.qualification,
    t.specialization,
    t.experience_years,
    t.contact,
    t.joining_date
FROM users u
INNER JOIN teachers t ON u.user_id = t.user_id
WHERE u.role = 'teacher';

CREATE VIEW enrollment_details AS
SELECT 
    e.enrollment_id,
    s.student_id,
    s.enrollment_no,
    u.full_name AS student_name,
    c.course_name,
    b.batch_name,
    b.start_date,
    b.end_date,
    e.enrollment_date,
    e.status AS enrollment_status,
    e.completion_status
FROM enrollments e
INNER JOIN students s ON e.student_id = s.student_id
INNER JOIN users u ON s.user_id = u.user_id
INNER JOIN batches b ON e.batch_id = b.batch_id
INNER JOIN courses c ON b.course_id = c.course_id;

-- Database schema created successfully
