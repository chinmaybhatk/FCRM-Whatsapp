import frappe
from frappe.model.document import Document
import json
import requests
import websocket
import ssl


class JanusWebRTCSettings(Document):
    def validate(self):
        """Validate Janus settings"""
        if self.is_enabled:
            self.validate_janus_connection()
            self.validate_stun_servers()
    
    def validate_janus_connection(self):
        """Test connection to Janus Gateway"""
        try:
            # Test HTTP Admin API if available
            if self.janus_server_url.startswith('http'):
                admin_url = self.janus_server_url.replace('/janus', '/admin')
                response = requests.get(f"{admin_url}/info", timeout=5)
                if response.status_code != 200:
                    frappe.throw(f"Cannot connect to Janus server: {response.status_code}")
            else:
                # Test WebSocket connection
                ws_url = self.janus_server_url
                try:
                    ws = websocket.create_connection(ws_url, timeout=5, sslopt={"cert_reqs": ssl.CERT_NONE})
                    ws.close()
                except Exception as e:
                    frappe.throw(f"Cannot connect to Janus WebSocket: {str(e)}")
                    
        except requests.RequestException as e:
            frappe.throw(f"Failed to validate Janus connection: {str(e)}")
    
    def validate_stun_servers(self):
        """Validate STUN servers JSON format"""
        if self.stun_servers:
            try:
                stun_list = json.loads(self.stun_servers)
                if not isinstance(stun_list, list):
                    frappe.throw("STUN servers must be a JSON array")
                
                for server in stun_list:
                    if not isinstance(server, dict) or 'urls' not in server:
                        frappe.throw("Each STUN server must have 'urls' field")
                        
            except json.JSONDecodeError:
                frappe.throw("Invalid JSON format for STUN servers")
    
    def get_ice_servers(self):
        """Get ICE servers configuration for WebRTC"""
        ice_servers = []
        
        # Add STUN servers
        if self.stun_servers:
            try:
                stun_servers = json.loads(self.stun_servers)
                ice_servers.extend(stun_servers)
            except json.JSONDecodeError:
                pass
        
        # Add TURN server if configured
        if self.turn_server_url and self.turn_username and self.turn_credential:
            ice_servers.append({
                "urls": self.turn_server_url,
                "username": self.turn_username,
                "credential": self.turn_credential
            })
        
        return ice_servers
    
    def create_janus_session(self):
        """Create a new Janus session"""
        try:
            if self.janus_server_url.startswith('http'):
                # HTTP API
                response = requests.post(
                    f"{self.janus_server_url}",
                    json={"janus": "create", "transaction": frappe.generate_hash()},
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("data", {}).get("id")
            else:
                # WebSocket will be handled in the frontend
                return frappe.generate_hash()
                
        except Exception as e:
            frappe.logger().error(f"Error creating Janus session: {str(e)}")
            return None
    
    def get_janus_config(self):
        """Get complete Janus configuration for frontend"""
        return {
            "server_url": self.janus_server_url,
            "api_secret": self.janus_api_secret if self.janus_api_secret else None,
            "ice_servers": self.get_ice_servers(),
            "recording_enabled": self.recording_enabled,
            "max_concurrent_sessions": self.max_concurrent_sessions
        }
    
    @frappe.whitelist()
    def get_janus_config_for_frontend(self):
        """API endpoint for frontend to get Janus configuration"""
        if not self.is_enabled:
            frappe.throw("Janus WebRTC is not enabled")
        return self.get_janus_config()