import frappe

@frappe.whitelist()
def get_janus_config():
    """API endpoint to get Janus configuration for frontend"""
    try:
        settings = frappe.get_single("Janus WebRTC Settings")
        if not settings.is_enabled:
            frappe.throw("Janus WebRTC is not enabled")
        
        return settings.get_janus_config()
        
    except Exception as e:
        frappe.logger().error(f"Error getting Janus config: {str(e)}")
        frappe.throw("Failed to get Janus configuration")