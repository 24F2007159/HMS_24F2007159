from flask_login import UserMixin
from .database import db
from datetime import datetime as dt

class User(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(), nullable = False, unique = True)
    user_role = db.Column(db.Integer(), nullable = False)
    admin = db.relationship('Admin', backref = 'user')
    doctor = db.relationship('Doctor', backref = 'user')
    patient = db.relationship('Patient', backref = 'user')
    

    def get_id(self):
        return str(self.id)
    
class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)
    admin_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable = False)

class Doctor(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)
    name = db.Column(db.String(), nullable = False)
    qualification = db.Column(db.String(), nullable = False)
    experience = db.Column(db.Integer(), nullable = False)
    fee = db.Column(db.Integer(), nullable = False)
    flagged = db.Column(db.Integer(), nullable = False)
    specialization = db.Column(db.String(), nullable = False)
    designation = db.Column(db.String(), nullable = False)
    registration_num = db.Column(db.String(), nullable = False)
    doctor_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable = False)
    appointment = db.relationship('Appointment', backref = 'doctor')
    department_id = db.Column(db.Integer(), db.ForeignKey("department.id"), nullable = False)


class Patient(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    username = db.Column(db.String(), nullable = False, unique = True)
    password = db.Column(db.String(), nullable = False)
    name = db.Column(db.String(), nullable = False)
    age = db.Column(db.Integer(), nullable = False)
    gender = db.Column(db.String(), nullable = False)
    address = db.Column(db.String(), nullable = False)
    contact_num = db.Column(db.Integer(), nullable = False)
    medical_history = db.Column(db.String(), nullable = False)
    flagged = db.Column(db.Integer(), nullable = False)
    patient_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable = False)
    appointment = db.relationship('Appointment', backref = 'patient')

class Treatment(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    diagnosis = db.Column(db.String(), nullable = False)
    prescription = db.Column(db.String(), nullable = False)
    notes = db.Column(db.String(), nullable = True)
    followup_date = db.Column(db.DateTime(), nullable = True)
    treatment_id = db.Column(db.Integer(), db.ForeignKey("appointment.id"), nullable = False)

class Department(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    name = db.Column(db.String(), nullable = False)
    description = db.Column(db.String(), nullable = False)
    doctor_registration = db.Column(db.String(), nullable = False)
    doctor = db.relationship('Doctor', backref = 'department')
    
class Appointment(UserMixin, db.Model):
    id = db.Column(db.Integer(), primary_key = True)
    appointment_date = db.Column(db.DateTime(), nullable = False)
    appointment_time = db.Column(db.Time(), nullable = False)
    reason = db.Column(db.String(), nullable = False)
    status = db.Column(db.String(), nullable = False)
    patient_id = db.Column(db.Integer(), db.ForeignKey("patient.id"), nullable = False)
    doctor_id = db.Column(db.Integer(), db.ForeignKey("doctor.id"), nullable = False)
    treatment = db.relationship('Treatment', backref = 'appointment')

