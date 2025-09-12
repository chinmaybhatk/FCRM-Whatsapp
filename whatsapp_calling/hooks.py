from . import __version__ as app_version

app_name = "whatsapp_calling"
app_title = "WhatsApp Business Calling"
app_publisher = "FrappeCRM"
app_description = "WebRTC voice calling integration with WhatsApp Business API for FrappeCRM"
app_icon = "octicon octicon-device-mobile"
app_color = "green"
app_email = "admin@frappecrm.com"
app_license = "MIT"
app_version = app_version

# Includes in <head>
app_include_css = "/assets/whatsapp_calling/css/whatsapp_calling.css"
app_include_js = [
    "https://unpkg.com/mediasoup-client@3/lib/index.min.js",
    "/assets/whatsapp_calling/js/webrtc_client.js",
    "/assets/whatsapp_calling/js/calling_interface.js"
]

# include js, css files in header of desk.html
web_include_css = "/assets/whatsapp_calling/css/whatsapp_calling.css"
web_include_js = [
    "https://unpkg.com/mediasoup-client@3/lib/index.min.js",
    "/assets/whatsapp_calling/js/whatsapp_tab.js",
    "/assets/whatsapp_calling/js/webrtc_client.js"
]

# include js in page
page_js = {"whatsapp_tab" : "public/js/whatsapp_tab.js"}

# include js in doctype views
doctype_js = {
    "Lead": "public/js/whatsapp_tab.js",
    "Contact": "public/js/whatsapp_tab.js",
    "Customer": "public/js/whatsapp_tab.js"
}

# Document Events
doc_events = {
    "Lead": {
        "validate": "whatsapp_calling.whatsapp_integration.api_client.create_lead_from_whatsapp",
        "after_insert": "whatsapp_calling.analytics.metrics_collector.track_lead_creation"
    },
    "Contact": {
        "validate": "whatsapp_calling.whatsapp_integration.api_client.sync_contact_phone",
        "on_update": "whatsapp_calling.analytics.metrics_collector.track_contact_update"
    }
}

# Scheduled Tasks
scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "whatsapp_calling.calling.webrtc_manager.check_call_quality",
            "whatsapp_calling.analytics.metrics_collector.collect_metrics"
        ]
    },
    "daily": [
        "whatsapp_calling.analytics.report_generator.generate_daily_report"
    ]
}

# Testing
before_tests = "whatsapp_calling.install.before_tests"

fixtures = [
    {
        "dt": "Custom Field",
        "filters": [
            [
                "name", "in", [
                    "Lead-whatsapp_phone",
                    "Contact-whatsapp_phone",
                    "Customer-whatsapp_phone"
                ]
            ]
        ]
    }
]

# Permissions
has_permission = {
    "WhatsApp Call Log": "whatsapp_calling.permissions.call_log_permission",
    "Bot Conversation State": "whatsapp_calling.permissions.bot_conversation_permission"
}

# Website Route Rules
website_route_rules = [
    {"from_route": "/whatsapp/<path:app_path>", "to_route": "whatsapp"},
]

website_context = {
    "favicon": "/assets/whatsapp_calling/images/favicon.png",
    "splash_image": "/assets/whatsapp_calling/images/splash.png"
}

# Jinja Environment
jenv = {
    "methods": [
        "whatsapp_calling.utils.jinja_methods.get_whatsapp_status",
        "whatsapp_calling.utils.jinja_methods.format_phone_number"
    ]
}