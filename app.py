from flask import Flask, render_template, request, redirect, url_for, session, flash, Response
from datetime import datetime
import json
import os
import csv
from io import StringIO
from functools import wraps
import tempfile

# ------------------------------
# Vercel: Use environment variable for secret key
# ------------------------------
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# ------------------------------
# Vercel: JSON files go to /tmp (writable directory)
# ------------------------------
SERVICES_FILE = os.environ.get('SERVICES_FILE', os.path.join(tempfile.gettempdir(), 'services.json'))
APPOINTMENTS_FILE = os.environ.get('APPOINTMENTS_FILE', os.path.join(tempfile.gettempdir(), 'appointments.json'))

# ============ OOP CLASSES ============

class Service:
    def __init__(self, service_id, name, fee, description=""):
        self.__service_id = service_id
        self.__name = name
        self.__fee = fee
        self.__description = description
    
    def get_service_id(self):
        return self.__service_id
    def get_name(self):
        return self.__name
    def get_fee(self):
        return self.__fee
    def get_description(self):
        return self.__description
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
        self.__service_list = service_list
        self.__date_time = date_time
        self.__special_requests = special_requests
        self.__status = "Pending"
    
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
    def set_status(self, status):
        valid_statuses = ["Pending", "Ongoing", "Completed"]
        if status in valid_statuses:
            self.__status = status
    def set_date_time(self, date_time):
        self.__date_time = date_time
    def add_service(self, service):
        self.__service_list.append(service)
    def get_total_fee(self):
        return sum(service.get_fee() for service in self.__service_list)
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

# ============ DATA STORAGE (using /tmp on Vercel) ============

class DataManager:
    def __init__(self):
        self.services = []
        self.appointments = []
        self.next_service_id = 1
        self.next_appointment_id = 1
        self.load_data()
    
    def load_data(self):
        # Load services from SERVICES_FILE
        if os.path.exists(SERVICES_FILE):
            try:
                with open(SERVICES_FILE, 'r') as f:
                    services_data = json.load(f)
                    for s in services_data:
                        service = Service(s['service_id'], s['name'], s['fee'], s.get('description', ''))
                        self.services.append(service)
                        self.next_service_id = max(self.next_service_id, s['service_id'] + 1)
            except:
                pass
        
        # Load appointments from APPOINTMENTS_FILE
        if os.path.exists(APPOINTMENTS_FILE):
            try:
                with open(APPOINTMENTS_FILE, 'r') as f:
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
        
        if len(self.services) == 0:
            self.add_sample_data()
    
    def add_sample_data(self):
        self.add_service("Haircut", 250.00, "Basic haircut service")
        self.add_service("Hair Color", 1500.00, "Full hair coloring")
        self.add_service("Manicure", 300.00, "Nail cleaning and polishing")
        self.add_service("Pedicure", 350.00, "Foot spa and nail care")
        self.add_service("Facial", 800.00, "Deep cleansing facial")
        
        service1 = self.find_service_by_id(1)
        service2 = self.find_service_by_id(2)
        if service1 and service2:
            self.create_appointment("John Doe", [1, 2], "2024-12-15T10:00", "Please arrive on time")
        
        service3 = self.find_service_by_id(3)
        if service3:
            self.create_appointment("Jane Smith", [3], "2024-12-16T14:30", "")
    
    def save_data(self):
        services_data = [s.to_dict() for s in self.services]
        with open(SERVICES_FILE, 'w') as f:
            json.dump(services_data, f, indent=2)
        appointments_data = [a.to_dict() for a in self.appointments]
        with open(APPOINTMENTS_FILE, 'w') as f:
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

# ============ HELPER DECORATORS ============

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'admin':
            flash('Please login as admin first')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def user_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'user':
            flash('Please login as user first')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session or session.get('role') != 'staff':
            flash('Please login as staff first')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ============ FLASK ROUTES ============

data_manager = DataManager()

# Users database (added staff user)
users = {
    'admin': ['admin123', 'admin'],
    'user1': ['user123', 'user'],
    'gwapo': ['admin123', 'admin'],
    'pangit': ['user123', 'user'],
    'staff1': ['staff123', 'staff']
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
                
                role = users[username][1]
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'staff':
                    return redirect(url_for('staff_dashboard'))
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
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html', username=session['username'])

@app.route('/admin/services')
@admin_required
def admin_services():
    services = data_manager.get_all_services()
    return render_template('admin_services.html', services=services)

@app.route('/admin/service/add', methods=['POST'])
@admin_required
def add_service():
    name = request.form.get('name', '')
    fee = float(request.form.get('fee', 0))
    description = request.form.get('description', '')
    success, message = data_manager.add_service(name, fee, description)
    flash(message)
    return redirect(url_for('admin_services'))

@app.route('/admin/service/update/<int:service_id>', methods=['POST'])
@admin_required
def update_service(service_id):
    name = request.form.get('name', '')
    fee = float(request.form.get('fee', 0))
    description = request.form.get('description', '')
    success, message = data_manager.update_service(service_id, name, fee, description)
    flash(message)
    return redirect(url_for('admin_services'))

@app.route('/admin/service/delete/<int:service_id>')
@admin_required
def delete_service(service_id):
    success, message = data_manager.delete_service(service_id)
    flash(message)
    return redirect(url_for('admin_services'))

@app.route('/admin/appointments')
@admin_required
def admin_appointments():
    appointments = data_manager.get_all_appointments()
    return render_template('admin_appointments.html', appointments=appointments)

@app.route('/admin/appointment/update_status/<int:appointment_id>', methods=['POST'])
@admin_required
def update_appointment_status(appointment_id):
    status = request.form.get('status', 'Pending')
    success, message = data_manager.update_appointment_status(appointment_id, status)
    flash(message)
    return redirect(url_for('admin_appointments'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    return render_template('admin_reports.html')

@app.route('/admin/report/daily', methods=['POST'])
@admin_required
def daily_report():
    date = request.form.get('date', '')
    report = data_manager.get_daily_report(date)
    return render_template('admin_reports.html', daily_report=report)

@app.route('/admin/report/monthly', methods=['POST'])
@admin_required
def monthly_report():
    year = int(request.form.get('year', 2024))
    month = int(request.form.get('month', 1))
    report = data_manager.get_monthly_report(year, month)
    return render_template('admin_reports.html', monthly_report=report)

@app.route('/admin/daily_report', methods=['GET', 'POST'])
@admin_required
def daily_report_view():
    report = None
    if request.method == 'POST':
        date = request.form.get('date', '')
        if date:
            report = data_manager.get_daily_report(date)
    return render_template('daily_report_view.html', report=report)

@app.route('/admin/monthly_report', methods=['GET', 'POST'])
@admin_required
def monthly_report_view():
    report = None
    if request.method == 'POST':
        year = int(request.form.get('year', 2024))
        month = int(request.form.get('month', 1))
        report = data_manager.get_monthly_report(year, month)
    return render_template('monthly_report_view.html', report=report)

@app.route('/admin/export_daily_report')
@admin_required
def export_daily_report():
    date = request.args.get('date', '')
    if not date:
        flash('No date provided')
        return redirect(url_for('daily_report_view'))
    report = data_manager.get_daily_report(date)
    if report['total_appointments'] == 0:
        flash('No appointments for this date')
        return redirect(url_for('daily_report_view'))
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Appointment ID', 'Customer Name', 'Services', 'Date/Time', 'Status', 'Total Fee'])
    for apt in report['appointments']:
        cw.writerow([
            apt.get_appointment_id(),
            apt.get_customer_name(),
            ', '.join(s.get_name() for s in apt.get_service_list()),
            apt.get_date_time(),
            apt.get_status(),
            f"₱{apt.get_total_fee():.2f}"
        ])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename=daily_report_{date}.csv'})

@app.route('/admin/export_monthly_report')
@admin_required
def export_monthly_report():
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month:
        flash('Missing year/month')
        return redirect(url_for('monthly_report_view'))
    report = data_manager.get_monthly_report(year, month)
    if report['total_appointments'] == 0:
        flash('No appointments for this month')
        return redirect(url_for('monthly_report_view'))
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Service', 'Times Requested'])
    for service, count in report['service_summary'].items():
        cw.writerow([service, count])
    cw.writerow([])
    cw.writerow(['Total Appointments', report['total_appointments']])
    cw.writerow(['Total Fees', f"₱{report['total_fees']:.2f}"])
    output = si.getvalue()
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': f'attachment; filename=monthly_report_{year}_{month:02d}.csv'})

@app.route('/admin/service_history')
@admin_required
def admin_service_history():
    all_appointments = data_manager.get_all_appointments()
    completed_appointments = [a for a in all_appointments if a.get_status() == 'Completed']
    return render_template('service_history.html', appointments=completed_appointments)

# ============ STAFF ROUTES ============

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    return render_template('staff_dashboard.html', username=session['username'])

@app.route('/staff/appointments')
@staff_required
def staff_appointments():
    appointments = data_manager.get_all_appointments()
    return render_template('staff_appointments.html', appointments=appointments)

@app.route('/staff/update_status/<int:appointment_id>', methods=['POST'])
@staff_required
def staff_update_status(appointment_id):
    status = request.form.get('status')
    if status not in ['Pending', 'Ongoing', 'Completed']:
        flash('Invalid status')
        return redirect(url_for('staff_appointments'))
    
    success, message = data_manager.update_appointment_status(appointment_id, status)
    flash(message)
    
    if status == 'Completed' and success:
        flash('Appointment completed. Report has been recorded.')
        return redirect(url_for('staff_report_completion', appointment_id=appointment_id))
    
    return redirect(url_for('staff_appointments'))

@app.route('/staff/report_completion/<int:appointment_id>')
@staff_required
def staff_report_completion(appointment_id):
    appointment = data_manager.find_appointment_by_id(appointment_id)
    if not appointment:
        flash('Appointment not found')
        return redirect(url_for('staff_appointments'))
    
    report = {
        'appointment_id': appointment.get_appointment_id(),
        'customer': appointment.get_customer_name(),
        'services': [s.get_name() for s in appointment.get_service_list()],
        'total_fee': appointment.get_total_fee(),
        'date_time': appointment.get_date_time(),
        'status': appointment.get_status()
    }
    return render_template('staff_report_completion.html', report=report, appointment=appointment)

@app.route('/staff/service_history')
@staff_required
def staff_service_history():
    all_appointments = data_manager.get_all_appointments()
    completed_appointments = [a for a in all_appointments if a.get_status() == 'Completed']
    return render_template('service_history.html', appointments=completed_appointments)

# ============ USER ROUTES ============

@app.route('/user/dashboard')
@user_required
def user_dashboard():
    return render_template('user_dashboard.html', username=session['username'])

@app.route('/user/appointments')
@user_required
def user_appointments():
    appointments = data_manager.get_all_appointments()
    return render_template('user_appointments.html', appointments=appointments)

@app.route('/user/book_appointment', methods=['GET', 'POST'])
@user_required
def book_appointment():
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
@user_required
def track_appointment():
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
@user_required
def service_history():
    appointments = data_manager.get_all_appointments()
    completed_appointments = [a for a in appointments if a.get_status() == 'Completed']
    return render_template('service_history.html', appointments=completed_appointments)

if __name__ == '__main__':
    app.run(debug=True)