from flask import Flask, render_template, redirect, request, url_for, session, flash, abort
from flask_login import login_required, current_user, login_user, logout_user,login_manager
from collections import Counter
from flask import current_app as app
# from sqlalchemy.orm import joinedload
from datetime import datetime,date
from .models import *
import matplotlib  # type: ignore
import matplotlib.ticker as ticker # type: ignore
import matplotlib.pyplot as plt # type: ignore
matplotlib.use("Agg")

# ------ADMIN-------
# Home Route
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html')

#ADMIN LOGIN
@app.route('/adminlogin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        this_admin = Admin.query.filter_by(username=u_name).first()
        if not this_admin:
            return render_template('admin_login.html', error="Admin does not exist.")
        if this_admin.password != pwd:
            return render_template('admin_login.html', error="Incorrect password.")
        #Include Admin Dashboard Functiolity later
        doctors = Doctor.query.all()
        departments = Department.query.all()
        login_user(this_admin)
        admin_name = this_admin.username
        return render_template('admin_dashboard.html', doctors=doctors, departments=departments, admin_name=admin_name)
    return render_template('admin_login.html')

#ADMIN LOGOUT
@app.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    return render_template('admin_login.html')

# Patient Registration and Login

#PATIENT REGISTER
@app.route('/patientregister' , methods = ['GET','POST'])
def patient_reg():
    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        name = request.form.get("name")
        age = int(request.form.get("age"))
        gender = request.form.get("gender")
        contact = int(request.form.get("contact"))
        address = request.form.get("address")
        medical_history = request.form.get("medical_history")
        if not (u_name and pwd and name and age and gender and contact and address and medical_history):
            return render_template('patient_register.html', message="Please fill out all fields and try again.Pls put NA as applicable")
        
        this_patient = Patient.query.filter_by(username = u_name).first()
        if this_patient:
            return "This Patient already exists"
        else:
            new_user = User(username = u_name, user_role = 2)
            db.session.add(new_user)
            db.session.commit()
            new_patient = Patient(username = u_name, password = pwd, name = name, age = age, gender = gender, address = address, contact_num = contact, medical_history = medical_history, patient_id = new_user.id)
            db.session.add(new_patient)
            db.session.commit()

            return redirect('/patientlogin')
    return render_template('patient_register.html')


#PATIENT LOGIN
@app.route('/patientlogin', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        this_patient = User.query.filter_by(username=u_name).first()
        if not this_patient:
            return render_template('patient_login.html', error="This patient does not exist.")
        if not Patient.query.filter_by(patient_id=this_patient.id, password=pwd).first():
            return render_template('patient_login.html', error="Incorrect password.")
        patient = Patient.query.filter_by(patient_id=this_patient.id).first()
        if patient.flagged == 1:
            return render_template('patient_login.html', error="Your account has been flagged and you cannot log in.")
        if this_patient.user_role == 2:
            login_user(this_patient)     
           
            return render_template('patient_dashboard.html', u_name=u_name, id=User.id)
    
    return render_template('patient_login.html')

#DOCTOR LOGIN
@app.route('/doctorlogin', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        this_doctor = User.query.filter_by(username=u_name).first()
        if not this_doctor:
            return render_template('doctor_login.html', error="This doctor does not exist.")
        if not Doctor.query.filter_by(doctor_id=this_doctor.id, password=pwd).first():
            return render_template('doctor_login.html', error="Incorrect password.")
        doctor = Doctor.query.filter_by(doctor_id=this_doctor.id).first()
        if doctor.flagged == 1:
            return render_template('doctor_login.html', error="Your account has been flagged and you cannot log in.")
        if this_doctor.user_role == 1:
            login_user(this_doctor)     
           
            return render_template('doctor_dashboard.html', u_name=u_name, id=User.id)
    
    return render_template('doctor_login.html')

# Create Departments
@app.route('/createdept', methods=['GET', 'POST'])
@login_required

def create_dept():
    # Only Admin can access
    if current_user.user_role != 0:
        return render_template('create_department.html', error = "Access denied, Only Admins can create Departments")
    else:
        if request.method == 'POST':
            name = request.form.get("name")
            desc = request.form.get("desc")
            this_dep = Department.query.filter_by(name = name).first()
            if this_dep:
               return render_template('create_department.html', error = "This Department Already Exists")
            else:
                new_dept = Department(name = name, description = desc)
                db.session.add(new_dept)
                db.session.commit()
                doctors = Doctor.query.all()
                departments = Department.query.all()
                admin_name = current_user.username
                return render_template('admin_dashboard.html', doctors=doctors, departments=departments, admin_name=admin_name)
    return render_template('create_department.html')

# ----------------------------------------------------------
# CREATE DOCTOR ROUTE (Admin Only)
# ----------------------------------------------------------

@app.route('/createdoctor', methods=['GET', 'POST'])
@login_required
def create_doctor():
    # Access control: Only Admin
    if current_user.user_role != 0:
        return render_template('create_doctor.html', error="Access denied, Only Admins can create Doctors")

    # Fetch departments for dropdown
    departments = Department.query.all()

    if request.method == 'POST':
        u_name = request.form.get("u_name")
        pwd = request.form.get("pwd")
        name = request.form.get("name")
        qual = request.form.get("qual")
        exp = request.form.get("exp")
        fee = request.form.get("fee")
        specialization = request.form.get("specialization")
        desig = request.form.get("desig")
        reg_num = request.form.get("reg_num")
        dep_id = request.form.get("dep_id")

        # Validate duplicates
        existing_user = User.query.filter_by(username=u_name).first()
        existing_reg = Doctor.query.filter_by(registration_num=reg_num).first()

        if existing_user:
            return render_template('create_doctor.html', error="Username already exists", departments=departments)
        if existing_reg:
            return render_template('create_doctor.html', error="Registration number already exists", departments=departments)

        # Create User entry
        new_user = User(username=u_name, user_role=1)  # 1 = Doctor
        db.session.add(new_user)
        db.session.commit()  # Commit first to generate user ID

        # Create Doctor entry
        new_doctor = Doctor(
            username=u_name,
            password=pwd,
            name=name,
            qualification=qual,
            experience=int(exp),
            fee=int(fee),
            flagged=0,
            specialization=specialization,
            designation=desig,
            registration_num=reg_num,
            doctor_id=new_user.id,
            department_id=int(dep_id)
        )

        db.session.add(new_doctor)
        db.session.commit()
        doctors = Doctor.query.all()
        departments = Department.query.all()
        admin_name = current_user.username

        return render_template('admin_dashboard.html', doctors=doctors, departments=departments, admin_name=admin_name)

    return render_template('create_doctor.html', departments=departments)

# ----------------------------------------------------------
# EDIT DOCTOR ROUTE (Admin Only)
# ----------------------------------------------------------

@app.route('/editdoctor/<int:doctor_id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(doctor_id):
    # Access control: Only Admin
    if current_user.user_role != 0:
        return render_template('edit_doctor.html', error="Access denied, Only Admins can edit Doctors")

    # Fetch doctor and departments
    doctor = Doctor.query.get_or_404(doctor_id)
    departments = Department.query.all()

    if request.method == 'POST':
        name = request.form.get("name")
        qual = request.form.get("qual")
        exp = request.form.get("exp")
        fee = request.form.get("fee")
        specialization = request.form.get("specialization")
        desig = request.form.get("desig")
        reg_num = request.form.get("reg_num")
        dep_id = request.form.get("dep_id")
        pwd = request.form.get("pwd")

        # Validation: registration number duplicate
        existing_reg = Doctor.query.filter(
            Doctor.registration_num == reg_num,
            Doctor.id != doctor_id
        ).first()
        if existing_reg:
            return render_template(
                'edit_doctor.html',
                doctor=doctor,
                departments=departments,
                error="Registration number already exists"
            )

        # Update doctor details
        doctor.name = name
        doctor.qualification = qual
        doctor.experience = int(exp)
        doctor.fee = int(fee)
        doctor.specialization = specialization
        doctor.designation = desig
        doctor.registration_num = reg_num
        doctor.department_id = int(dep_id)

        if pwd:  # Update password only if entered
            doctor.password = pwd

        db.session.commit()

        return redirect('/admindoctors')  # redirect to doctors list page

    return render_template('edit_doctor.html', doctor=doctor, departments=departments)


#ADMIN DASHBOARD
@app.route("/admindashboard")
def admin_dashboard():
    doctors = Doctor.query.all()
    departments = Department.query.all()
    admin_name = current_user.username
    return render_template("admin_dashboard.html", doctors=doctors, departments=departments, admin_name=admin_name)


#DELETE DOCTOR ROUTE (Admin Only)
@app.route('/deletedoctor/<int:doctor_id>', methods=['POST'])
@login_required
def delete_doctor(doctor_id):
    # Access control: Only Admin
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can delete Doctors")

    doctor = Doctor.query.get_or_404(doctor_id)
    user = User.query.get(doctor.doctor_id)

    db.session.delete(doctor)
    if user:
        db.session.delete(user)
    db.session.commit()

    return redirect('/admindashboard')  # redirect to admin dashboard

#DELTETE DEPARTMENT ROUTE (Admin Only)
@app.route('/deletedepartment/<int:department_id>', methods=['POST'])
@login_required
def delete_department(department_id):
    # Access control: Only Admin
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can delete Departments")

    department = Department.query.get_or_404(department_id)
    db.session.delete(department)
    db.session.commit()

    return redirect('/admindashboard')  # redirect to admin dashboard

#EDIT DEPARTMENT ROUTE (Admin Only)
@app.route('/editdepartment/<int:department_id>', methods=['GET', 'POST'])
@login_required
def edit_department(department_id):
    # Access control: Only Admin
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can edit Departments")

    department = Department.query.get_or_404(department_id)

    if request.method == 'POST':
        name = request.form.get("name")
        desc = request.form.get("desc")

        # Update department details
        department.name = name
        department.description = desc

        db.session.commit()

        return redirect('/admindashboard')  # redirect to admin dashboard

    return render_template('edit_department.html', department=department)


