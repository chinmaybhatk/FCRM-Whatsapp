import frappe

@frappe.whitelist()
def get_mediasoup_config():
    """API endpoint to get MediaSoup configuration for frontend"""
    try:
        settings = frappe.get_single("MediaSoup WebRTC Settings")
        if not settings.is_enabled:
            frappe.throw("MediaSoup WebRTC is not enabled")
        
        return settings.get_mediasoup_config()
        
    except Exception as e:
        frappe.logger().error(f"Error getting MediaSoup config: {str(e)}")
        frappe.throw("Failed to get MediaSoup configuration")

@frappe.whitelist()
def check_mediasoup_status():
    """Check MediaSoup installation and configuration status"""
    try:
        settings = frappe.get_single("MediaSoup WebRTC Settings")
        
        # Check installation
        install_status = settings.check_mediasoup_installation()
        
        # Check port availability
        ports_available = settings.test_port_range()
        
        # Get public IP
        public_ip = settings.get_public_ip()
        
        return {
            "enabled": settings.is_enabled,
            "installation": install_status,
            "ports_available": ports_available,
            "public_ip": public_ip,
            "config": settings.get_mediasoup_config() if settings.is_enabled else None
        }
        
    except Exception as e:
        frappe.logger().error(f"Error checking MediaSoup status: {str(e)}")
        return {
            "enabled": False,
            "error": str(e)
        }