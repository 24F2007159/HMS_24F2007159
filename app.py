from flask import Flask
from flask_login import LoginManager
from application.database import db


import datetime

app = None

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.debug = True

    app.config['SECRET_KEY'] = 'secretkey'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hms.sqlite3'
    db.init_app(app)
    my_login_manager = LoginManager()
    my_login_manager.init_app(app)

    from application.models import User, Admin, Patient, Doctor, Department, Appointment, Treatment
    with app.app_context():
        db.create_all()
        db.session.commit()

        admin_username = 'admin'
        admin_password = 'admin123'  
        existing_admin = Admin.query.filter_by(username=admin_username).first()
        if not existing_admin:

            user = User(username=admin_username, user_role=0)
            db.session.add(user)
            db.session.commit()

            admin = Admin(username=admin_username, password=admin_password, admin_id=user.id)
            db.session.add(admin)
            db.session.commit()
            
    
    @my_login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    app.app_context().push()
    return app

app = create_app()
from application.routes import *

if __name__ == '__main__':
    app.run(debug=True)