from flask import Flask, render_template, redirect, url_for
from config import Config
from database import init_connection_pool, test_connection
import os

# Import blueprints
from auth import auth_bp
from routes.admin_routes import admin_bp
from routes.teacher_routes import teacher_bp
from routes.student_routes import student_bp
from routes.visitor_routes import visitor_bp

def create_app():
    """Application factory"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize configuration
    Config.init_app(app)
    
    # Initialize database connection pool
    init_connection_pool()
    
    # Test database connection
    if not test_connection():
        print("Warning: Could not connect to database. Please check your configuration.")
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(visitor_bp)
    
    # Global route for dashboard (redirects to role-specific dashboard)
    @app.route('/dashboard')
    def dashboard():
        from flask import session
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
        else:
            return redirect(url_for('visitor.home'))
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("=" * 60)
    print("Disha Computer Classes Management System")
    print("=" * 60)
    print("Server starting...")
    print("Access the application at: http://localhost:5000")
    print("Default admin login:")
    print("  Username: admin")
    print("  Password: admin123")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
