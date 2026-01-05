import bcrypt
from database import execute_query, init_connection_pool

def test_admin_login():
    """Test admin login credentials"""
    print("=" * 60)
    print("Testing Admin Login")
    print("=" * 60)
    
    # Initialize database connection
    if not init_connection_pool():
        print("ERROR: Could not connect to database!")
        return
    
    # Test credentials
    test_username = "admin"
    test_password = "admin123"
    
    print(f"\nTesting login with:")
    print(f"  Username: {test_username}")
    print(f"  Password: {test_password}")
    
    # Get user from database
    user = execute_query(
        "SELECT * FROM users WHERE username = %s",
        (test_username,),
        fetch_one=True
    )
    
    if not user:
        print("\n[ERROR] User 'admin' not found in database!")
        print("   Please check if the admin user was created properly.")
        return
    
    print(f"\n[OK] User found in database")
    print(f"  User ID: {user['user_id']}")
    print(f"  Username: {user['username']}")
    print(f"  Email: {user['email']}")
    print(f"  Role: {user['role']}")
    print(f"  Status: {user['status']}")
    print(f"  Full Name: {user['full_name']}")
    print(f"  Password Hash: {user['password_hash']}")
    
    # Check if user is active
    if user['status'] != 'active':
        print(f"\n[ERROR] User status is '{user['status']}', not 'active'!")
        print("   The login query requires status = 'active'")
        return
    
    # Test password verification
    print("\nTesting password verification...")
    stored_hash = user['password_hash']
    
    try:
        # Verify password
        is_valid = bcrypt.checkpw(
            test_password.encode('utf-8'),
            stored_hash.encode('utf-8')
        )
        
        if is_valid:
            print("[SUCCESS] Password verification SUCCESSFUL!")
            print("  The password 'admin123' matches the stored hash.")
            print("\n[OK] Login should work! Check for other issues:")
            print("  1. Make sure MySQL is running on port 3309")
            print("  2. Check for JavaScript errors in browser console")
            print("  3. Check Flask application logs")
        else:
            print("[FAILED] Password verification FAILED!")
            print("  The password 'admin123' does NOT match the stored hash.")
            print("\n  Possible solutions:")
            print("  1. The hash in database might be incorrect")
            print("  2. Try resetting the admin password")
    except Exception as e:
        print(f"[ERROR] during password verification: {e}")
        print(f"   Hash format might be invalid")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_admin_login()
