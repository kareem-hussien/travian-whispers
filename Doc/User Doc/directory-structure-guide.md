# Directory Structure Guide for Travian Whispers Web Templates

## CSS Files Structure
Place all CSS files in `web/static/css/`:

```
web/static/css/
├── variables.css       - CSS variables and color definitions
├── style.css           - Main general styles
├── sidebar.css         - Sidebar specific styles
├── layout.css          - Layout structure styles
├── components.css      - Reusable UI component styles
└── dashboard.css       - Dashboard specific styles
```

## HTML Components Structure
Place all component templates in `web/templates/user/components/`:

```
web/templates/user/components/
├── header.html             - Head section with CSS imports
├── sidebar.html            - Sidebar navigation
├── topbar.html             - Top navigation bar
├── footer.html             - Footer with scripts
├── flash_messages.html     - Flash message display
├── stat_card.html          - Statistics card
├── task_card.html          - Task status card
├── village_card.html       - Village information card
├── activity_log.html       - Activity history display
├── auto_farm_status.html   - Auto farm status display
├── farm_stats.html         - Farm statistics display
├── troop_card.html         - Troop training card
├── subscription_card.html  - Subscription plan card
├── profile_card.html       - Profile information form
├── password_change.html    - Password change form
├── welcome_card.html       - Dashboard welcome message
├── form_field.html         - Reusable form field
├── form_checkbox.html      - Reusable form checkbox
├── form_select.html        - Reusable form select dropdown
└── page_header.html        - Page header with title and buttons
```

## Main Page Templates
Main page templates extend the layout and include the components:

```
web/templates/user/
├── layout.html             - Main layout template (includes components)
├── dashboard.html          - Dashboard page
├── profile.html            - Profile settings page
├── travian_settings.html   - Travian account settings page
├── villages.html           - Villages management page
├── auto_farm.html          - Auto farm management page
├── troop_trainer.html      - Troop trainer page
├── activity_logs.html      - Activity logs page
├── subscription.html       - Subscription management page
└── support.html            - Help and support page
```

## Usage Examples

### Example 1: Using a Component in a Template

```html
<!-- In auto_farm.html -->
{% extends 'user/layout.html' %}

{% block title %}Auto Farm Management{% endblock %}

{% block breadcrumb %}
<li class="breadcrumb-item active" aria-current="page">Auto Farm</li>
{% endblock %}

{% block content %}
<div class="content">
    <!-- Page Header -->
    <div class="row mb-4">
        <div class="col-12">
            <h2 class="mb-4">Auto Farm Management</h2>
            
            <!-- Include flash messages component -->
            {% include 'user/components/flash_messages.html' %}
        </div>
    </div>
    
    <!-- Status Overview -->
    <div class="row mb-4">
        <div class="col-lg-6 mb-4 mb-lg-0">
            <!-- Include auto farm status component -->
            {% with auto_farm=auto_farm %}
                {% include 'user/components/auto_farm_status.html' %}
            {% endwith %}
        </div>
        
        <div class="col-lg-6">
            <!-- Include farm stats component -->
            {% with farm_stats=farm_stats %}
                {% include 'user/components/farm_stats.html' %}
            {% endwith %}
        </div>
    </div>
    
    <!-- Rest of the content -->
</div>
{% endblock %}
```

### Example 2: Using the Main Layout Template

```html
<!-- In profile.html -->
{% extends 'user/layout.html' %}

{% block title %}Profile Settings{% endblock %}

{% block breadcrumb %}
<li class="breadcrumb-item active" aria-current="page">Profile Settings</li>
{% endblock %}

{% block content %}
<div class="content">
    <!-- Page Header -->
    <div class="row mb-4">
        <div class="col-12">
            <h2 class="mb-4">Profile Settings</h2>
            
            <!-- Include flash messages component -->
            {% include 'user/components/flash_messages.html' %}
        </div>
    </div>
    
    <div class="row">
        <!-- Profile Information -->
        <div class="col-lg-6 mb-4">
            {% with user_profile=user_profile %}
                {% include 'user/components/profile_card.html' %}
            {% endwith %}
        </div>
        
        <!-- Password Change -->
        <div class="col-lg-6 mb-4">
            {% include 'user/components/password_change.html' %}
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<!-- Any additional scripts for this page -->
{% endblock %}
```

## Best Practices for Using Components

1. **Pass Only Required Data**: Only pass the specific data needed by each component
   ```html
   {% with village=village_data %}
       {% include 'user/components/village_card.html' %}
   {% endwith %}
   ```

2. **Use Default Values**: Components should have sensible defaults for optional parameters
   ```html
   <!-- In the component -->
   <h3>{{ value|default('N/A') }}</h3>
   ```

3. **Keep Components Independent**: Each component should be self-contained
   - CSS classes should be applied within the component
   - Component-specific JavaScript should be included at the end of the component

4. **Consistent Naming Conventions**: Follow consistent naming patterns
   - Components: snake_case (e.g., `village_card.html`)
   - Page templates: snake_case (e.g., `auto_farm.html`)
   - CSS files: kebab-case (e.g., `sidebar-menu.css`)
   - JavaScript files: kebab-case (e.g., `password-strength.js`)

## Integration with Flask

To properly integrate these templates with Flask:

1. Ensure the static files are properly linked:
   ```python
   app = Flask(__name__, static_folder='static', template_folder='templates')
   ```

2. When rendering templates, pass all required data:
   ```python
   @user_bp.route('/profile', methods=['GET', 'POST'])
   @login_required
   def profile():
       # Get user data
       user_model = User()
       user = user_model.get_user_by_id(session['user_id'])
       
       # Process form submission
       if request.method == 'POST':
           # Form processing code...
       
       # Prepare user profile data
       user_profile = {
           'username': user['username'],
           'email': user['email'],
           'settings': {
               'notification_email': user['settings'].get('notification', True),
               'auto_renew': user['settings'].get('autoRenew', False)
           }
       }
       
       # Render profile template with data
       return render_template(
           'user/profile.html', 
           user_profile=user_profile,
           current_user=user,
           title='Profile Settings'
       )
   ```