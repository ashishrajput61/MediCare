import streamlit as st
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from twilio.rest import Client

# Get configuration from secrets
DB_CONFIG = {
    "host": st.secrets["database"]["host"],
    "user": st.secrets["database"]["user"],
    "password": st.secrets["database"]["password"],
    "database": st.secrets["database"]["database"],
}

# Twilio configuration
TWILIO_ACCOUNT_SID = st.secrets.get("twilio", {}).get("account_sid", "")
TWILIO_AUTH_TOKEN = st.secrets.get("twilio", {}).get("auth_token", "")
TWILIO_PHONE = st.secrets.get("twilio", {}).get("phone_number", "")

def get_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Error connecting to database: {e}")
        return None

def execute_query(query, params=None, fetch=False):
    """Execute a query and optionally fetch results"""
    conn = get_connection()
    if not conn:
        return None
    
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount
        
        cursor.close()
        return result
    except Error as e:
        st.error(f"Database error: {e}")
        return None
    finally:
        conn.close()

def send_sms(phone_number, message):
    """Send SMS notification using Twilio"""
    try:
        if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
            client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            message = client.messages.create(
                body=message,
                from_=TWILIO_PHONE,
                to=f"+91{phone_number}" if not phone_number.startswith('+') else phone_number
            )
            return True
    except Exception as e:
        print(f"SMS Error: {e}")
    return False

# Doctor functions
def get_doctor_count():
    """Get total number of doctors"""
    query = "SELECT COUNT(*) FROM doctors"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else 0

def get_doctors_by_department(dept_id):
    """Get doctors by department"""
    query = """
        SELECT id, name, expertise, consultation_fee, phone 
        FROM doctors 
        WHERE department_id = %s 
        ORDER BY rating DESC 
        LIMIT 5
    """
    return execute_query(query, (dept_id,), fetch=True) or []

# Department functions
def get_department_count():
    """Get total number of departments"""
    query = "SELECT COUNT(*) FROM departments"
    result = execute_query(query, fetch=True)
    return result[0][0] if result else 0

def get_all_departments():
    """Get all departments"""
    query = "SELECT id, name FROM departments ORDER BY name"
    return execute_query(query, fetch=True) or []

# Service functions
def get_services():
    """Get all services"""
    query = "SELECT id, name, description FROM services"
    return execute_query(query, fetch=True) or []

# Appointment functions
def book_appointment(phone, doctor_id, dept_id, appt_date, problem):
    """Book an appointment"""
    query = """
        INSERT INTO appointments (user_phone, doctor_id, department_id, appointment_date, problem, status, created_at)
        VALUES (%s, %s, %s, %s, %s, 'pending', %s)
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = execute_query(query, (phone, doctor_id, dept_id, appt_date, problem, created_at))
    
    if result:
        message = f"Hi! Your appointment has been booked. You will receive confirmation SMS once approved. Appointment Date: {appt_date}"
        send_sms(phone, message)
        return True
    return False

def get_appointments_by_user(phone):
    """Get appointments for a specific user"""
    query = """
        SELECT id, user_phone, doctor_id, department_id, appointment_date, problem, status, created_at
        FROM appointments 
        WHERE user_phone = %s 
        ORDER BY appointment_date DESC
    """
    return execute_query(query, (phone,), fetch=True) or []

def get_all_appointments():
    """Get all appointments (for admin)"""
    query = """
        SELECT id, user_phone, doctor_id, department_id, appointment_date, problem, status, created_at
        FROM appointments 
        ORDER BY created_at DESC
    """
    return execute_query(query, fetch=True) or []

def cancel_appointment(appt_id):
    """Cancel an appointment"""
    query = "UPDATE appointments SET status = 'cancelled' WHERE id = %s"
    return execute_query(query, (appt_id,))

def approve_appointment(appt_id):
    """Approve an appointment (admin only)"""
    # Get appointment details
    query = """
        SELECT a.user_phone, d.name, d.consultation_fee, a.appointment_date
        FROM appointments a
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.id = %s
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (appt_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        phone, doctor_name, fee, appt_date = result
        
        # Update status
        update_query = "UPDATE appointments SET status = 'approved' WHERE id = %s"
        execute_query(update_query, (appt_id,))
        
        # Send SMS
        message = f"✅ Your appointment has been APPROVED!\n\nDr. {doctor_name}\nFee: ₹{fee}\nDate: {appt_date}\n\nPlease arrive 10 minutes early."
        send_sms(phone, message)
        return True
    return False

def reject_appointment(appt_id):
    """Reject an appointment (admin only)"""
    # Get appointment details
    query = """
        SELECT a.user_phone, a.appointment_date
        FROM appointments a
        WHERE a.id = %s
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (appt_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if result:
        phone, appt_date = result
        
        # Update status
        update_query = "UPDATE appointments SET status = 'rejected' WHERE id = %s"
        execute_query(update_query, (appt_id,))
        
        # Send SMS
        message = f"❌ Your appointment scheduled for {appt_date} has been REJECTED.\n\nPlease book another appointment or contact us for more information."
        send_sms(phone, message)
        return True
    return False

# Medicine functions
def get_all_medicines():
    """Get all medicines"""
    query = """
        SELECT id, name, description, price, stock 
        FROM medicines 
        ORDER BY name
    """
    return execute_query(query, fetch=True) or []

def add_medicine_purchase(phone, medicine_id, quantity, total_price):
    """Add a medicine purchase"""
    query = """
        INSERT INTO medicine_purchases (user_phone, medicine_id, quantity, total_price, status, created_at)
        VALUES (%s, %s, %s, %s, 'pending', %s)
    """
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Get medicine name
    med_query = "SELECT name FROM medicines WHERE id = %s"
    cursor.execute(med_query, (medicine_id,))
    med_result = cursor.fetchone()
    med_name = med_result[0] if med_result else "Medicine"
    
    # Insert purchase
    cursor.execute(query, (phone, medicine_id, quantity, total_price, created_at))
    conn.commit()
    
    cursor.close()
    conn.close()
    
    # Send SMS
    message = f"💊 Your order has been placed!\n\n{med_name} x {quantity}\nTotal: ₹{total_price}\n\nYou'll receive delivery confirmation SMS shortly."
    send_sms(phone, message)
    return True

def get_medicine_purchases_by_user(phone):
    """Get medicine purchases for a user"""
    query = """
        SELECT mp.id, m.name, mp.quantity, mp.total_price, mp.status, mp.created_at
        FROM medicine_purchases mp
        JOIN medicines m ON mp.medicine_id = m.id
        WHERE mp.user_phone = %s
        ORDER BY mp.created_at DESC
    """
    return execute_query(query, (phone,), fetch=True) or []

# Utility function to create tables (run this once)
def create_tables():
    """Create all required tables"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    # Create departments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create doctors table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            department_id INT NOT NULL,
            expertise VARCHAR(100),
            consultation_fee DECIMAL(10, 2),
            phone VARCHAR(20),
            rating DECIMAL(3, 2) DEFAULT 4.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)
    
    # Create services table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create appointments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_phone VARCHAR(20) NOT NULL,
            doctor_id INT NOT NULL,
            department_id INT NOT NULL,
            appointment_date DATE NOT NULL,
            problem TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id),
            FOREIGN KEY (department_id) REFERENCES departments(id)
        )
    """)
    
    # Create medicines table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            price DECIMAL(10, 2) NOT NULL,
            stock INT DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create medicine_purchases table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_purchases (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_phone VARCHAR(20) NOT NULL,
            medicine_id INT NOT NULL,
            quantity INT NOT NULL,
            total_price DECIMAL(10, 2) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (medicine_id) REFERENCES medicines(id)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return True