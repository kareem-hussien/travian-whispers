"""
Admin routes for Travian Whispers web application.
This module serves as the entry point for the admin panel blueprint.
"""
import logging
from flask import Blueprint

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import route modules - avoid circular imports by importing here
from web.routes.admin_apis import dashboard, users, subscriptions, transactions, settings, maintenance

# Register route functions with the blueprint
# Dashboard routes
admin_bp.add_url_rule('/', view_func=dashboard.index, methods=['GET'])

# User routes
admin_bp.add_url_rule('/users', view_func=users.index, methods=['GET'])
admin_bp.add_url_rule('/users/create', view_func=users.create, methods=['GET', 'POST'])
admin_bp.add_url_rule('/users/edit/<user_id>', view_func=users.edit, methods=['GET', 'POST'])
admin_bp.add_url_rule('/users/delete/<user_id>', view_func=users.delete, methods=['POST'])

# Subscription routes
admin_bp.add_url_rule('/subscriptions', view_func=subscriptions.index, methods=['GET'])
admin_bp.add_url_rule('/subscriptions/create', view_func=subscriptions.create, methods=['GET', 'POST'])
admin_bp.add_url_rule('/subscriptions/edit/<plan_id>', view_func=subscriptions.edit, methods=['GET', 'POST'])
admin_bp.add_url_rule('/subscriptions/delete/<plan_id>', view_func=subscriptions.delete, methods=['POST'])

# Transaction routes
admin_bp.add_url_rule('/transactions', view_func=transactions.index, methods=['GET'])
admin_bp.add_url_rule('/transactions/<transaction_id>', view_func=transactions.details, methods=['GET'])
admin_bp.add_url_rule('/transactions/update-status/<transaction_id>', view_func=transactions.update_status, methods=['POST'])

# Settings routes
admin_bp.add_url_rule('/settings', view_func=settings.index, methods=['GET', 'POST'])

# Maintenance routes
admin_bp.add_url_rule('/maintenance', view_func=maintenance.index, methods=['GET'])
admin_bp.add_url_rule('/logs', view_func=maintenance.logs, methods=['GET'])