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
        login_user(this_admin)
        return render_template('admin_dashboard.html', current_user=u_name, u_name=u_name)                               
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