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

# ADMIN LOGIN
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

        login_user(this_admin)
        return redirect(url_for('admin_dashboard'))  

    return render_template('admin_login.html')
# Admin Search
@app.route('/adminsearch')
@login_required
def admin_search():
    # Only Admin can access
    if current_user.user_role != 0:
        abort(403)

    query = request.args.get('q', '').strip()

    doctors = Doctor.query.filter(Doctor.name.ilike(f"%{query}%")).all()
    patients = Patient.query.filter(Patient.name.ilike(f"%{query}%")).all()
    departments = Department.query.filter(Department.name.ilike(f"%{query}%")).all()

    return render_template(
        'admin_search.html',
        query=query,
        doctors=doctors,
        patients=patients,
        departments=departments
    )


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
            return redirect(url_for('patient_dashboard'))  # ✅ Redirect instead of rendering directly

    return render_template('patient_login.html')


# Patient Dashboard
@app.route('/patientdashboard')
@login_required
def patient_dashboard():

    if current_user.user_role != 2:
        return render_template('patient_login.html', error="Access denied.")

    patient = Patient.query.filter_by(username=current_user.username).first()

    # ALL appointments
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()

    # --- UPCOMING appointments only ---
    today = datetime.today().date()
    upcoming_appointments = Appointment.query.filter(
        Appointment.patient_id == patient.id,
        Appointment.status == "Booked",
        Appointment.appointment_date >= today
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    # TREATMENT HISTORY
    treatment_history = Appointment.query.join(Treatment).filter(
        Appointment.patient_id == patient.id
    ).order_by(Appointment.appointment_date.desc()).all()

    departments = Department.query.all()

    return render_template(
        'patient_dashboard.html',
        patient=patient,
        appointments=appointments,
        upcoming_appointments=upcoming_appointments,     
        departments=departments,
        treatment_history=treatment_history,
        current_date=datetime.today()
    )


from sqlalchemy.orm import joinedload

# ----------------------------------------------------------
# PATIENT HISTORY PAGE (View complete medical history)
# ----------------------------------------------------------
@app.route('/patient/history')
@login_required
def patient_history_page():

    # # Only patients can access this
    # if current_user.user_role != 2:
    #     abort(403)

    patient = Patient.query.filter_by(username=current_user.username).first()

    # ✔ Load Treatment + Appointment + Doctor together (fixes date & time missing)
    history = (
        Treatment.query
        .options(
            joinedload(Treatment.appointment).joinedload(Appointment.doctor)
        )
        .join(Appointment, Treatment.treatment_id == Appointment.id)
        .filter(Appointment.patient_id == patient.id)
        .order_by(
            Appointment.appointment_date.desc(),
            Appointment.appointment_time.desc()
        )
        .all()
    )

    return render_template(
        'patient_history.html',
        patient=patient,
        history=history
    )


# Patient Self  Edit Profile for Themselves
@app.route('/patient/edit', methods=['GET', 'POST'])
@login_required
def patient_edit_self():
    # Only patients can access
    if current_user.user_role != 2:
        return redirect(url_for('patient_login'))

    patient = Patient.query.filter_by(username=current_user.username).first()

    if request.method == 'POST':
        patient.name = request.form.get("name")
        patient.age = request.form.get("age")
        patient.gender = request.form.get("gender")
        patient.address = request.form.get("address")
        patient.contact_num = request.form.get("contact_num")
        patient.medical_history = request.form.get("medical_history")

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('patient_dashboard'))

    return render_template("patient_edit_profile.html", patient=patient)


# ----------------------------------------------------------
# EDIT PATIENT (Admin Only)
# ----------------------------------------------------------
@app.route('/editpatient/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def edit_patient(patient_id):
    # Only admins allowed
    if current_user.user_role != 0:
        abort(403)

    patient = Patient.query.get_or_404(patient_id)

    if request.method == 'POST':
        # Fetch updated data from form
        patient.name = request.form.get("name")
        patient.age = int(request.form.get("age") or patient.age)
        patient.gender = request.form.get("gender")
        patient.address = request.form.get("address")
        patient.contact_num = int(request.form.get("contact_num") or patient.contact_num)
        patient.medical_history = request.form.get("medical_history")

        db.session.commit()
        flash("Patient profile updated successfully!", "success")
        return redirect(url_for('admin_dashboard'))

    return render_template('edit_patient.html', patient=patient)


# ----------------------------------------------------------
# BOOK APPOINTMENT (Patient selects Department → Doctor → Slot)
# ----------------------------------------------------------
from datetime import datetime
from flask import jsonify

@app.route('/bookappointment', methods=['GET', 'POST'])
@login_required
def book_appointment():
    # ✅ Access control: Only patients
    if current_user.user_role != 2:
        return render_template('patient_login.html', error="Access denied. Only patients can book appointments.")

    patient = Patient.query.filter_by(username=current_user.username).first()
    departments = Department.query.all()  # All available departments

    # STEP 1️⃣ — Handle GET (show dropdowns)
    if request.method == 'GET':
        return render_template(
            'book_appointment.html',
            patient=patient,
            departments=departments,
            doctors=[],
            slots=[]
        )

    # STEP 2️⃣ — Handle POST (form submissions)
    selected_department = request.form.get("department_id")
    selected_doctor = request.form.get("doctor_id")
    selected_slot = request.form.get("slot_id")

    # 🔹 If department selected but no doctor yet — show doctors
    if selected_department and not selected_doctor:
        doctors = Doctor.query.filter_by(department_id=selected_department).all()
        return render_template(
            'book_appointment.html',
            patient=patient,
            departments=departments,
            selected_department=int(selected_department),
            doctors=doctors,
            slots=[]
        )

    # 🔹 If doctor selected but no slot yet — show available slots
    if selected_doctor and not selected_slot:
        today = datetime.today().date()
        slots = Appointment.query.filter(
            Appointment.doctor_id == selected_doctor,
            Appointment.appointment_date >= today,
            Appointment.status == "Available"
        ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

        doctors = Doctor.query.filter_by(department_id=selected_department).all()
        return render_template(
            'book_appointment.html',
            patient=patient,
            departments=departments,
            selected_department=int(selected_department),
            doctors=doctors,
            selected_doctor=int(selected_doctor),
            slots=slots
        )

    # 🔹 If slot selected — confirm booking
    if selected_slot:
        slot = Appointment.query.get_or_404(selected_slot)
        slot.patient_id = patient.id
        slot.status = "Booked"
        slot.reason = "Booked by patient"
        db.session.commit()

        flash("Appointment booked successfully!", "success")
        return redirect(url_for('patient_dashboard'))

    # Fallback (should not happen)
    return redirect(url_for('book_appointment'))

# ----------------------------------------------------------
# CANCEL APPOINTMENT (Patient Only – Only Future Appointments)
# ----------------------------------------------------------
@app.route('/cancelappointment/<int:appt_id>', methods=['POST'])
@login_required
def cancel_appointment(appt_id):

    # Only patients should use this
    if current_user.user_role != 2:
        abort(403)

    patient = Patient.query.filter_by(username=current_user.username).first()
    appointment = Appointment.query.get_or_404(appt_id)

    # Safety checks
    if appointment.patient_id != patient.id:
        abort(403)  # Cannot cancel someone else's appointment

    # Must be a BOOKED upcoming appointment
    today = datetime.today()
    if appointment.appointment_date < today:
        flash("You cannot cancel past appointments.", "danger")
        return redirect(url_for('patient_dashboard'))

    if appointment.status != "Booked":
        flash("Only booked appointments can be cancelled.", "warning")
        return redirect(url_for('patient_dashboard'))

    # Perform cancellation → free the slot again
    appointment.status = "Available"
    appointment.patient_id = 999  # Default empty patient id
    appointment.reason = "Cancelled by patient"

    db.session.commit()

    flash("Your appointment has been cancelled successfully.", "success")
    return redirect(url_for('patient_dashboard'))




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
           
            return redirect(url_for('doctor_dashboard'))
  
    return render_template('doctor_login.html')

# ----------------------------------------------------------
# DOCTOR DASHBOARD
# ----------------------------------------------------------
@app.route('/doctordashboard')
@login_required
def doctor_dashboard():
    # Restrict access only to doctors
    if current_user.user_role != 1:
        return render_template('doctor_login.html', error="Access denied. Only doctors can access this page.")

    # Logged-in doctor record
    doctor = Doctor.query.filter_by(username=current_user.username).first()

    # Upcoming appointments only
    today = datetime.today().date()
    upcoming_appointments = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.status.in_(["Booked"])
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    # Assigned patients list (distinct)
    assigned_patients = (
        Patient.query.join(Appointment, Appointment.patient_id == Patient.id)
        .filter(Appointment.doctor_id == doctor.id)
        .distinct()
        .all()
    )

    return render_template(
        'doctor_dashboard.html',
        doctor=doctor,
        upcoming_appointments=upcoming_appointments,
        assigned_patients=assigned_patients
    )
# MARK APPOINTMENT AS COMPLETED (Doctor Only)
@app.route('/doctor/complete/<int:appt_id>', methods=['POST'])
@login_required
def mark_completed(appt_id):
    if current_user.user_role != 1:
        abort(403)

    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "Completed"
    db.session.commit()

    flash("Appointment marked as completed!", "success")
    return redirect(url_for('doctor_dashboard'))

# ----------------------------------------------------------
# Cancel APPOINTMENT (Doctor Only)
# ----------------------------------------------------------
@app.route('/doctor/cancel/<int:appt_id>', methods=['POST'])
@login_required
def doctor_cancel_appointment(appt_id):
    if current_user.user_role != 1:
        abort(403)

    appt = Appointment.query.get_or_404(appt_id)
    appt.status = "Cancelled"
    db.session.commit()

    flash("Appointment cancelled.", "danger")
    return redirect(url_for('doctor_dashboard'))

# ----------------------------------------------------------
# Update Patient History (Doctor Only)
# ----------------------------------------------------------    
@app.route('/doctor/update_history/<int:appt_id>', methods=['GET', 'POST'])
@login_required
def update_history(appt_id):
    # if current_user.user_role != 1:
    #     abort(403)

    appt = Appointment.query.get_or_404(appt_id)

    if request.method == 'POST':
        # Fetch fields
        visit_type = request.form.get("visit_type")
        test_done = request.form.get("test_done")
        diagnosis = request.form.get("diagnosis")
        prescription = request.form.get("prescription")
        notes = request.form.get("notes")

        medicine1 = request.form.get("medicine1")
        medicine2 = request.form.get("medicine2")
        medicine3 = request.form.get("medicine3")

        # Combine all data into a readable string
        combined_notes = f"""
Visit Type: {visit_type}
Test Done: {test_done}

Diagnosis:
{diagnosis}

Prescription:
{prescription}

Medicines:
- {medicine1}
- {medicine2}
- {medicine3}

Additional Notes:
{notes}
        """.strip()

        # Save Treatment
        treatment = Treatment(
            diagnosis=diagnosis,
            prescription=prescription,
            notes=combined_notes,
            treatment_id=appt.id
        )
        db.session.add(treatment)

        # Mark appointment completed
        appt.status = "Completed"
        db.session.commit()

        flash("Patient history updated successfully!", "success")
        return redirect(url_for('doctor_dashboard'))

    return render_template('update_history.html', appt=appt)


# ----------------------------------------------------------
# view PATIENT History (Doctor Only)
# ----------------------------------------------------------
@app.route('/doctor/patient_history/<int:patient_id>')
@login_required
def doctor_patient_history(patient_id):
    # if current_user.user_role != 1:
    #    abort(403)

    patient = Patient.query.get_or_404(patient_id)

    history = (
        Treatment.query
        .join(Appointment, Treatment.treatment_id == Appointment.id)
        .filter(Appointment.patient_id == patient.id)
        .all()
    )

    return render_template('doctor_patient_history.html',
                           patient=patient,
                           history=history)

# ----------------------------------------------------------
# PATIENT SEARCH (Patients can search Doctors or Departments)
# ----------------------------------------------------------
@app.route('/patientsearch')
@login_required
def patient_search():
    if current_user.user_role != 2:
        abort(403)

    query = request.args.get('q', '').strip()

    # Search doctors by name OR specialization
    doctors = Doctor.query.filter(
        (Doctor.name.ilike(f"%{query}%")) |
        (Doctor.specialization.ilike(f"%{query}%"))
    ).all()

    # Search departments for convenience (optional)
    departments = Department.query.filter(
        Department.name.ilike(f"%{query}%")
    ).all()

    return render_template(
        'patient_search.html',
        query=query,
        doctors=doctors,
        departments=departments
    )



# ----------------------------------------------------------
# DOCTOR AVAILABILITY (Patient View)
# ----------------------------------------------------------
@app.route('/doctor/<int:doctor_id>/availability')
@login_required
def doctor_availability(doctor_id):

    # Only patients can access
    if current_user.user_role != 2:
        abort(403)

    doctor = Doctor.query.get_or_404(doctor_id)
    this_doctor = User.query.filter_by(id=doctor.doctor_id).first()

    # Upcoming available slots
    today = date.today()
    slots = Appointment.query.filter(
        Appointment.doctor_id == this_doctor.id,
        Appointment.status == "Available",
        Appointment.appointment_date >= today
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    return render_template(
        'doctor_availability.html',
        doctor=doctor,
        slots=slots
    )





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
                # Use PRG pattern and ensure consistent dashboard context
                return redirect(url_for('admin_dashboard'))
    return render_template('create_department.html')


@app.route('/createdoctor', methods=['GET', 'POST'])
@login_required
def create_doctor():
    if current_user.user_role != 0:
        return render_template('create_doctor.html', error="Access denied, Only Admins can create Doctors")
   
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

     
        new_user = User(username=u_name, user_role=1)  # 1 = Doctor
        db.session.add(new_user)
        db.session.commit()  

       
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
        # Use PRG pattern and ensure consistent dashboard context
        return redirect(url_for('admin_dashboard'))

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
from datetime import date

@app.route("/admindashboard")
@login_required
def admin_dashboard():
    if current_user.user_role != 0:
        abort(403)

    doctors = Doctor.query.all()
    departments = Department.query.all()
    patients = Patient.query.all()

    today = date.today()

    upcoming_appointments = Appointment.query.filter(
        Appointment.appointment_date >= today,
        Appointment.status == "Booked"
    ).order_by(Appointment.appointment_date, Appointment.appointment_time).all()

    past_appointments = Appointment.query.filter(
        Appointment.appointment_date < today
    ).order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc()).all()

    totals = {
        "doctors": len(doctors),
        "patients": len(patients),
        "departments": len(departments),
        "appointments": Appointment.query.count(),
    }

    return render_template(
        "admin_dashboard.html",
        admin_name=current_user.username,
        doctors=doctors,
        departments=departments,
        patients=patients,
        totals=totals,
        upcoming_appointments=upcoming_appointments,
        past_appointments=past_appointments
    )



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


# ----------------------------------------------------------
# FLAG / UNFLAG DOCTOR (Admin Only)
# ----------------------------------------------------------

@app.route('/flagdoctor/<int:doctor_id>', methods=['POST'])
@login_required
def flag_doctor(doctor_id):
    # Only Admins allowed
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can flag Doctors")

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.flagged = 1
    db.session.commit()

    flash(f"Doctor '{doctor.name}' has been flagged and cannot log in.", "warning")
    return redirect(url_for('admin_dashboard'))


@app.route('/unflagdoctor/<int:doctor_id>', methods=['POST'])
@login_required
def unflag_doctor(doctor_id):
    # Only Admins allowed
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can unflag Doctors")

    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.flagged = 0
    db.session.commit()

    flash(f"Doctor '{doctor.name}' has been unflagged and can now log in.", "success")
    return redirect(url_for('admin_dashboard'))

# ----------------------------------------------------------
# FLAG / UNFLAG PATIENT (Admin Only)
# ----------------------------------------------------------

@app.route('/flagpatient/<int:patient_id>', methods=['POST'])
@login_required
def flag_patient(patient_id):
    # Only Admins allowed
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can flag Patients")

    patient = Patient.query.get_or_404(patient_id)
    patient.flagged = 1
    db.session.commit()

    flash(f"Patient '{patient.name}' has been flagged and cannot log in.", "warning")
    return redirect(url_for('admin_dashboard'))


@app.route('/unflagpatient/<int:patient_id>', methods=['POST'])
@login_required
def unflag_patient(patient_id):
    # Only Admins allowed
    if current_user.user_role != 0:
        return render_template('admin_dashboard.html', error="Access denied, Only Admins can unflag Patients")

    patient = Patient.query.get_or_404(patient_id)
    patient.flagged = 0
    db.session.commit()

    flash(f"Patient '{patient.name}' has been unflagged and can now log in.", "success")
    return redirect(url_for('admin_dashboard'))
# ----------------------------------------------------------
# DOCTOR APPOINTMENT AVAILABILITY (Morning & Evening Slots)
# ----------------------------------------------------------
from datetime import datetime, timedelta, time

@app.route('/appointment', methods=['GET', 'POST'])
@login_required
def appointment():
    # ✅ Access control: Only doctors
    if current_user.user_role != 1:
        return render_template(
            'doctor_login.html',
            error="Access denied. Only doctors can manage appointments."
        )

    # ✅ Get doctor details
    doctor = Doctor.query.filter_by(username=current_user.username).first()

    today = datetime.today().date()
    next_7_days = [today + timedelta(days=i) for i in range(7)]

    # Define fixed slots
    morning_start, morning_end = time(8, 0), time(12, 0)
    evening_start, evening_end = time(16, 0), time(21, 0)
    slot_duration = timedelta(minutes=45)

    if request.method == 'POST':
        selected_mornings = request.form.getlist('morning')
        selected_evenings = request.form.getlist('evening')

        # ✅ Delete old available slots for next 7 days
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date >= today,
            Appointment.status == "Available"
        ).delete()

        # ✅ Create slots for selected sessions
        for date_str in next_7_days:
            # Ensure date_str is a datetime.date, not datetime
            if isinstance(date_str, datetime):
                date_only = date_str.date()
            else:
                date_only = date_str

            day_str = date_only.strftime("%Y-%m-%d")

            # Morning slot generation
            if day_str in selected_mornings:
                current_dt = datetime.combine(date_only, morning_start)
                while current_dt < datetime.combine(date_only, morning_end):
                    db.session.add(Appointment(
                        appointment_date=date_only,  
                        appointment_time=current_dt.time().replace(second=0, microsecond=0),  
                        status="Available",
                        reason="Morning Slot",
                        doctor_id=doctor.id
                    ))
                    current_dt += slot_duration


            # Evening slot generation
            if day_str in selected_evenings:
                current_dt = datetime.combine(date_str, evening_start)
                while current_dt < datetime.combine(date_str, evening_end):
                    db.session.add(Appointment(
                        appointment_date=date_str,
                        appointment_time=current_dt.time(),
                        status="Available",
                        reason="Evening Slot",
                        doctor_id=doctor.id
                    ))
                    current_dt += slot_duration

        db.session.commit()
        flash("Availability updated successfully!", "success")
        return redirect(url_for('doctor_dashboard'))

    # ✅ Pre-select existing availability
    existing = Appointment.query.filter(
        Appointment.doctor_id == doctor.id,
        Appointment.appointment_date >= today,
        Appointment.status == "Available"
    ).all()

    morning_dates = {a.appointment_date for a in existing if a.appointment_time < time(12, 0)}
    evening_dates = {a.appointment_date for a in existing if a.appointment_time >= time(16, 0)}

    return render_template(
        'appointment.html',
        doctor=doctor,
        next_7_days=next_7_days,
        morning_dates=morning_dates,
        evening_dates=evening_dates
    )
# ----------------------------------------------------------
# DEPARTMENT DETAILS (Patient View)
# ----------------------------------------------------------
@app.route('/department/<int:dep_id>')
@login_required
def department_details(dep_id):
    # Only Patients should access
    if current_user.user_role != 2:
        return render_template('patient_login.html', error="Access denied. Only patients can view departments.")

    department = Department.query.get_or_404(dep_id)
    doctors = Doctor.query.filter_by(department_id=dep_id).all()

    return render_template('department_details.html', department=department, doctors=doctors)

@app.route('/patient_history/<int:patient_id>')
@login_required
def patient_history(patient_id):
    # if current_user.user_role != 1:
    #    abort(403)

    patient = Patient.query.get_or_404(patient_id)

    history = (
        Treatment.query
        .join(Appointment, Treatment.treatment_id == Appointment.id)
        .filter(Appointment.patient_id == patient.id)
        .all()
    )

    return render_template('patient_history_admin.html',
                           patient=patient,
                           history=history)

@app.route('/doctor/<int:doctor_id>')
@login_required
def doctor_details(doctor_id):

    # Only patients can view doctor details
    if current_user.user_role != 2:
        abort(403)

    doctor = Doctor.query.get_or_404(doctor_id)

    return render_template(
        'doctor_details.html',
        doctor=doctor
    )

