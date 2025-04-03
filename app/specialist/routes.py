from flask import app, render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from app import db
from app.models import Client, Membership, PlanOption, Appointment, MembershipOption
from app.forms import AppointmentForm
from app.specialist import bp

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'specialist':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    # Get today's appointments
    today = datetime.utcnow().date()
    appointments = Appointment.query.filter(
        Appointment.specialist_id == current_user.id,
        db.func.date(Appointment.appointment_date) == today,
        Appointment.status == 'scheduled'
    ).order_by(Appointment.appointment_date).all()
    
    return render_template('specialist/dashboard.html', appointments=appointments)

@bp.route('/appointments')
@login_required
def appointments():
    if current_user.role != 'specialist':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    appointments = Appointment.query.filter_by(specialist_id=current_user.id).order_by(Appointment.appointment_date.desc()).all()
    return render_template('specialist/appointments.html', appointments=appointments)
@bp.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule():
    if current_user.role != 'specialist':
        flash('Access denied', 'danger')
        return redirect(url_for('auth.index'))

    form = AppointmentForm()
    
    # Initialize with empty choices to prevent None errors
    form.option_id.choices = [('', 'Select a service...')]
    form.client_id.choices = [('', 'Select a client...')]

    try:
        # Get services matching specialist's specialty
        services_query = PlanOption.query
        if hasattr(PlanOption, 'specialty') and current_user.specialty:
            services_query = services_query.filter(PlanOption.specialty == current_user.specialty)
        
        services = services_query.order_by(PlanOption.option_name).all()
        if services:
            form.option_id.choices += [(str(s.id), f"{s.option_name} (${s.option_price})") for s in services]
        else:
            form.option_id.choices = [('', 'No available services')]
            flash('No services available for your specialty', 'warning')

    except Exception as e:
        flash('Error loading services', 'danger')
        app.logger.error(f"Service loading error: {str(e)}")

    try:
        # Get active clients with memberships
        clients = Client.query.join(Membership).order_by(Client.last_name).all()
        if clients:
            form.client_id.choices += [(str(c.id), c.full_name()) for c in clients]
        else:
            form.client_id.choices = [('', 'No clients available')]
            flash('No clients found', 'warning')

    except Exception as e:
        flash('Error loading clients', 'danger')
        app.logger.error(f"Client loading error: {str(e)}")

    if form.validate_on_submit():
        try:
            # Validate selections
            if not form.client_id.data or form.client_id.data == '':
                flash('Please select a client', 'warning')
                return redirect(url_for('specialist.schedule'))

            if not form.option_id.data or form.option_id.data == '':
                flash('Please select a service', 'warning')
                return redirect(url_for('specialist.schedule'))

            client = Client.query.get(int(form.client_id.data))
            option = PlanOption.query.get(int(form.option_id.data))
            
            # Validate existence
            if not client:
                flash('Selected client not found', 'danger')
                return redirect(url_for('specialist.schedule'))
            
            if not option:
                flash('Selected service not found', 'danger')
                return redirect(url_for('specialist.schedule'))
            
            # Check membership and hours
            membership_option = MembershipOption.query.join(Membership).filter(
                Membership.client_id == client.id,
                MembershipOption.option_id == option.id,
                MembershipOption.hours_remaining > 0
            ).first()
            
            if not membership_option:
                flash(f'{client.full_name()} has no available hours for {option.option_name}', 'warning')
                return redirect(url_for('specialist.schedule'))
            
            # Validate appointment time
            appointment_time = form.appointment_date.data
            if appointment_time <= datetime.utcnow():
                flash('Appointment time must be in the future', 'warning')
                return redirect(url_for('specialist.schedule'))
            
            # Validate duration (30min to 4 hours)
            duration = form.duration.data
            if not (30 <= duration <= 240):
                flash('Duration must be between 30 and 240 minutes', 'warning')
                return redirect(url_for('specialist.schedule'))
            
            # Check for overlapping appointments
            existing = Appointment.query.filter(
                Appointment.specialist_id == current_user.id,
                Appointment.appointment_date == appointment_time
            ).first()
            
            if existing:
                flash(f'You already have an appointment at {appointment_time.strftime("%H:%M")}', 'warning')
                return redirect(url_for('specialist.schedule'))
            
            # Create appointment
            appointment = Appointment(
                client_id=client.id,
                specialist_id=current_user.id,
                option_id=option.id,
                appointment_date=appointment_time,
                duration=duration,
                notes=form.notes.data,
                status='scheduled'
            )
            
            # Update hours (convert minutes to hours)
            duration_hours = duration / 60
            membership_option.hours_used += duration_hours
            membership_option.hours_remaining = max(0, membership_option.hours_remaining - duration_hours)
            
            db.session.add(appointment)
            db.session.commit()
            
            flash(
                f'''Appointment scheduled!
                Client: {client.full_name()}
                Service: {option.option_name}
                Time: {appointment_time.strftime("%Y-%m-%d %H:%M")}''',
                'success'
            )
            return redirect(url_for('specialist.appointments'))
            
        except ValueError as e:
            db.session.rollback()
            flash('Invalid selection - please try again', 'danger')
            app.logger.error(f"Value error in scheduling: {str(e)}")
        except Exception as e:
            db.session.rollback()
            flash('Failed to schedule appointment', 'danger')
            app.logger.error(f"Scheduling error: {str(e)}")
    
    return render_template('specialist/schedule.html',
                         form=form,
                         specialist=current_user,
                         now=datetime.utcnow())

@bp.route('/appointment/<int:id>/complete')
@login_required
def complete_appointment(id):
    if current_user.role != 'specialist':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    appointment = Appointment.query.get_or_404(id)
    if appointment.specialist_id != current_user.id:
        flash('You can only complete your own appointments')
        return redirect(url_for('specialist.appointments'))
    
    appointment.status = 'completed'
    db.session.commit()
    flash('Appointment marked as completed')
    return redirect(url_for('specialist.appointments'))

@bp.route('/appointment/<int:id>/cancel')
@login_required
def cancel_appointment(id):
    if current_user.role != 'specialist':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    appointment = Appointment.query.get_or_404(id)
    if appointment.specialist_id != current_user.id:
        flash('You can only cancel your own appointments')
        return redirect(url_for('specialist.appointments'))
    
    # Return hours to client's membership
    membership_option = MembershipOption.query.join(Membership).filter(
        Membership.client_id == appointment.client_id,
        MembershipOption.option_id == appointment.option_id
    ).first()
    
    if membership_option:
        duration_hours = appointment.duration / 60
        membership_option.hours_used -= duration_hours
        membership_option.hours_remaining += duration_hours
    
    appointment.status = 'cancelled'
    db.session.commit()
    flash('Appointment cancelled and hours returned to client')
    return redirect(url_for('specialist.appointments'))