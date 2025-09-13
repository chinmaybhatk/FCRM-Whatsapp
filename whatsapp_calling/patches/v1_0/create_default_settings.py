import frappe


def execute():
    """Create default WhatsApp Business Account and MediaSoup WebRTC settings"""
    
    # Create default WhatsApp Business Account if it doesn't exist
    if not frappe.db.exists("WhatsApp Business Account", "WhatsApp Business Account"):
        try:
            whatsapp_account = frappe.new_doc("WhatsApp Business Account")
            whatsapp_account.phone_number_id = ""
            whatsapp_account.business_account_id = ""
            whatsapp_account.access_token = ""
            whatsapp_account.webhook_verify_token = frappe.generate_hash(length=32)
            whatsapp_account.is_enabled = False
            whatsapp_account.tier = "Free"
            whatsapp_account.bot_enabled = False
            whatsapp_account.ai_provider = "Claude"
            whatsapp_account.api_key = ""
            whatsapp_account.insert(ignore_permissions=True)
            
            print("✅ Default WhatsApp Business Account created")
            
        except Exception as e:
            print(f"❌ Error creating WhatsApp Business Account: {str(e)}")
    
    # Create default MediaSoup WebRTC Settings if it doesn't exist
    if not frappe.db.exists("MediaSoup WebRTC Settings", "MediaSoup WebRTC Settings"):
        try:
            mediasoup_settings = frappe.new_doc("MediaSoup WebRTC Settings")
            mediasoup_settings.server_host = "127.0.0.1"
            mediasoup_settings.server_port = 3000
            mediasoup_settings.rtc_min_port = 10000
            mediasoup_settings.rtc_max_port = 10100
            mediasoup_settings.is_enabled = False
            mediasoup_settings.worker_pool_size = 1
            mediasoup_settings.ice_servers = '''[
  {"urls": "stun:stun.l.google.com:19302"},
  {"urls": "stun:stun1.l.google.com:19302"}
]'''
            mediasoup_settings.recording_enabled = False
            mediasoup_settings.recording_path = "/var/recordings"
            mediasoup_settings.max_concurrent_sessions = 100
            mediasoup_settings.codec_preferences = '''[
  {
    "kind": "audio",
    "mimeType": "audio/opus",
    "clockRate": 48000,
    "channels": 2
  },
  {
    "kind": "audio",
    "mimeType": "audio/PCMU",
    "clockRate": 8000
  }
]'''
            mediasoup_settings.insert(ignore_permissions=True)
            
            print("✅ Default MediaSoup WebRTC Settings created")
            
        except Exception as e:
            print(f"❌ Error creating MediaSoup WebRTC Settings: {str(e)}")
    
    frappe.db.commit()
    print("✅ Default settings creation completed")