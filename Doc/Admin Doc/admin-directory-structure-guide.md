# Directory Structure Guide for Admin Templates

## Overview

This guide outlines the recommended directory structure for the admin section of the Travian Whispers application, focusing on the template organization and component usage patterns.

## Directory Structure

```
web/
├── static/
│   ├── css/
│   │   ├── variables.css           - CSS variables (colors, sizes, etc.)
│   │   ├── style_dashboard.css     - Main dashboard styles
│   │   ├── sidebar.css             - Sidebar navigation styles
│   │   ├── layout.css              - Layout structure styles
│   │   └── components.css          - Reusable UI component styles
│   ├── js/
│   │   ├── admin.js                - Main admin panel JavaScript
│   │   ├── charts.js               - Chart initialization and config
│   │   └── admin-components.js     - Component-specific JavaScript
│   └── img/
│       └── admin/                  - Admin-specific images
│
└── templates/
    └── admin/
        ├── layout.html             - Main admin layout template
        ├── dashboard.html          - Admin dashboard
        ├── users.html              - User management page
        ├── subscriptions.html      - Subscription plans page
        ├── transactions.html       - Transaction history page
        ├── settings.html           - System settings page
        ├── settings/           - System settings page
        │   ├── maintenance.html    - System maintenance page
        │   ├── backup.html           - System logs page
        │   ├── logs.html           - System logs page
        ├── user/                   - User management related pages
        │   ├── create.html         - Create user page
        │   ├── edit.html           - Edit user page
        │   └── view.html           - View user details page
        ├── subscriptions/          - Subscription plan related pages
        │   ├── create.html         - Create plan page
        │   └── edit.html           - Edit plan page
        ├── transaction/            - Transaction related pages
        │   └── details.html        - Transaction details page
        └── components/             - Reusable admin components
            ├── admin-layout.html           - Main layout component
            ├── admin-sidebar.html          - Sidebar navigation
            ├── admin-topbar.html           - Top navigation bar
            ├── admin-footer.html           - Footer with scripts
            ├── admin-page-header.html      - Page headers with actions
            ├── admin-flash-messages.html   - Flash messages display
            ├── admin-dashboard-card.html   - Cards for dashboard
            ├── admin-stat-card.html        - Statistics cards
            ├── admin-table.html            - Data tables component
            ├── admin-activity-log.html     - Activity log component
            ├── admin-user-card.html        - User card component
            ├── admin-plan-card.html        - Plan card component
            ├── admin-transaction-card.html - Transaction card component
            ├── admin-chart-card.html       - Chart card component
            ├── admin-quick-actions.html    - Quick actions component
            ├── admin-system-status.html    - System status component
            ├── admin-search-filter.html    - Search and filter component
            ├── admin-tab-nav.html          - Tab navigation component
            ├── admin-modal.html            - Modal dialog component
            ├── admin-confirmation-modal.html - Confirmation dialog
            ├── admin-alert.html            - Alert message component
            ├── admin-form-field.html       - Form field component
            ├── admin-form-select.html      - Form select component
            ├── admin-form-checkbox.html    - Form checkbox component
            ├── admin-settings-form.html    - Settings form component
            ├── admin-backup-restore.html   - Backup and restore component
            ├── admin-maintenance-mode.html - Maintenance mode component
            └── admin-report-generator.html - Report generator component
```

## Component Usage Patterns

### Main Layout Structure

Every admin page should extend the main admin layout:

```html
{% extends 'admin/components/admin-layout.html' %}

{% block title %}Dashboard{% endblock %}

{% block breadcrumb %}
<li class="breadcrumb-item active" aria-current="page">Dashboard</li>
{% endblock %}

{% block content %}
<!-- Page content goes here -->
{% endblock %}

{% block scripts %}
<!-- Page-specific scripts go here -->
{% endblock %}
```

### Page Header Pattern

Use the page header component for consistent page titles and action buttons:

```html
{% with 
    title="User Management",
    subtitle="Manage user accounts and permissions",
    show_buttons=true,
    primary_button_text="Add New User",
    primary_button_icon="person-plus",
    primary_button_url=url_for('admin.user_create')
%}
    {% include 'admin/components/admin-page-header.html' %}
{% endwith %}
```

### Dashboard Cards Pattern

Use dashboard cards to organize content sections:

```html
{% with 
    card_title="Recent Activity",
    header_action_text="View All",
    header_action_url=url_for('admin.logs')
%}
    {% include 'admin/components/admin-dashboard-card.html' %}
    <!-- Card content goes here -->
{% endwith %}
```

### Data Tables Pattern

Use the table component for displaying data with consistent styling:

```html
{% with 
    columns=[
        {'key': 'username', 'label': 'Username', 'sortable': true},
        {'key': 'email', 'label': 'Email', 'sortable': true},
        {'key': 'role', 'label': 'Role', 'format': 'badge'},
        {'key': 'status', 'label': 'Status', 'format': 'badge'},
        {'key': 'joined', 'label': 'Joined', 'format': 'datetime'}
    ],
    data=users,
    view_url_prefix=url_for('admin.user_view', user_id=''),
    edit_url_prefix=url_for('admin.user_edit', user_id=''),
    empty_message="No users found matching your criteria."
%}
    {% include 'admin/components/admin-table.html' %}
{% endwith %}
```

### Form Components Pattern

Use form components for consistent form styling:

```html
<form action="{{ url_for('admin.user_create') }}" method="post">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    
    {% with 
        field_type="text",
        field_id="username",
        field_name="username",
        field_label="Username",
        field_required=true,
        field_help="Username must be 3-20 characters and start with a letter."
    %}
        {% include 'admin/components/admin-form-field.html' %}
    {% endwith %}
    
    {% with 
        field_type="email",
        field_id="email",
        field_name="email",
        field_label="Email Address",
        field_required=true
    %}
        {% include 'admin/components/admin-form-field.html' %}
    {% endwith %}
    
    {% with 
        select_id="role",
        select_name="role",
        select_label="User Role",
        select_options=[
            {'value': 'user', 'text': 'User'},
            {'value': 'admin', 'text': 'Administrator'}
        ],
        select_selected='user',
        select_required=true
    %}
        {% include 'admin/components/admin-form-select.html' %}
    {% endwith %}
    
    <button type="submit" class="btn btn-primary">Create User</button>
</form>
```

### Modal Dialog Pattern

Use modal dialogs for confirmations and forms:

```html
{% with 
    modal_id="deleteUserModal",
    modal_title="Confirm User Deletion",
    confirm_message="Are you sure you want to delete this user? This action cannot be undone.",
    confirm_button_text="Delete User",
    item_type="User",
    form_id="deleteUserForm",
    form_action=url_for('admin.user_delete')
%}
    {% include 'admin/components/admin-confirmation-modal.html' %}
{% endwith %}
```

## Integration with Flask Routes

The admin templates are designed to work with the following Flask blueprint structure:

```python
# admin/__init__.py
from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import routes to register them with the blueprint
from . import dashboard, users, subscriptions, transactions, settings, maintenance, logs

# Register the blueprint with the Flask app
def register_admin_blueprint(app):
    app.register_blueprint(admin_bp)
```

Each route should render the appropriate template and pass the necessary data:

```python
# admin/dashboard.py
from flask import render_template
from . import admin_bp

@admin_bp.route('/')
def dashboard():
    # Get dashboard data from database
    # ...
    
    return render_template(
        'admin/dashboard.html',
        user_stats=user_stats,
        revenue_stats=revenue_stats,
        subscription_stats=subscription_stats,
        system_stats=system_stats,
        recent_activity=recent_activity,
        recent_users=recent_users,
        recent_transactions=recent_transactions
    )
```

## CSS Naming Conventions

For CSS class naming, follow these conventions:

1. Use kebab-case for class names (e.g., `admin-card`, `user-table`)
2. Prefix admin-specific classes with `admin-` (e.g., `admin-sidebar`, `admin-card`)
3. Use BEM (Block Element Modifier) for complex components:
   - Block: `admin-card`
   - Element: `admin-card__header`
   - Modifier: `admin-card--highlighted`

## JavaScript Organization

Organize JavaScript by component function:

1. Place general admin panel JavaScript in `admin.js`
2. Place chart initializations in `charts.js`
3. Place component-specific JavaScript in `admin-components.js`
4. For components with significant JavaScript, include the script directly in the component template

## Best Practices

1. **Consistent Naming**: Keep component names consistent with their filenames
2. **Parameter Documentation**: Document all parameters in component templates
3. **Minimal Dependencies**: Minimize external JavaScript dependencies
4. **Responsive Design**: Ensure all components work well on both desktop and mobile
5. **Accessibility**: Include proper ARIA attributes and keyboard navigation
6. **Performance**: Minimize DOM manipulations and optimize JavaScript
7. **Error Handling**: Include appropriate error states for all components
8. **Defaults**: Provide sensible defaults for all component parameters
9. **Component Independence**: Components should work independently when possible
10. **Documentation**: Keep this guide updated as new components are added

## Example Page Construction

### Dashboard Page

```html
{% extends 'admin/components/admin-layout.html' %}

{% block title %}Dashboard{% endblock %}

{% block breadcrumb %}
<li class="breadcrumb-item active" aria-current="page">Dashboard</li>
{% endblock %}

{% block content %}
<div class="content">
    <!-- Page Header -->
    {% with 
        title="Admin Dashboard",
        subtitle="Overview of your system status and statistics",
        show_buttons=true,
        primary_button_text="Refresh Stats",
        primary_button_icon="arrow-clockwise",
        primary_button_id="refreshStatsBtn",
        secondary_button_text="Generate Report",
        secondary_button_icon="file-earmark-text",
        secondary_button_id="generateReportBtn",
        secondary_button_url="#generateReportModal",
        secondary_button_data_bs_toggle="modal",
        secondary_button_data_bs_target="#generateReportModal"
    %}
        {% include 'admin/components/admin-page-header.html' %}
    {% endwith %}
    
    <!-- Key Stats -->
    <div class="row mb-4">
        <div class="col-xl-3 col-md-6 mb-4">
            {% with 
                icon="people",
                icon_bg="bg-primary-light",
                title="Total Users",
                value=user_stats.total_users,
                change_value="+"+user_stats.new_users_week+" this week",
                change_direction="up",
                progress_value=(user_stats.active_users / user_stats.total_users * 100)|round|int if user_stats.total_users > 0 else 0,
                progress_label=user_stats.active_users|string+" active users ("+((user_stats.active_users / user_stats.total_users * 100)|round|int if user_stats.total_users > 0 else 0)|string+"%)"
            %}
                {% include 'admin/components/admin-stat-card.html' %}
            {% endwith %}
        </div>
        
        <!-- Add more stat cards here -->
    </div>
    
    <!-- Recent Activity and Users -->
    <div class="row mb-4">
        <!-- Recent Activity -->
        <div class="col-lg-7 mb-4 mb-lg-0">
            {% with 
                activities=recent_activity,
                show_header=true,
                max_height="400px"
            %}
                {% include 'admin/components/admin-activity-log.html' %}
            {% endwith %}
        </div>
        
        <!-- Recent Users -->
        <div class="col-lg-5">
            <div class="dashboard-card">
                <div class="d-flex justify-content-between align-items-center mb-4">
                    <h5 class="mb-0">Recent Users</h5>
                    <a href="{{ url_for('admin.users') }}" class="btn btn-sm btn-outline-primary">View All</a>
                </div>
                
                <div class="list-group">
                    {% for user in recent_users %}
                        {% with user=user, show_actions=true %}
                            {% include 'admin/components/admin-user-card.html' %}
                        {% endwith %}
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Quick Actions -->
    {% with 
        actions=[
            {
                'icon': 'person-plus',
                'text': 'Add New User',
                'url': url_for('admin.user_create'),
                'color': 'primary'
            },
            {
                'icon': 'plus-circle',
                'text': 'Create Plan',
                'url': url_for('admin.create_plan'),
                'color': 'info'
            },
            {
                'icon': 'cloud-arrow-up',
                'text': 'Database Backup',
                'modal': 'backupModal',
                'color': 'warning'
            },
            {
                'icon': 'tools',
                'text': 'Maintenance Mode',
                'modal': 'maintenanceModal',
                'color': 'secondary'
            }
        ],
        columns=4
    %}
        {% include 'admin/components/admin-quick-actions.html' %}
    {% endwith %}
</div>

<!-- Include modals -->
{% include 'admin/components/modals/generate-report-modal.html' %}
{% include 'admin/components/modals/backup-modal.html' %}
{% include 'admin/components/modals/maintenance-modal.html' %}
{% endblock %}

{% block scripts %}
<script src="{{ url_for('static', filename='js/admin/charts.js') }}"></script>
<script>
    // Initialize charts and dashboard-specific functionality
    document.addEventListener('DOMContentLoaded', function() {
        // Refresh stats button functionality
        document.getElementById('refreshStatsBtn').addEventListener('click', function() {
            // Refresh dashboard stats
        });
        
        // Initialize subscription chart
        initSubscriptionChart();
    });
    
    function initSubscriptionChart() {
        // Chart initialization code
    }
</script>
{% endblock %}
```

This guide should provide a comprehensive overview of how to organize and use the admin components to build consistent and maintainable admin pages.
