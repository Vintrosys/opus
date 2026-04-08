app_name = "opus"
app_title = "Opus"
app_publisher = "Opus"
app_description = "OPUS Customization"
app_email = "admin@vintrosys.com"
app_license = "mit"

fixtures = [

    # Client Scripts
    {
        "dt": "Client Script",
        "filters": [
            ["dt", "in", [
                "Sales Invoice",
                "BOM",
                "Work Order",
                "Stock Entry",
                "Sales Order",
                "Sales Person",
                "Coating Machine Production Record",
                "Batch",
                "Production Plan",
                "Purchase Invoice"
            ]],
            ["module", "=", "Opus"]
        ]
    },

    # Server Scripts
    {
        "dt": "Server Script",
        "filters": [
            ["reference_doctype", "in", [
                "Stock Entry",
                "BOM",
                "Work Order",
                "Sales Order",
                "Coating Machine Production Record",
                "Job Card",
                "Material Request",
                "Employee Checkin",
                "Production Plan"
            ]],
            ["module", "=", "Opus"]
        ]
    },

    # Print Formats
    {
        "dt": "Print Format",
        "filters": [
            ["doc_type", "in", [
                "Sales Invoice",
                "Payment Entry",
                "Quality Inspection",
                "Purchase Order"
            ]],
            ["module", "=", "Opus"]
        ]
    }
]








# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "opus",
# 		"logo": "/assets/opus/logo.png",
# 		"title": "Opus",
# 		"route": "/opus",
# 		"has_permission": "opus.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/opus/css/opus.css"
# app_include_js = "/assets/opus/js/opus.js"

# include js, css files in header of web template
# web_include_css = "/assets/opus/css/opus.css"
# web_include_js = "/assets/opus/js/opus.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "opus/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {"Job Card" : "overrides/js/job_card.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "opus/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "opus.utils.jinja_methods",
# 	"filters": "opus.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "opus.install.before_install"
# after_install = "opus.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "opus.uninstall.before_uninstall"
# after_uninstall = "opus.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "opus.utils.before_app_install"
# after_app_install = "opus.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "opus.utils.before_app_uninstall"
# after_app_uninstall = "opus.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "opus.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

override_doctype_class = {
	"Stock Entry": "opus.overrides.py.stock_entry.CustomSe",
    "Job Card": "opus.overrides.py.job_card.JC"
}

# Document Events
# ---------------
# Hook on document methods and events

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"opus.tasks.all"
# 	],
# 	"daily": [
# 		"opus.tasks.daily"
# 	],
# 	"hourly": [
# 		"opus.tasks.hourly"
# 	],
# 	"weekly": [
# 		"opus.tasks.weekly"
# 	],
# 	"monthly": [
# 		"opus.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "opus.install.before_tests"

# Overriding Methods
# ------------------------------
#
override_whitelisted_methods = {
	"erpnext.manufacturing.doctype.job_card.job_card.make_time_log": "opus.overrides.py.job_card.make_time_log"
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "opus.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["opus.utils.before_request"]
# after_request = ["opus.utils.after_request"]

# Job Events
# ----------
# before_job = ["opus.utils.before_job"]
# after_job = ["opus.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"opus.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

