"""
IGNISYL - AUTHENTICATION & AUTHORIZATION SYSTEM
Complete user management with role-based access control
"""

import streamlit as st
import pandas as pd
import hashlib
import sqlite3
from datetime import datetime
import json

class AuthenticationSystem:
    """
    Complete authentication and authorization system
    Features:
    - User login/logout
    - Password hashing (SHA-256)
    - Role-based access control (RBAC)
    - Session management
    - Audit logging
    - Account lockout after failed attempts
    """
    
    def __init__(self, db_path='ignisyl_database.db'):
        self.db_path = db_path
        self.init_auth_database()
    
    def init_auth_database(self):
        """Initialize authentication tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                role TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_login DATETIME,
                is_active INTEGER DEFAULT 1,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until DATETIME
            )
        ''')
        
        # Roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role_name TEXT UNIQUE NOT NULL,
                description TEXT,
                permissions TEXT
            )
        ''')
        
        # Audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                username TEXT,
                action TEXT,
                details TEXT,
                ip_address TEXT,
                success INTEGER
            )
        ''')
        
        conn.commit()
        
        # Initialize default roles
        self._init_default_roles(conn)
        
        # Create default users
        self._init_default_users(conn)
        
        conn.close()
    
    def _init_default_roles(self, conn):
        """Initialize default roles with permissions"""
        default_roles = [
            {
                'role_name': 'Admin',
                'description': 'Full system access - can manage everything',
                'permissions': json.dumps({
                    'view_dashboard': True,
                    'view_threats': True,
                    'whitelist': True,
                    'block_users': True,
                    'modify_settings': True,
                    'manage_users': True,
                    'view_audit_logs': True,
                    'download_reports': True
                })
            },
            {
                'role_name': 'Security_Analyst',
                'description': 'Threat analysis and response',
                'permissions': json.dumps({
                    'view_dashboard': True,
                    'view_threats': True,
                    'whitelist': True,
                    'block_users': True,
                    'modify_settings': False,
                    'manage_users': False,
                    'view_audit_logs': True,
                    'download_reports': True
                })
            },
            {
                'role_name': 'Viewer',
                'description': 'Read-only access - cannot make changes',
                'permissions': json.dumps({
                    'view_dashboard': True,
                    'view_threats': True,
                    'whitelist': False,
                    'block_users': False,
                    'modify_settings': False,
                    'manage_users': False,
                    'view_audit_logs': False,
                    'download_reports': False
                })
            },
            {
                'role_name': 'Auditor',
                'description': 'Compliance and audit access',
                'permissions': json.dumps({
                    'view_dashboard': True,
                    'view_threats': True,
                    'whitelist': False,
                    'block_users': False,
                    'modify_settings': False,
                    'manage_users': False,
                    'view_audit_logs': True,
                    'download_reports': True
                })
            }
        ]
        
        cursor = conn.cursor()
        for role in default_roles:
            cursor.execute('''
                INSERT OR IGNORE INTO roles (role_name, description, permissions)
                VALUES (?, ?, ?)
            ''', (role['role_name'], role['description'], role['permissions']))
        conn.commit()
    
    def _init_default_users(self, conn):
        """Create default users if none exist"""
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Create default users for demo
            default_users = [
                {
                    'username': 'admin',
                    'password': 'admin123',
                    'full_name': 'System Administrator',
                    'email': 'admin@ignisyl.com',
                    'role': 'Admin'
                },
                {
                    'username': 'analyst',
                    'password': 'analyst123',
                    'full_name': 'Security Analyst',
                    'email': 'analyst@ignisyl.com',
                    'role': 'Security_Analyst'
                },
                {
                    'username': 'viewer',
                    'password': 'viewer123',
                    'full_name': 'Read Only User',
                    'email': 'viewer@ignisyl.com',
                    'role': 'Viewer'
                },
                {
                    'username': 'auditor',
                    'password': 'auditor123',
                    'full_name': 'Compliance Auditor',
                    'email': 'auditor@ignisyl.com',
                    'role': 'Auditor'
                }
            ]
            
            for user in default_users:
                password_hash = self._hash_password(user['password'])
                cursor.execute('''
                    INSERT INTO users (username, password_hash, full_name, email, role)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user['username'], password_hash, user['full_name'], 
                      user['email'], user['role']))
            
            conn.commit()
    
    def _hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username, password):
        """
        Authenticate user credentials
        Returns: (success: bool, message: str, user_data: dict)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if account is locked
        cursor.execute('''
            SELECT account_locked_until FROM users 
            WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        
        if result and result[0]:
            locked_until = datetime.fromisoformat(result[0])
            if datetime.now() < locked_until:
                self._log_audit(username, 'LOGIN_FAILED', 
                              'Account locked', False)
                conn.close()
                return False, "⛔ Account is locked. Try again later.", None
        
        # Get user data
        cursor.execute('''
            SELECT username, password_hash, full_name, email, role, is_active,
                   failed_login_attempts
            FROM users 
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if not user:
            self._log_audit(username, 'LOGIN_FAILED', 
                          'User not found', False)
            conn.close()
            return False, "❌ Invalid username or password", None
        
        username_db, password_hash, full_name, email, role, is_active, failed_attempts = user
        
        # Check if account is active
        if not is_active:
            self._log_audit(username, 'LOGIN_FAILED', 
                          'Account disabled', False)
            conn.close()
            return False, "⛔ Account is disabled. Contact administrator.", None
        
        # Verify password
        input_hash = self._hash_password(password)
        
        if input_hash != password_hash:
            # Increment failed login attempts
            failed_attempts += 1
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                lock_until = datetime.now().replace(
                    hour=datetime.now().hour + 1
                )
                cursor.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?,
                        account_locked_until = ?
                    WHERE username = ?
                ''', (failed_attempts, lock_until.isoformat(), username))
                conn.commit()
                self._log_audit(username, 'ACCOUNT_LOCKED', 
                              f'Too many failed attempts', False)
                conn.close()
                return False, "🚫 Account locked due to 5 failed attempts. Try again in 1 hour.", None
            else:
                cursor.execute('''
                    UPDATE users 
                    SET failed_login_attempts = ?
                    WHERE username = ?
                ''', (failed_attempts, username))
                conn.commit()
            
            self._log_audit(username, 'LOGIN_FAILED', 
                          'Invalid password', False)
            conn.close()
            return False, f"❌ Invalid password. {5 - failed_attempts} attempts remaining.", None
        
        # Successful login - reset failed attempts
        cursor.execute('''
            UPDATE users 
            SET failed_login_attempts = 0,
                last_login = ?,
                account_locked_until = NULL
            WHERE username = ?
        ''', (datetime.now().isoformat(), username))
        conn.commit()
        
        # Get permissions
        cursor.execute('''
            SELECT permissions FROM roles WHERE role_name = ?
        ''', (role,))
        permissions_json = cursor.fetchone()[0]
        permissions = json.loads(permissions_json)
        
        user_data = {
            'username': username_db,
            'full_name': full_name,
            'email': email,
            'role': role,
            'permissions': permissions
        }
        
        self._log_audit(username, 'LOGIN_SUCCESS', 
                      'User logged in successfully', True)
        
        conn.close()
        return True, "✅ Login successful", user_data
    
    def _log_audit(self, username, action, details, success):
        """Log audit events"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_log (username, action, details, success)
            VALUES (?, ?, ?, ?)
        ''', (username, action, details, 1 if success else 0))
        
        conn.commit()
        conn.close()
    
    def has_permission(self, user_data, permission):
        """Check if user has specific permission"""
        if not user_data:
            return False
        return user_data.get('permissions', {}).get(permission, False)
    
    def get_audit_logs(self, limit=100):
        """Get recent audit logs"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query(f'''
            SELECT * FROM audit_log 
            ORDER BY timestamp DESC 
            LIMIT {limit}
        ''', conn)
        conn.close()
        return df
    
    def create_user(self, username, password, full_name, email, role):
        """Create new user (Admin only)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            password_hash = self._hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, role)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, full_name, email, role))
            conn.commit()
            self._log_audit(username, 'USER_CREATED', 
                          f'User created with role {role}', True)
            conn.close()
            return True, "✅ User created successfully"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "❌ Username already exists"
    
    def get_all_users(self):
        """Get all users (Admin only)"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT username, full_name, email, role, 
                   last_login, is_active
            FROM users
            ORDER BY username
        ''', conn)
        conn.close()
        return df
    
    def change_password(self, username, old_password, new_password):
        """Change user password"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verify old password
        cursor.execute('''
            SELECT password_hash FROM users WHERE username = ?
        ''', (username,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False, "❌ User not found"
        
        old_hash = self._hash_password(old_password)
        if old_hash != result[0]:
            conn.close()
            return False, "❌ Current password is incorrect"
        
        # Update password
        new_hash = self._hash_password(new_password)
        cursor.execute('''
            UPDATE users SET password_hash = ? WHERE username = ?
        ''', (new_hash, username))
        conn.commit()
        
        self._log_audit(username, 'PASSWORD_CHANGED', 
                      'User changed password', True)
        conn.close()
        return True, "✅ Password changed successfully"


if __name__ == "__main__":
    # Test authentication system
    print("Initializing Authentication System...")
    auth = AuthenticationSystem()
    print("✅ Database initialized")
    print("\nDefault Users Created:")
    print("1. admin / admin123 (Admin)")
    print("2. analyst / analyst123 (Security Analyst)")
    print("3. viewer / viewer123 (Viewer)")
    print("4. auditor / auditor123 (Auditor)")
