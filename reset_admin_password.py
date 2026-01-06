import bcrypt
from database import execute_query, init_connection_pool

def reset_admin_password():
    """Reset admin password to 'admin123'"""
    print("=" * 60)
    print("Resetting Admin Password")
    print("=" * 60)
    
    # Initialize database connection
    if not init_connection_pool():
        print("[ERROR] Could not connect to database!")
        return
    
    # Generate correct hash for 'admin123'
    password = "admin123"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    print(f"\nGenerating password hash for: {password}")
    print(f"New hash: {password_hash}")
    
    # Update admin user password
    result = execute_query(
        "UPDATE users SET password_hash = %s WHERE username = 'admin'",
        (password_hash,),
        commit=True
    )
    
    if result:
        print("\n[SUCCESS] Admin password has been reset!")
        print("\nYou can now login with:")
        print("  Username: admin")
        print("  Password: admin123")
        
        # Verify the update
        user = execute_query(
            "SELECT username, password_hash FROM users WHERE username = 'admin'",
            fetch_one=True
        )
        
        if user:
            # Test the new hash
            is_valid = bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))
            if is_valid:
                print("\n[VERIFIED] Password hash is correct and working!")
            else:
                print("\n[WARNING] Password verification still failing. This shouldn't happen.")
    else:
        print("\n[ERROR] Failed to update password!")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    reset_admin_password()
