import frappe
from frappe.model.document import Document
import json
import requests
import socket
import subprocess
import os


class MediaSoupWebRTCSettings(Document):
    def validate(self):
        """Validate MediaSoup settings"""
        if self.is_enabled:
            self.validate_ports()
            self.validate_ice_servers()
            self.validate_codec_preferences()
    
    def validate_ports(self):
        """Validate port ranges"""
        if self.rtc_min_port and self.rtc_max_port:
            if self.rtc_min_port >= self.rtc_max_port:
                frappe.throw("RTC Min Port must be less than RTC Max Port")
            
            if self.rtc_max_port - self.rtc_min_port < 50:
                frappe.throw("Port range should be at least 50 ports")
    
    def validate_ice_servers(self):
        """Validate ICE servers JSON format"""
        if self.ice_servers:
            try:
                ice_list = json.loads(self.ice_servers)
                if not isinstance(ice_list, list):
                    frappe.throw("ICE servers must be a JSON array")
                
                for server in ice_list:
                    if not isinstance(server, dict) or 'urls' not in server:
                        frappe.throw("Each ICE server must have 'urls' field")
                        
            except json.JSONDecodeError:
                frappe.throw("Invalid JSON format for ICE servers")
    
    def validate_codec_preferences(self):
        """Validate codec preferences JSON format"""
        if self.codec_preferences:
            try:
                codecs = json.loads(self.codec_preferences)
                if not isinstance(codecs, list):
                    frappe.throw("Codec preferences must be a JSON array")
                
                for codec in codecs:
                    required_fields = ['kind', 'mimeType', 'clockRate']
                    for field in required_fields:
                        if field not in codec:
                            frappe.throw(f"Codec entry must have '{field}' field")
                            
            except json.JSONDecodeError:
                frappe.throw("Invalid JSON format for codec preferences")
    
    def get_ice_servers(self):
        """Get ICE servers configuration for WebRTC"""
        ice_servers = []
        
        # Add configured ICE servers
        if self.ice_servers:
            try:
                configured_servers = json.loads(self.ice_servers)
                ice_servers.extend(configured_servers)
            except json.JSONDecodeError:
                pass
        
        return ice_servers
    
    def get_worker_config(self):
        """Get MediaSoup worker configuration"""
        config = {
            "logLevel": "warn",
            "logTags": [
                "info",
                "ice",
                "dtls",
                "rtp",
                "srtp",
                "rtcp"
            ],
            "rtcMinPort": self.rtc_min_port or 10000,
            "rtcMaxPort": self.rtc_max_port or 10100
        }
        
        # Add announced IP if configured
        if self.announced_ip:
            config["webRtcTransportOptions"] = {
                "listenIps": [
                    {
                        "ip": "0.0.0.0",
                        "announcedIp": self.announced_ip
                    }
                ]
            }
        else:
            config["webRtcTransportOptions"] = {
                "listenIps": [{"ip": "0.0.0.0"}]
            }
        
        return config
    
    def get_router_config(self):
        """Get MediaSoup router configuration with codec preferences"""
        try:
            codecs = json.loads(self.codec_preferences) if self.codec_preferences else []
        except json.JSONDecodeError:
            codecs = []
        
        # Default audio codecs if none specified
        if not codecs:
            codecs = [
                {
                    "kind": "audio",
                    "mimeType": "audio/opus",
                    "clockRate": 48000,
                    "channels": 2
                }
            ]
        
        return {"mediaCodecs": codecs}
    
    def get_mediasoup_config(self):
        """Get complete MediaSoup configuration for application"""
        return {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "worker_config": self.get_worker_config(),
            "router_config": self.get_router_config(),
            "ice_servers": self.get_ice_servers(),
            "recording_enabled": self.recording_enabled,
            "recording_path": self.recording_path,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "worker_pool_size": self.worker_pool_size or 1
        }
    
    def check_mediasoup_installation(self):
        """Check if MediaSoup is installed and available"""
        try:
            # Check if mediasoup npm package is available
            result = subprocess.run(
                ["node", "-e", "console.log(require('mediasoup').version)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return {
                    "installed": True,
                    "version": result.stdout.strip()
                }
            else:
                return {
                    "installed": False,
                    "error": result.stderr
                }
                
        except Exception as e:
            return {
                "installed": False,
                "error": str(e)
            }
    
    def get_public_ip(self):
        """Auto-detect public IP address"""
        try:
            # Try multiple services for redundancy
            services = [
                "https://api.ipify.org",
                "https://checkip.amazonaws.com",
                "https://icanhazip.com"
            ]
            
            for service in services:
                try:
                    response = requests.get(service, timeout=5)
                    if response.status_code == 200:
                        return response.text.strip()
                except:
                    continue
                    
            return None
            
        except Exception as e:
            frappe.logger().error(f"Error getting public IP: {str(e)}")
            return None
    
    def test_port_range(self):
        """Test if the configured port range is available"""
        if not self.rtc_min_port or not self.rtc_max_port:
            return False
            
        # Test a few random ports in the range
        import random
        test_ports = random.sample(
            range(self.rtc_min_port, min(self.rtc_max_port, self.rtc_min_port + 20)), 
            min(5, self.rtc_max_port - self.rtc_min_port)
        )
        
        for port in test_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                    sock.bind(('', port))
                    return True
            except OSError:
                continue
                
        return False