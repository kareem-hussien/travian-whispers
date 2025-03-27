"""
Subscription management routes for Travian Whispers admin panel.
This module defines the subscription management routes for the admin panel.
"""
import logging
from flask import render_template, request, redirect, url_for, flash, session
from bson import ObjectId

from web.utils.decorators import admin_required
from database.models.subscription import SubscriptionPlan
from database.models.user import User

# Initialize logger
logger = logging.getLogger(__name__)

@admin_required
def index():
    """Subscription plans management page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get subscription plans
    subscription_model = SubscriptionPlan()
    plans = subscription_model.list_plans()
    
    # Add user count and revenue to each plan
    for plan in plans:
        # Count users with this plan
        plan_id = plan["_id"]
        user_count = user_model.collection.count_documents({
            "subscription.planId": plan_id,
            "subscription.status": "active"
        })
        
        # Calculate monthly revenue
        monthly_revenue = user_count * plan["price"]["monthly"]
        
        # Add to plan object
        plan["users"] = user_count
        plan["revenue"] = monthly_revenue
        
        # Format price for display
        plan["price"] = f"${plan['price']['monthly']}"
    
    # Render subscription plans template
    return render_template(
        'admin/subscriptions.html', 
        plans=plans, 
        current_user=current_user,
        title='Subscription Plans'
    )

@admin_required
def create():
    """Create subscription plan page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    if request.method == 'POST':
        # Process form submission
        name = request.form.get('planName')
        monthly_price = float(request.form.get('planPrice', 0))
        yearly_price = float(request.form.get('yearlyPrice', 0))
        description = request.form.get('planDescription')
        
        # Get features
        features = {
            'autoFarm': 'featureAutoFarm' in request.form,
            'trainer': 'featureTrainer' in request.form,
            'notification': 'featureNotification' in request.form,
            'advanced': 'featureAdvanced' in request.form,
            'maxVillages': int(request.form.get('maxVillages', 1)),
            'maxTasks': int(request.form.get('maxTasks', 1))
        }
        
        # Create new plan
        subscription_model = SubscriptionPlan()
        new_plan = subscription_model.create_plan(
            name=name,
            description=description,
            monthly_price=monthly_price,
            yearly_price=yearly_price,
            features=features
        )
        
        if new_plan:
            flash('Subscription plan created successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' created subscription plan '{name}'")
            return redirect(url_for('admin.subscriptions'))
        else:
            flash('Failed to create plan. Name may already exist.', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to create subscription plan '{name}'")
    
    # Render plan create template
    return render_template(
        'admin/subscriptions/create.html', 
        current_user=current_user,
        title='Create Subscription Plan'
    )

@admin_required
def edit(plan_id):
    """Edit subscription plan page."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get subscription plan
    subscription_model = SubscriptionPlan()
    plan = subscription_model.get_plan_by_id(plan_id)
    
    if not plan:
        flash('Plan not found', 'danger')
        return redirect(url_for('admin.subscriptions'))
    
    if request.method == 'POST':
        # Process form submission
        name = request.form.get('planName')
        monthly_price = float(request.form.get('planPrice', 0))
        yearly_price = float(request.form.get('yearlyPrice', 0))
        description = request.form.get('planDescription')
        
        # Get features
        features = {
            'autoFarm': 'featureAutoFarm' in request.form,
            'trainer': 'featureTrainer' in request.form,
            'notification': 'featureNotification' in request.form,
            'advanced': 'featureAdvanced' in request.form,
            'maxVillages': int(request.form.get('maxVillages', 1)),
            'maxTasks': int(request.form.get('maxTasks', 1))
        }
        
        # Prepare update data
        update_data = {
            'name': name,
            'description': description,
            'price': {
                'monthly': monthly_price,
                'yearly': yearly_price
            },
            'features': features
        }
        
        # Update plan
        success = subscription_model.update_plan(plan_id, update_data)
        
        if success:
            flash('Subscription plan updated successfully', 'success')
            logger.info(f"Admin '{current_user['username']}' updated subscription plan '{name}'")
            return redirect(url_for('admin.subscriptions'))
        else:
            flash('Failed to update plan', 'danger')
            logger.warning(f"Admin '{current_user['username']}' failed to update subscription plan '{name}'")
    
    # Render plan edit template
    return render_template(
        'admin/plan_edit.html', 
        plan=plan, 
        current_user=current_user,
        title='Edit Subscription Plan'
    )

@admin_required
def delete(plan_id):
    """Delete subscription plan."""
    # Get current user for the template
    user_model = User()
    current_user = user_model.get_user_by_id(session['user_id'])
    
    # Get subscription plan
    subscription_model = SubscriptionPlan()
    plan = subscription_model.get_plan_by_id(plan_id)
    
    if not plan:
        flash('Plan not found', 'danger')
        return redirect(url_for('admin.subscriptions'))
    
    # Check if plan has active users
    user_count = user_model.collection.count_documents({
        "subscription.planId": ObjectId(plan_id),
        "subscription.status": "active"
    })
    
    if user_count > 0:
        flash(f'Cannot delete plan: {user_count} active users are subscribed to this plan', 'danger')
        return redirect(url_for('admin.subscriptions'))
    
    # Delete plan
    success = subscription_model.delete_plan(plan_id)
    
    if success:
        flash('Subscription plan deleted successfully', 'success')
        logger.info(f"Admin '{current_user['username']}' deleted subscription plan '{plan['name']}'")
    else:
        flash('Failed to delete plan', 'danger')
        logger.warning(f"Admin '{current_user['username']}' failed to delete subscription plan '{plan['name']}'")
    
    return redirect(url_for('admin.subscriptions'))