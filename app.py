from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import datetime
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ============ OOP CLASSES ============

class Service:
    def __init__(self, service_id, name, fee, description=""):
        self.__service_id = service_id
        self.__name = name
        self.__fee = fee
        self.__description = description
    
    # Getters
    def get_service_id(self):
        return self.__service_id
    
    def get_name(self):
        return self.__name
    
    def get_fee(self):
        return self.__fee
    
    def get_description(self):
        return self.__description
    
    # Setters
    def set_name(self, name):
        self.__name = name
    
    def set_fee(self, fee):
        if fee > 0:
            self.__fee = fee
    
    def set_description(self, description):
        self.__description = description
    
    def to_dict(self):
        return {
            'service_id': self.__service_id,
            'name': self.__name,
            'fee': self.__fee,
            'description': self.__description
        }
    
    def display(self):
        return f"ID: {self.__service_id} | Name: {self.__name} | Fee: ₱{self.__fee}"

class Appointment:
    def __init__(self, appointment_id, customer_name, service_list, date_time, special_requests=""):
        self.__appointment_id = appointment_id
        self.__customer_name = customer_name
        self.__service_list = service_list  # List of Service objects
        self.__date_time = date_time
        self.__special_requests = special_requests
        self.__status = "Pending"  # Pending, Ongoing, Completed
    
    # Getters
    def get_appointment_id(self):
        return self.__appointment_id
    
    def get_customer_name(self):
        return self.__customer_name
    
    def get_service_list(self):
        return self.__service_list
    
    def get_date_time(self):
        return self.__date_time
    
    def get_special_requests(self):
        return self.__special_requests
    
    def get_status(self):
        return self.__status
    
    # Setters
    def set_status(self, status):
        valid_statuses = ["Pending", "Ongoing", "Completed"]
        if status in valid_statuses:
            self.__status = status
    
    def set_date_time(self, date_time):
        self.__date_time = date_time
    
    def add_service(self, service):
        self.__service_list.append(service)
    
    def get_total_fee(self):
        total = sum(service.get_fee() for service in self.__service_list)
        return total
    
    def to_dict(self):
        return {
            'appointment_id': self.__appointment_id,
            'customer_name': self.__customer_name,
            'service_ids': [s.get_service_id() for s in self.__service_list],
            'date_time': self.__date_time,
            'special_requests': self.__special_requests,
            'status': self.__status,
            'total_fee': self.get_total_fee()
        }
    
    def display(self):
        services_str = ", ".join([s.get_name() for s in self.__service_list])
        return f"ID: {self.__appointment_id} | Customer: {self.__customer_name} | Services: {services_str} | Date: {self.__date_time} | Status: {self.__status}"

# ============ DATA STORAGE ============

class DataManager:
    def __init__(self):
        self.services = []
        self.appointments = []
        self.next_service_id = 1
        self.next_appointment_id = 1
        self.load_data()
    
    def load_data(self):
        # Load services
        if os.path.exists('services.json'):
            try:
                with open('services.json', 'r') as f:
                    services_data = json.load(f)
                    for s in services_data:
                        service = Service(s['service_id'], s['name'], s['fee'], s.get('description', ''))
                        self.services.append(service)
                        self.next_service_id = max(self.next_service_id, s['service_id'] + 1)
            except:
                pass
        
        # Load appointments
        if os.path.exists('appointments.json'):
            try:
                with open('appointments.json', 'r') as f:
                    appointments_data = json.load(f)
                    for a in appointments_data:
                        service_list = [self.find_service_by_id(sid) for sid in a['service_ids'] if self.find_service_by_id(sid)]
                        appointment = Appointment(a['appointment_id'], a['customer_name'], 
                                                service_list, a['date_time'], a.get('special_requests', ''))
                        appointment.set_status(a.get('status', 'Pending'))
                        self.appointments.append(appointment)
                        self.next_appointment_id = max(self.next_appointment_id, a['appointment_id'] + 1)
            except:
                pass
        
        # Add sample data if no data exists
        if len(self.services) == 0:
            self.add_sample_data()
    
    def add_sample_data(self):
        # Add sample services
        self.add_service("Haircut", 250.00, "Basic haircut service")
        self.add_service("Hair Color", 1500.00, "Full hair coloring")
        self.add_service("Manicure", 300.00, "Nail cleaning and polishing")
        self.add_service("Pedicure", 350.00, "Foot spa and nail care")
        self.add_service("Facial", 800.00, "Deep cleansing facial")
        
        # Add sample appointments
        service1 = self.find_service_by_id(1)
        service2 = self.find_service_by_id(2)
        if service1 and service2:
            self.create_appointment("John Doe", [1, 2], "2024-12-15T10:00", "Please arrive on time")
        if service3:
            self.create_appointment("Jane Smith", [3], "2024-12-16T14:30", "")
    
    def save_data(self):
        # Save services
        services_data = [s.to_dict() for s in self.services]
        with open('services.json', 'w') as f:
            json.dump(services_data, f, indent=2)
        
        # Save appointments
        appointments_data = [a.to_dict() for a in self.appointments]
        with open('appointments.json', 'w') as f:
            json.dump(appointments_data, f, indent=2)
    
    def add_service(self, name, fee, description=""):
        if fee <= 0:
            return False, "Service fee must be greater than zero"
        
        service = Service(self.next_service_id, name, fee, description)
        self.services.append(service)
        self.next_service_id += 1
        self.save_data()
        return True, "Service added successfully"
    
    def get_all_services(self):
        return self.services
    
    def find_service_by_id(self, service_id):
        for service in self.services:
            if service.get_service_id() == service_id:
                return service
        return None
    
    def update_service(self, service_id, name, fee, description=""):
        service = self.find_service_by_id(service_id)
        if service:
            if fee <= 0:
                return False, "Service fee must be greater than zero"
            service.set_name(name)
            service.set_fee(fee)
            service.set_description(description)
            self.save_data()
            return True, "Service updated successfully"
        return False, "Service not found"
    
    def delete_service(self, service_id):
        service = self.find_service_by_id(service_id)
        if service:
            self.services.remove(service)
            self.save_data()
            return True, "Service deleted successfully"
        return False, "Service not found"
    
    def create_appointment(self, customer_name, service_ids, date_time, special_requests=""):
        if not service_ids:
            return False, "Appointment must include at least one service"
        
        service_list = []
        for sid in service_ids:
            service = self.find_service_by_id(sid)
            if service:
                service_list.append(service)
        
        if not service_list:
            return False, "No valid services selected"
        
        appointment = Appointment(self.next_appointment_id, customer_name, 
                                service_list, date_time, special_requests)
        self.appointments.append(appointment)
        self.next_appointment_id += 1
        self.save_data()
        return True, f"Appointment created successfully! ID: {appointment.get_appointment_id()}"
    
    def get_all_appointments(self):
        return self.appointments
    
    def find_appointment_by_id(self, appointment_id):
        for appointment in self.appointments:
            if appointment.get_appointment_id() == appointment_id:
                return appointment
        return None
    
    def update_appointment_status(self, appointment_id, status):
        appointment = self.find_appointment_by_id(appointment_id)
        if appointment:
            appointment.set_status(status)
            self.save_data()
            return True, "Status updated successfully"
        return False, "Appointment not found"
    
    def get_daily_report(self, date):
        daily_appointments = [a for a in self.appointments if a.get_date_time().startswith(date)]
        total_appointments = len(daily_appointments)
        total_fees = sum(a.get_total_fee() for a in daily_appointments)
        
        # Get most requested service
        service_count = {}
        for appointment in daily_appointments:
            for service in appointment.get_service_list():
                service_name = service.get_name()
                service_count[service_name] = service_count.get(service_name, 0) + 1
        
        most_requested = max(service_count.items(), key=lambda x: x[1])[0] if service_count else "None"
        
        return {
            'date': date,
            'total_appointments': total_appointments,
            'total_fees': total_fees,
            'most_requested_service': most_requested,
            'appointments': daily_appointments
        }
    
    def get_monthly_report(self, year, month):
        monthly_appointments = [a for a in self.appointments 
                               if a.get_date_time().startswith(f"{year}-{month:02d}")]
        
        total_appointments = len(monthly_appointments)
        total_fees = sum(a.get_total_fee() for a in monthly_appointments)
        
        # Service summary
        service_summary = {}
        for appointment in monthly_appointments:
            for service in appointment.get_service_list():
                service_name = service.get_name()
                service_summary[service_name] = service_summary.get(service_name, 0) + 1
        
        return {
            'year': year,
            'month': month,
            'total_appointments': total_appointments,
            'total_fees': total_fees,
            'service_summary': service_summary
        }

# ============ FLASK ROUTES ============

data_manager = DataManager()

# Users database
users = {
    'admin': ['admin123', 'admin'],
    'user1': ['user123', 'user'],
    'gwapo': ['admin123', 'admin'],
    'pangit': ['user123', 'user']
}

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if username in users:
            if users[username][0] == password:
                session['username'] = username
                session['role'] = users[username][1]
                
                if users[username][1] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid password')
        else:
            flash('Invalid username')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))

# ============ ADMIN ROUTES ============

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Please login as admin first')
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html', username=session['username'])

# Service Management
@app.route('/admin/services')
def admin_services():
    if 'username' not in session or session.get('role') != 'admin':
        flash('Please login as admin first')
        return redirect(url_for('login'))
    services = data_manager.get_all_services()
    return render_template('admin_services.html', services=services)

@app.route('/admin/service/add', methods=['POST'])
def add_service():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    name = request.form.get('name', '')
    fee = float(request.form.get('fee', 0))
    description = request.form.get('description', '')
    
    success, message = data_manager.add_service(name, fee, description)
    flash(message)
    return redirect(url_for('admin_services'))

@app.route('/admin/service/update/<int:service_id>', methods=['POST'])
def update_service(service_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    name = request.form.get('name', '')
    fee = float(request.form.get('fee', 0))
    description = request.form.get('description', '')
    
    success, message = data_manager.update_service(service_id, name, fee, description)
    flash(message)
    return redirect(url_for('admin_services'))

@app.route('/admin/service/delete/<int:service_id>')
def delete_service(service_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    success, message = data_manager.delete_service(service_id)
    flash(message)
    return redirect(url_for('admin_services'))

# Appointment Management for Admin
@app.route('/admin/appointments')
def admin_appointments():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    appointments = data_manager.get_all_appointments()
    return render_template('admin_appointments.html', appointments=appointments)

@app.route('/admin/appointment/update_status/<int:appointment_id>', methods=['POST'])
def update_appointment_status(appointment_id):
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    status = request.form.get('status', 'Pending')
    success, message = data_manager.update_appointment_status(appointment_id, status)
    flash(message)
    return redirect(url_for('admin_appointments'))

# Reports for Admin
@app.route('/admin/reports')
def admin_reports():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_reports.html')

@app.route('/admin/report/daily', methods=['POST'])
def daily_report():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    date = request.form.get('date', '')
    report = data_manager.get_daily_report(date)
    return render_template('admin_reports.html', daily_report=report)

@app.route('/admin/report/monthly', methods=['POST'])
def monthly_report():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    
    year = int(request.form.get('year', 2024))
    month = int(request.form.get('month', 1))
    report = data_manager.get_monthly_report(year, month)
    return render_template('admin_reports.html', monthly_report=report)

# ============ USER ROUTES ============

@app.route('/user/dashboard')
def user_dashboard():
    if 'username' not in session or session.get('role') != 'user':
        flash('Please login as user first')
        return redirect(url_for('login'))
    return render_template('user_dashboard.html', username=session['username'])

@app.route('/user/appointments')
def user_appointments():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    appointments = data_manager.get_all_appointments()
    return render_template('user_appointments.html', appointments=appointments)

@app.route('/user/book_appointment', methods=['GET', 'POST'])
def book_appointment():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        customer_name = request.form.get('customer_name', '')
        service_ids = [int(sid) for sid in request.form.getlist('service_ids')]
        date_time = request.form.get('date_time', '')
        special_requests = request.form.get('special_requests', '')
        
        success, message = data_manager.create_appointment(customer_name, service_ids, date_time, special_requests)
        flash(message)
        if success:
            return redirect(url_for('user_appointments'))
    
    services = data_manager.get_all_services()
    return render_template('book_appointment.html', services=services)

@app.route('/user/track_appointment', methods=['GET', 'POST'])
def track_appointment():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    
    appointment = None
    if request.method == 'POST':
        appointment_id = request.form.get('appointment_id')
        if appointment_id:
            appointment = data_manager.find_appointment_by_id(int(appointment_id))
            if not appointment:
                flash('Appointment not found')
    elif request.method == 'GET':
        appointment_id = request.args.get('appointment_id')
        if appointment_id:
            appointment = data_manager.find_appointment_by_id(int(appointment_id))
    
    return render_template('track_appointment.html', appointment=appointment)

@app.route('/user/service_history')
def service_history():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    
    appointments = data_manager.get_all_appointments()
    completed_appointments = [a for a in appointments if a.get_status() == 'Completed']
    return render_template('service_history.html', appointments=completed_appointments)

if __name__ == '__main__':
    app.run(debug=True)