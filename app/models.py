from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'specialist'
    full_name = db.Column(db.String(100), nullable=False)
    specialty = db.Column(db.String(50))  # Only for specialists
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    appointments = db.relationship('Appointment', backref='specialist', lazy='dynamic')
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Plan(db.Model):
    __tablename__ = 'plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(20), nullable=False)  # 'monthly', 'quarterly', 'yearly'
    base_price = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    options = db.relationship('PlanOption', backref='plan', lazy='dynamic', cascade='all, delete-orphan')
    memberships = db.relationship('Membership', backref='plan', lazy='dynamic')

    def __repr__(self):
        return f'<Plan {self.name}>'

class PlanOption(db.Model):
    __tablename__ = 'plan_options'
    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    option_name = db.Column(db.String(100), nullable=False)
    option_price = db.Column(db.Numeric(10, 2), nullable=False)
    hours_included = db.Column(db.Integer, default=0)
    specialty = db.Column(db.String(50), nullable=False)
    
    membership_options = db.relationship('MembershipOption', backref='option', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='option', lazy='dynamic')

    def __repr__(self):
        return f'<PlanOption {self.option_name} (Specialty: {self.specialty})>'


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), index=True, unique=True, nullable=False)
    phone = db.Column(db.String(20))
    address = db.Column(db.Text)
    date_of_birth = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    memberships = db.relationship('Membership', backref='client', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='client', lazy='dynamic')

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __repr__(self):
        return f'<Client {self.full_name()}>'

class Membership(db.Model):
    __tablename__ = 'memberships'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plans.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    renewal_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='active')  # 'active', 'expired', 'cancelled'
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    options = db.relationship('MembershipOption', backref='membership', lazy='dynamic', cascade='all, delete-orphan')

    def is_expiring_soon(self):
        return self.end_date <= datetime.utcnow().date() + timedelta(days=30)

    def __repr__(self):
        return f'<Membership {self.client.full_name()} - {self.plan.name}>'

class MembershipOption(db.Model):
    __tablename__ = 'membership_options'
    id = db.Column(db.Integer, primary_key=True)
    membership_id = db.Column(db.Integer, db.ForeignKey('memberships.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('plan_options.id'), nullable=False)
    hours_used = db.Column(db.Integer, default=0)
    hours_remaining = db.Column(db.Integer, nullable=False)

    def update_hours(self, duration):
        self.hours_used += duration
        self.hours_remaining = max(0, self.hours_remaining - duration)
        db.session.commit()

    def __repr__(self):
        return f'<MembershipOption {self.option.option_name}>'

class Appointment(db.Model):
    __tablename__ = 'appointments'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    specialist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey('plan_options.id'), nullable=False)
    appointment_date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # in minutes
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='scheduled')  # 'scheduled', 'completed', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Appointment {self.client.full_name()} with {self.specialist.full_name}>'

class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    related_entity_type = db.Column(db.String(20), nullable=False)  # 'membership' or 'appointment'
    related_entity_id = db.Column(db.Integer, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def mark_as_read(self):
        self.is_read = True
        db.session.commit()

    def __repr__(self):
        return f'<Notification {self.message[:20]}...>'

@login.user_loader
def load_user(id):
    return User.query.get(int(id))