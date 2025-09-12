import frappe
import json
import requests
from datetime import datetime, timedelta
import uuid
import jwt
from frappe.utils import now_datetime, cstr


class WebRTCManager:
    def __init__(self):
        self.valve_settings = frappe.get_single("Valve WebRTC Settings")
        if not self.valve_settings:
            frappe.throw("Valve WebRTC Settings not configured")
    
    def initiate_call(self, to_number, from_agent, lead_id=None):
        """Initiate a WebRTC call to WhatsApp number"""
        try:
            # Generate session ID
            session_id = str(uuid.uuid4())
            
            # Create call log entry
            call_log = frappe.new_doc("WhatsApp Call Log")
            call_log.call_id = frappe.generate_hash(length=10).upper()
            call_log.session_id = session_id
            call_log.from_number = from_agent
            call_log.to_number = to_number
            call_log.direction = "Outgoing"
            call_log.status = "Initiated"
            call_log.agent = from_agent
            
            if lead_id:
                call_log.lead = lead_id
            
            call_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
            # Request WebRTC session from Valve
            session_data = self.create_webrtc_session(session_id, from_agent, to_number)
            
            if session_data:
                # Update call log with session data
                call_log.session_id = session_data.get("session_id")
                call_log.start_call(from_agent)
                
                return {
                    "success": True,
                    "call_id": call_log.call_id,
                    "session_id": session_id,
                    "ice_servers": session_data.get("ice_servers", []),
                    "session_token": session_data.get("session_token"),
                    "call_log": call_log.name
                }
            else:
                call_log.status = "Failed"
                call_log.save(ignore_permissions=True)
                frappe.throw("Failed to create WebRTC session")
                
        except Exception as e:
            frappe.logger().error(f"Error initiating call: {str(e)}")
            frappe.throw(f"Failed to initiate call: {str(e)}")
    
    def create_webrtc_session(self, session_id, caller_id, callee_id):
        """Create WebRTC session via Valve Gateway"""
        try:
            headers = {
                'Authorization': f'Bearer {self.valve_settings.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "session_id": session_id,
                "caller": {"id": caller_id, "type": "agent"},
                "callee": {"id": callee_id, "type": "whatsapp"},
                "features": {
                    "recording": self.should_enable_recording(),
                    "transcription": self.should_enable_transcription(),
                    "analytics": True
                },
                "quality_settings": {
                    "codec": "opus",
                    "bitrate": 32000,
                    "sample_rate": 48000
                }
            }
            
            response = requests.post(
                f"{self.valve_settings.base_url}/api/v1/session/create",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                frappe.logger().error(f"Valve API Error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            frappe.logger().error(f"Error creating WebRTC session: {str(e)}")
            return None
    
    def end_call(self, session_id, end_reason="user_hangup"):
        """End WebRTC call session"""
        try:
            headers = {
                'Authorization': f'Bearer {self.valve_settings.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "session_id": session_id,
                "end_reason": end_reason
            }
            
            response = requests.post(
                f"{self.valve_settings.base_url}/api/v1/session/end",
                json=payload,
                headers=headers
            )
            
            # Update call log
            call_log = frappe.get_value("WhatsApp Call Log", {"session_id": session_id}, "name")
            if call_log:
                call_doc = frappe.get_doc("WhatsApp Call Log", call_log)
                call_doc.end_call(end_reason)
            
            return response.status_code == 200
            
        except Exception as e:
            frappe.logger().error(f"Error ending call: {str(e)}")
            return False
    
    def get_call_token(self, session_id, user_id):
        """Generate JWT token for WebRTC authentication"""
        try:
            payload = {
                "session_id": session_id,
                "user": user_id,
                "exp": datetime.utcnow() + timedelta(minutes=60),
                "iss": "frappe-webrtc",
                "sub": user_id
            }
            
            token = jwt.encode(
                payload,
                self.valve_settings.jwt_secret,
                algorithm="HS256"
            )
            
            return token
            
        except Exception as e:
            frappe.logger().error(f"Error generating call token: {str(e)}")
            return None
    
    def get_ice_servers(self):
        """Get ICE servers configuration from Valve"""
        try:
            headers = {
                'Authorization': f'Bearer {self.valve_settings.api_key}'
            }
            
            response = requests.get(
                f"{self.valve_settings.base_url}/api/v1/ice-servers",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json().get("ice_servers", [])
            else:
                # Fallback ICE servers
                return [
                    {"urls": "stun:stun.valve.yourcompany.com:443"},
                    {
                        "urls": "turn:turn.valve.yourcompany.com:443",
                        "username": "webrtc_user",
                        "credential": "webrtc_pass"
                    }
                ]
                
        except Exception as e:
            frappe.logger().error(f"Error getting ICE servers: {str(e)}")
            return []
    
    def check_call_quality(self):
        """Monitor and check call quality for active sessions"""
        try:
            # Get active calls
            active_calls = frappe.get_all(
                "WhatsApp Call Log",
                filters={"status": ["in", ["Ringing", "Connected"]]},
                fields=["name", "session_id", "call_id"]
            )
            
            for call in active_calls:
                quality_data = self.get_session_quality(call.session_id)
                if quality_data:
                    self.update_call_quality(call.name, quality_data)
            
        except Exception as e:
            frappe.logger().error(f"Error checking call quality: {str(e)}")
    
    def get_session_quality(self, session_id):
        """Get real-time quality metrics for a session"""
        try:
            headers = {
                'Authorization': f'Bearer {self.valve_settings.api_key}'
            }
            
            response = requests.get(
                f"{self.valve_settings.base_url}/api/v1/session/{session_id}/quality",
                headers=headers
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            frappe.logger().error(f"Error getting session quality: {str(e)}")
            return None
    
    def update_call_quality(self, call_log_name, quality_data):
        """Update call log with quality metrics"""
        try:
            call_log = frappe.get_doc("WhatsApp Call Log", call_log_name)
            call_log.call_quality_score = json.dumps(quality_data)
            call_log.save(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.logger().error(f"Error updating call quality: {str(e)}")
    
    def should_enable_recording(self):
        """Check if recording should be enabled based on tier"""
        account = frappe.get_single("WhatsApp Business Account")
        return account and account.tier in ["Professional", "Enterprise"]
    
    def should_enable_transcription(self):
        """Check if transcription should be enabled"""
        account = frappe.get_single("WhatsApp Business Account")
        return account and account.tier in ["Professional", "Enterprise"]
    
    def handle_call_event(self, event_data):
        """Handle incoming call events from Valve Gateway"""
        try:
            session_id = event_data.get("session_id")
            event_type = event_data.get("event_type")
            
            call_log = frappe.get_value("WhatsApp Call Log", {"session_id": session_id}, "name")
            if not call_log:
                frappe.logger().warning(f"No call log found for session {session_id}")
                return
            
            call_doc = frappe.get_doc("WhatsApp Call Log", call_log)
            
            if event_type == "call_ringing":
                call_doc.status = "Ringing"
            elif event_type == "call_answered":
                call_doc.connect_call()
            elif event_type == "call_ended":
                end_reason = event_data.get("end_reason", "unknown")
                call_doc.end_call(end_reason)
            elif event_type == "quality_update":
                quality_data = event_data.get("quality_metrics")
                if quality_data:
                    call_doc.call_quality_score = json.dumps(quality_data)
                    call_doc.save(ignore_permissions=True)
            
            frappe.db.commit()
            
        except Exception as e:
            frappe.logger().error(f"Error handling call event: {str(e)}")


@frappe.whitelist()
def initiate_call(to_number, lead_id=None):
    """API endpoint to initiate WebRTC call"""
    manager = WebRTCManager()
    from_agent = frappe.session.user
    return manager.initiate_call(to_number, from_agent, lead_id)


@frappe.whitelist()
def end_call(session_id, end_reason="user_hangup"):
    """API endpoint to end WebRTC call"""
    manager = WebRTCManager()
    return manager.end_call(session_id, end_reason)


@frappe.whitelist()
def get_call_token(session_id):
    """API endpoint to get call authentication token"""
    manager = WebRTCManager()
    user_id = frappe.session.user
    return manager.get_call_token(session_id, user_id)


@frappe.whitelist()
def get_ice_servers():
    """API endpoint to get ICE servers configuration"""
    manager = WebRTCManager()
    return manager.get_ice_servers()