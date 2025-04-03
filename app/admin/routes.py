from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_required
from datetime import datetime, timedelta
from app import db
from app.models import User, Client, Plan, PlanOption, Membership, MembershipOption, Notification
from app.forms import ClientForm, PlanForm, PlanOptionForm, MembershipForm
from app.admin import bp

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    # Get expiring memberships (within 30 days)
    expiring_memberships = Membership.query.filter(
        Membership.end_date <= datetime.utcnow().date() + timedelta(days=30),
        Membership.end_date >= datetime.utcnow().date(),
        Membership.status == 'active'
    ).all()
    
    # Get recent clients
    recent_clients = Client.query.order_by(Client.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                         expiring_memberships=expiring_memberships,
                         recent_clients=recent_clients)

@bp.route('/clients')
@login_required
def clients():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    clients = Client.query.order_by(Client.last_name).all()
    return render_template('admin/clients.html', clients=clients)

@bp.route('/add_client', methods=['GET', 'POST'])
@login_required
def add_client():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    form = ClientForm()
    if form.validate_on_submit():
        client = Client(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data,
            date_of_birth=form.date_of_birth.data
        )
        db.session.add(client)
        db.session.commit()
        flash('Client added successfully!')
        return redirect(url_for('admin.clients'))
    
    return render_template('admin/add_client.html', form=form)

@bp.route('/edit_client/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_client(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    client = Client.query.get_or_404(id)
    form = ClientForm(obj=client)
    
    if form.validate_on_submit():
        client.first_name = form.first_name.data
        client.last_name = form.last_name.data
        client.email = form.email.data
        client.phone = form.phone.data
        client.address = form.address.data
        client.date_of_birth = form.date_of_birth.data
        db.session.commit()
        flash('Client updated successfully!')
        return redirect(url_for('admin.clients'))
    
    return render_template('admin/edit_client.html', form=form, client=client)

@bp.route('/delete_client/<int:id>')
@login_required
def delete_client(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    flash('Client deleted successfully!')
    return redirect(url_for('admin.clients'))

@bp.route('/plans')
@login_required
def plans():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    plans = Plan.query.all()
    return render_template('admin/plans.html', plans=plans)

@bp.route('/add_plan', methods=['GET', 'POST'])
@login_required
def add_plan():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    form = PlanForm()
    if form.validate_on_submit():
        plan = Plan(
            name=form.name.data,
            duration=form.duration.data,
            base_price=form.base_price.data,
            description=form.description.data
        )
        db.session.add(plan)
        db.session.commit()
        flash('Plan added successfully!')
        return redirect(url_for('admin.plans'))
    
    return render_template('admin/add_plan.html', form=form)

@bp.route('/edit_plan/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_plan(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    plan = Plan.query.get_or_404(id)
    form = PlanForm(obj=plan)
    
    if form.validate_on_submit():
        plan.name = form.name.data
        plan.duration = form.duration.data
        plan.base_price = form.base_price.data
        plan.description = form.description.data
        db.session.commit()
        flash('Plan updated successfully!')
        return redirect(url_for('admin.plans'))
    
    return render_template('admin/edit_plan.html', form=form, plan=plan)

@bp.route('/delete_plan/<int:id>')
@login_required
def delete_plan(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    plan = Plan.query.get_or_404(id)
    db.session.delete(plan)
    db.session.commit()
    flash('Plan deleted successfully!')
    return redirect(url_for('admin.plans'))

@bp.route('/plan/<int:id>/add_option', methods=['GET', 'POST'])
@login_required
def add_plan_option(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    plan = Plan.query.get_or_404(id)
    form = PlanOptionForm()
    
    if form.validate_on_submit():
        option = PlanOption(
            plan_id=plan.id,
            option_name=form.option_name.data,
            option_price=form.option_price.data,
            hours_included=form.hours_included.data
        )
        db.session.add(option)
        db.session.commit()
        flash('Option added successfully!')
        return redirect(url_for('admin.plans'))
    
    return render_template('admin/add_plan_option.html', form=form, plan=plan)

@bp.route('/client/<int:id>/add_membership', methods=['GET', 'POST'])
@login_required
def add_membership(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    client = Client.query.get_or_404(id)
    form = MembershipForm()
    
    if form.validate_on_submit():
        plan = Plan.query.get(form.plan_id.data)
        
        # Calculate end date based on plan duration
        start_date = form.start_date.data
        if plan.duration == 'monthly':
            end_date = start_date + timedelta(days=30)
        elif plan.duration == 'quarterly':
            end_date = start_date + timedelta(days=90)
        else:  # yearly
            end_date = start_date + timedelta(days=365)
        
        # Calculate renewal date (7 days before end date)
        renewal_date = end_date - timedelta(days=7)
        
        # Calculate total price
        selected_options = PlanOption.query.filter(PlanOption.id.in_(form.options.data)).all()
        options_price = sum(option.option_price for option in selected_options)
        total_price = plan.base_price + options_price
        
        # Create membership
        membership = Membership(
            client_id=client.id,
            plan_id=plan.id,
            start_date=start_date,
            end_date=end_date,
            renewal_date=renewal_date,
            total_price=total_price
        )
        db.session.add(membership)
        db.session.commit()
        
        # Add selected options
        for option in selected_options:
            membership_option = MembershipOption(
                membership_id=membership.id,
                option_id=option.id,
                hours_remaining=option.hours_included
            )
            db.session.add(membership_option)
        
        db.session.commit()
        
        # Create notification for renewal
        notification = Notification(
            user_id=current_user.id,
            message=f"Membership for {client.full_name()} needs renewal by {renewal_date}",
            related_entity_type='membership',
            related_entity_id=membership.id
        )
        db.session.add(notification)
        db.session.commit()
        
        flash('Membership added successfully!')
        return redirect(url_for('admin.client_details', id=client.id))
    
    return render_template('admin/add_membership.html', form=form, client=client)

@bp.route('/client/<int:id>')
@login_required
def client_details(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('auth.index'))
    
    client = Client.query.get_or_404(id)
    return render_template('admin/client_details.html', client=client)