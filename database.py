import mysql.connector
from mysql.connector import Error, pooling
from config import Config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection pool
connection_pool = None

def init_connection_pool():
    """Initialize MySQL connection pool"""
    global connection_pool
    try:
        connection_pool = pooling.MySQLConnectionPool(
            pool_name="disha_pool",
            pool_size=5,
            pool_reset_session=True,
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT
        )
        logger.info("MySQL connection pool created successfully")
        return True
    except Error as e:
        logger.error(f"Error creating connection pool: {e}")
        return False

def get_db_connection():
    """Get a connection from the pool"""
    global connection_pool
    try:
        if connection_pool is None:
            init_connection_pool()
        connection = connection_pool.get_connection()
        return connection
    except Error as e:
        logger.error(f"Error getting connection from pool: {e}")
        return None

def execute_query(query, params=None, fetch=False, fetch_one=False, commit=False):
    """
    Execute a database query
    
    Args:
        query: SQL query string
        params: Query parameters (tuple)
        fetch: Whether to fetch results
        fetch_one: Fetch only one row
        commit: Whether to commit the transaction
    
    Returns:
        Query results or affected row count
    """
    connection = get_db_connection()
    if not connection:
        return None
    
    cursor = None
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params or ())
        
        if fetch_one:
            result = cursor.fetchone()
        elif fetch:
            result = cursor.fetchall()
        else:
            result = cursor.rowcount
            
        if commit:
            connection.commit()
            result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
            
        return result
    except Error as e:
        logger.error(f"Database error: {e}")
        if connection:
            connection.rollback()
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def execute_many(query, data_list):
    """
    Execute multiple queries with different parameters
    
    Args:
        query: SQL query string
        data_list: List of parameter tuples
    
    Returns:
        Number of affected rows
    """
    connection = get_db_connection()
    if not connection:
        return 0
    
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.executemany(query, data_list)
        connection.commit()
        return cursor.rowcount
    except Error as e:
        logger.error(f"Database error in executemany: {e}")
        if connection:
            connection.rollback()
        return 0
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

def test_connection():
    """Test database connection"""
    try:
        connection = get_db_connection()
        if connection and connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()
            logger.info(f"Connected to database: {db_name}")
            cursor.close()
            connection.close()
            return True
        return False
    except Error as e:
        logger.error(f"Connection test failed: {e}")
        return False
