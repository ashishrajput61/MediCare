import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
from datetime import datetime, timedelta
import time
from database import (
    get_doctor_count, get_department_count,
    get_all_departments, get_doctors_by_department, book_appointment,
    get_appointments_by_user, cancel_appointment, get_all_appointments,
    approve_appointment, reject_appointment, get_all_medicines,
    get_services, add_medicine_purchase
)

# Page configuration
st.set_page_config(
    page_title="MediCare Hub",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful UI
st.markdown("""
    <style>
    /* Main theme colors */
    :root {
        --primary-color: #0066CC;
        --secondary-color: #00CC99;
        --danger-color: #FF6B6B;
        --warning-color: #FFA500;
        --success-color: #51CF66;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #0066CC 0%, #00CC99 100%);
    }
    
    /* Main content background */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Card styling */
    .doctor-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #0066CC;
        margin: 10px 0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .doctor-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
    }
    
    /* Department card */
    .dept-card {
        background: linear-gradient(135deg, #0066CC 0%, #0052A3 100%);
        color: white;
        border-radius: 12px;
        padding: 25px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s ease;
        margin: 10px;
    }
    
    .dept-card:hover {
        transform: scale(1.05);
    }
    
    /* Service card */
    .service-card {
        background: linear-gradient(135deg, #00CC99 0%, #00AA88 100%);
        color: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .service-card:hover {
        transform: translateY(-8px);
    }
    
    /* Header styling */
    .header-title {
        color: #0066CC;
        font-size: 2.5em;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Badge styling */
    .badge {
        display: inline-block;
        background: #E3F2FD;
        color: #0066CC;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.9em;
        font-weight: 500;
        margin: 5px 5px 5px 0;
    }
    
    /* Metric styling */
    .metric-box {
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-top: 4px solid #0066CC;
    }
    
    .metric-number {
        font-size: 2.5em;
        font-weight: bold;
        color: #0066CC;
    }
    
    .metric-label {
        color: #666;
        font-size: 1em;
        margin-top: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_phone' not in st.session_state:
    st.session_state.user_phone = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# Sidebar navigation
with st.sidebar:
    st.markdown("""
        <div style='text-align: center; color: black; padding: 20px 0;'>
            <h1>🏥 MediCare Hub</h1>
            <p style='font-size: 0.9em;'>Your Healthcare Partner</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Admin login section
    with st.expander("🔐 Admin Login"):
        admin_password = st.text_input("Admin Password", type="password")
        if st.button("Login as Admin"):
            if admin_password == "admin123":
                st.session_state.is_admin = True
                st.success("Admin logged in!")
            else:
                st.error("Invalid password!")
    
    # User info section
    st.subheader("👤 User Info")
    user_name = st.text_input("Your Name")
    user_phone = st.text_input("Your Phone Number")
    
    if user_name and user_phone:
        st.session_state.user_name = user_name
        st.session_state.user_phone = user_phone
        st.success(f"Welcome, {user_name}!")
    
    st.divider()
    
    # Navigation menu
    if st.session_state.is_admin:
        selected = option_menu(
            menu_title="Navigation",
            options=["Dashboard", "Departments", "Services", "Medicine Store", "Admin Panel", "About"],
            icons=["speedometer2", "hospital-fill", "heart-pulse", "capsule", "shield-lock", "info-circle"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "black", "font-size": "20px"},
                "nav-link": {"color": "black", "font-size": "16px", "text-align": "left", "margin": "10px 0"},
                "nav-link-selected": {"background-color": "rgba(255,255,255,0.2)"},
            }
        )
    else:
        selected = option_menu(
            menu_title="Navigation",
            options=["Dashboard", "Departments", "Services", "Medicine Store", "My Appointments", "About"],
            icons=["speedometer2", "hospital-fill", "heart-pulse", "capsule", "calendar-check", "info-circle"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "black", "font-size": "20px"},
                "nav-link": {"color": "black", "font-size": "16px", "text-align": "left", "margin": "10px 0"},
                "nav-link-selected": {"background-color": "rgba(255,255,255,0.2)"},
            }
        )

# Main content area
def dashboard_page():
    st.markdown("<h1 class='header-title'>🏥 Welcome to MediCare Hub</h1>", unsafe_allow_html=True)
    
    if st.session_state.user_name:
        st.markdown(f"""
            <div style='background: linear-gradient(135deg, #0066CC 0%, #00CC99 100%); 
                        color: white; padding: 25px; border-radius: 12px; text-align: center;'>
                <h2>Welcome, {st.session_state.user_name}! 👋</h2>
                <p>We're here to provide you with the best healthcare services</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Metrics
    col1, col2, col3 = st.columns(3)
    
    doctor_count = get_doctor_count()
    dept_count = get_department_count()
    
    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-number'>👨‍⚕️ {doctor_count}</div>
                <div class='metric-label'>Experienced Doctors</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-number'>🏢 {dept_count}</div>
                <div class='metric-label'>Departments</div>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-number'>⭐ 4.8</div>
                <div class='metric-label'>Rating</div>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    

    
    # Featured content
    st.subheader("ℹ️ Why Choose MediCare Hub?")
    
    features = [
        ("✅ Expert Doctors", "Highly qualified and experienced medical professionals"),
        ("✅ 24/7 Service", "Round-the-clock appointment booking and support"),
        ("✅ Online Consultation", "Consult from the comfort of your home"),
        ("✅ Affordable Rates", "Transparent and competitive pricing")
    ]
    
    feat_col1, feat_col2 = st.columns(2)
    
    for i, (title, desc) in enumerate(features):
        if i % 2 == 0:
            with feat_col1:
                st.info(f"{title}\n\n{desc}")
        else:
            with feat_col2:
                st.info(f"{title}\n\n{desc}")

def departments_page():
    st.markdown("<h1 class='header-title'>🏥 Our Departments</h1>", unsafe_allow_html=True)
    
    departments = get_all_departments()
    
    if departments:
        # Create tabs for each department
        dept_names = [d[1] for d in departments]
        tabs = st.tabs(dept_names)
        
        for idx, tab in enumerate(tabs):
            with tab:
                dept_id, dept_name = departments[idx]
                
                st.markdown(f"<h2 style='color: #0066CC;'>{dept_name}</h2>", unsafe_allow_html=True)
                
                # Get doctors for this department
                doctors = get_doctors_by_department(dept_id)
                
                if doctors:
                    st.subheader(f"Top Doctors in {dept_name}")
                    
                    for doctor in doctors[:5]:
                        doc_id, doc_name, expertise, fee, phone = doctor
                        
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"""
                                <div class='doctor-card'>
                                    <h3 style='color: #0066CC; margin: 0;'>👨‍⚕️ Dr. {doc_name}</h3>
                                    <p style='color: #666; margin: 5px 0;'><strong>Expertise:</strong> {expertise}</p>
                                    <p style='color: #666; margin: 5px 0;'><strong>Consultation Fee:</strong> ₹{fee}</p>
                                    <p style='color: #666; margin: 5px 0;'><strong>Phone:</strong> {phone}</p>
                                    <span class='badge'>Available</span>
                                </div>
                            """, unsafe_allow_html=True)
                        
                        with col2:
                            if st.button("Book Now", key=f"book_{doc_id}"):
                                st.session_state.selected_doctor = doc_id
                                st.session_state.selected_dept = dept_id
                else:
                    st.warning(f"No doctors available in {dept_name}")
        
        st.divider()
        st.subheader("📅 Book an Appointment")
        
        if st.session_state.user_phone:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                dept_id = st.selectbox("Select Department", [d[0] for d in departments], 
                                     format_func=lambda x: next(d[1] for d in departments if d[0] == x))
            
            doctors = get_doctors_by_department(dept_id)
            if doctors:
                with col2:
                    doctor_id = st.selectbox("Select Doctor", [d[0] for d in doctors], 
                                           format_func=lambda x: next(f"Dr. {d[1]}" for d in doctors if d[0] == x))
            
            with col3:
                appt_date = st.date_input("Select Date", min_value=datetime.now().date())
            
            problem = st.text_area("Describe your problem")
            
            if st.button("Book Appointment", use_container_width=True):
                if problem:
                    book_appointment(st.session_state.user_phone, doctor_id, dept_id, 
                                   str(appt_date), problem)
                    st.success("✅ Appointment booked successfully! You will receive an SMS confirmation.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Please describe your problem")
        else:
            st.warning("Please enter your phone number in the sidebar first!")
    else:
        st.error("No departments found")

def services_page():
    st.markdown("<h1 class='header-title'>❤️ Our Services</h1>", unsafe_allow_html=True)
    st.markdown("Click on any service to learn more or book an appointment")
    
    services = get_services()
    
    if services:
        cols = st.columns(3)
        
        for idx, service in enumerate(services):
            service_id, service_name, description = service
            
            with cols[idx % 3]:
                st.markdown(f"""
                    <div class='service-card' style='cursor: pointer;'>
                        <h3>{service_name}</h3>
                        <p style='font-size: 0.95em;'>{description}</p>
                    </div>
                """, unsafe_allow_html=True)
                
                if st.button("Learn More", key=f"service_{service_id}"):
                    st.info(f"**{service_name}**\n\n{description}\n\nTo book this service, please visit the Departments section and select an appropriate doctor.")
    else:
        st.warning("No services available at the moment")

def medicines_page():
    st.markdown("<h1 class='header-title'>💊 Medicine Store</h1>", unsafe_allow_html=True)
    
    medicines = get_all_medicines()
    
    if medicines:
        # Search and filter
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            search_term = st.text_input("Search medicines", placeholder="Type medicine name...")
        
        with search_col2:
            price_filter = st.slider("Filter by price (₹)", 0, 500, (0, 500))
        
        # Filter medicines
        filtered_medicines = medicines
        
        if search_term:
            filtered_medicines = [m for m in filtered_medicines 
                                if search_term.lower() in m[1].lower()]
        
        filtered_medicines = [m for m in filtered_medicines 
                            if price_filter[0] <= m[3] <= price_filter[1]]
        
        if filtered_medicines:
            cols = st.columns(3)
            
            for idx, medicine in enumerate(filtered_medicines):
                med_id, med_name, description, price, stock = medicine
                
                with cols[idx % 3]:
                    st.markdown(f"""
                        <div class='doctor-card' style='border-left-color: #00CC99;'>
                            <h4 style='color: #00CC99; margin: 0;'>💊 {med_name}</h4>
                            <p style='color: #666; font-size: 0.9em; margin: 5px 0;'>{description}</p>
                            <p style='color: #0066CC; font-weight: bold; margin: 5px 0;'>₹{price}</p>
                            <p style='color: #666; font-size: 0.9em; margin: 5px 0;'>Stock: {stock}</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if stock > 0:
                        qty = st.number_input("Qty", min_value=1, max_value=stock, value=1, key=f"qty_{med_id}")
                        if st.button("Order Now", key=f"order_{med_id}"):
                            if st.session_state.user_phone:
                                add_medicine_purchase(st.session_state.user_phone, med_id, qty, price * qty)
                                st.success(f"✅ Order placed! You'll receive SMS confirmation at {st.session_state.user_phone}")
                                time.sleep(2)
                                st.rerun()
                            else:
                                st.error("Please enter your phone number in the sidebar first!")
                    else:
                        st.error("Out of stock")
        else:
            st.warning("No medicines found matching your criteria")
    else:
        st.error("No medicines available")

def my_appointments_page():
    st.markdown("<h1 class='header-title'>📅 My Appointments</h1>", unsafe_allow_html=True)
    
    if st.session_state.user_phone:
        appointments = get_appointments_by_user(st.session_state.user_phone)
        
        if appointments:
            st.subheader("Your Appointments")
            
            for appt in appointments:
                appt_id, user_phone, doctor_id, dept_id, appt_date, problem, status, created_at = appt
                
                if status == "approved":
                    status_color = "🟢"
                elif status == "rejected":
                    status_color = "🔴"
                else:
                    status_color = "🟡"
                
                with st.expander(f"{status_color} Appointment - {appt_date} (Status: {status.upper()})"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Date:** {appt_date}")
                        st.write(f"**Problem:** {problem}")
                        st.write(f"**Status:** {status.upper()}")
                    
                    with col2:
                        st.write(f"**Booked on:** {created_at}")
                    
                    if status == "pending":
                        if st.button("Cancel Appointment", key=f"cancel_{appt_id}"):
                            cancel_appointment(appt_id)
                            st.success("Appointment cancelled!")
                            time.sleep(1)
                            st.rerun()
        else:
            st.info("You don't have any appointments yet. Book one now!")
    else:
        st.warning("Please enter your phone number in the sidebar to view your appointments.")

def admin_panel():
    st.markdown("<h1 class='header-title'>🛡️ Admin Panel</h1>", unsafe_allow_html=True)
    
    if not st.session_state.is_admin:
        st.error("⚠️ Admin access required. Please login using the admin panel in the sidebar.")
        return
    
    admin_tab1, admin_tab2 = st.tabs(["Manage Appointments", "Analytics"])
    
    with admin_tab1:
        st.subheader("All Appointments")
        
        appointments = get_all_appointments()
        
        if appointments:
            for appt in appointments:
                appt_id, user_phone, doctor_id, dept_id, appt_date, problem, status, created_at = appt
                
                if status == "approved":
                    status_emoji = "🟢"
                elif status == "rejected":
                    status_emoji = "🔴"
                else:
                    status_emoji = "🟡"
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"{status_emoji} **{user_phone}** | **{appt_date}** | {problem}")
                
                with col2:
                    st.write(f"Status: {status}")
                
                with col3:
                    if status == "pending":
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("✅ Approve", key=f"approve_{appt_id}"):
                                approve_appointment(appt_id)
                                st.success("Appointment approved!")
                                time.sleep(1)
                                st.rerun()
                        with btn_col2:
                            if st.button("❌ Reject", key=f"reject_{appt_id}"):
                                reject_appointment(appt_id)
                                st.success("Appointment rejected!")
                                time.sleep(1)
                                st.rerun()
        else:
            st.info("No appointments found")
    
    with admin_tab2:
        st.subheader("Analytics Dashboard")
        
        all_appts = get_all_appointments()
        if all_appts:
            approved_count = sum(1 for a in all_appts if a[6] == "approved")
            rejected_count = sum(1 for a in all_appts if a[6] == "rejected")
            pending_count = sum(1 for a in all_appts if a[6] == "pending")
            
            metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
            
            with metric_col1:
                st.metric("Total Appointments", len(all_appts))
            with metric_col2:
                st.metric("Approved", approved_count, delta=None)
            with metric_col3:
                st.metric("Rejected", rejected_count, delta=None)
            with metric_col4:
                st.metric("Pending", pending_count, delta=None)
            
            chart_data = pd.DataFrame({
                'Status': ['Approved', 'Rejected', 'Pending'],
                'Count': [approved_count, rejected_count, pending_count]
            })
            
            st.bar_chart(chart_data.set_index('Status'))

def about_page():
    st.markdown("<h1 class='header-title'>ℹ️ About MediCare Hub</h1>", unsafe_allow_html=True)
    
    st.markdown("""
        <div style='background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h2 style='color: #0066CC;'>About Us</h2>
            <p style='font-size: 1.1em; line-height: 1.8; color: #333;'>
                MediCare Hub is a comprehensive healthcare management platform designed to connect patients 
                with qualified healthcare professionals and essential medical services. Our mission is to make 
                healthcare accessible, affordable, and convenient for everyone.
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    st.markdown("""
        <div style='background: white; padding: 25px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);'>
            <h2 style='color: #00CC99;'>Developer Details</h2>
        </div>
    """, unsafe_allow_html=True)
    
    dev_col1, dev_col2 = st.columns(2)
    
    with dev_col1:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #0066CC 0%, #00CC99 100%); 
                        color: white; padding: 20px; border-radius: 12px; text-align: center;'>
                <h3>📱 Phone</h3>
                <p style='font-size: 1.2em; font-weight: bold;'>+91 7505197684</p>
            </div>
        """, unsafe_allow_html=True)
    
    with dev_col2:
        st.markdown("""
            <div style='background: linear-gradient(135deg, #00CC99 0%, #00AA88 100%); 
                        color: white; padding: 20px; border-radius: 12px; text-align: center;'>
                <h3>📧 Email</h3>
                <p style='font-size: 1.1em; font-weight: bold;'>rajputashish6165@gmail.com</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    st.subheader("🌟 Key Features")
    
    features_list = [
        "🏥 Connect with 500+ experienced doctors",
        "🏢 Services across 10+ medical departments",
        "📅 Easy online appointment booking",
        "💊 Online medicine store with home delivery",
        "📲 Instant SMS notifications",
        "⭐ 4.8/5 average rating from patients",
        "💰 Affordable consultation fees",
        "🔒 Secure and confidential"
    ]
    
    for feature in features_list:
        st.write(feature)

# Route pages
if selected == "Dashboard":
    dashboard_page()
elif selected == "Departments":
    departments_page()
elif selected == "Services":
    services_page()
elif selected == "Medicine Store":
    medicines_page()
elif selected == "My Appointments":
    if not st.session_state.is_admin:
        my_appointments_page()
    else:
        st.error("Admins cannot view this page")
elif selected == "Admin Panel":
    admin_panel()
elif selected == "About":
    about_page()

# Footer
st.divider()
st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>© 2024 MediCare Hub. All rights reserved.</p>
        <p>Disclaimer: This is a demo application. For real medical advice, consult a licensed healthcare provider.</p>
    </div>
""", unsafe_allow_html=True)
