from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DateField, DateTimeField, TextAreaField, DecimalField, IntegerField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from app.models import PlanOption, User, Client, Plan

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('specialist', 'Specialist')], validators=[DataRequired()])
    specialty = StringField('Specialty (if specialist)')
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

class ClientForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone')
    address = TextAreaField('Address')
    date_of_birth = DateField('Date of Birth')
    submit = SubmitField('Save')

class PlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired()])
    duration = SelectField('Duration', choices=[
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], validators=[DataRequired()])
    base_price = DecimalField('Base Price', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Save')

class PlanOptionForm(FlaskForm):
    option_name = StringField('Option Name', validators=[DataRequired()])
    option_price = DecimalField('Option Price', validators=[DataRequired()])
    hours_included = IntegerField('Hours Included', default=0)
    submit = SubmitField('Save')

class MembershipForm(FlaskForm):
    plan_id = SelectField('Plan', coerce=int, validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    options = SelectMultipleField('Options', coerce=int)
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(MembershipForm, self).__init__(*args, **kwargs)
        self.plan_id.choices = [(p.id, p.name) for p in Plan.query.order_by(Plan.name).all()]
        self.options.choices = [(o.id, f"{o.option_name} (${o.option_price})") 
                              for o in PlanOption.query.order_by(PlanOption.option_name).all()]

class AppointmentForm(FlaskForm):
    client_id = SelectField('Client',  validators=[DataRequired()])
    option_id = SelectField('Service',  validators=[DataRequired()])
    appointment_date = DateTimeField('Date and Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()])
    duration = IntegerField('Duration (minutes)', validators=[DataRequired()])
    notes = TextAreaField('Notes')
    submit = SubmitField('Schedule')

    def __init__(self, *args, **kwargs):
        super(AppointmentForm, self).__init__(*args, **kwargs)
        self.client_id.choices = [('', 'Select Client...')] + [(c.id, c.full_name()) for c in Client.query.order_by(Client.last_name).all()]
        self.option_id.choices = [('', 'Select Service...')] + [(o.id, o.option_name) for o in PlanOption.query.order_by(PlanOption.option_name).all()]