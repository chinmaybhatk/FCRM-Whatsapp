import frappe
from frappe.model.document import Document
import requests
import json
from datetime import datetime


class WhatsAppBusinessAccount(Document):
    def validate(self):
        """Validate the WhatsApp Business Account configuration"""
        if self.is_active:
            self.validate_credentials()
    
    def validate_credentials(self):
        """Validate WhatsApp Business API credentials"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test API connection
            url = f"https://graph.facebook.com/v17.0/{self.business_account_id}"
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code != 200:
                frappe.throw(f"Invalid credentials: {response.text}")
                
        except Exception as e:
            frappe.throw(f"Failed to validate credentials: {str(e)}")
    
    def send_message(self, to_number, message_body, message_type="text"):
        """Send message via WhatsApp Business API"""
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": message_type,
                message_type: {
                    "body": message_body
                }
            }
            
            url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Log successful message
                self.create_message_log(to_number, message_body, "sent", "delivered")
                return response.json()
            else:
                frappe.throw(f"Failed to send message: {response.text}")
                
        except Exception as e:
            self.create_message_log(to_number, message_body, "sent", "failed")
            frappe.throw(f"Error sending message: {str(e)}")
    
    def create_message_log(self, phone_number, message_body, direction, status):
        """Create WhatsApp Message log"""
        message_log = frappe.new_doc("WhatsApp Message")
        message_log.conversation_id = f"CONV-{phone_number}-{datetime.now().strftime('%Y%m%d')}"
        message_log.from_number = self.phone_number if direction == "sent" else phone_number
        message_log.to_number = phone_number if direction == "sent" else self.phone_number
        message_log.message_body = message_body
        message_log.message_type = "text"
        message_log.status = status
        message_log.direction = direction
        message_log.timestamp = datetime.now()
        
        # Link to Lead/Contact if exists
        lead = frappe.db.get_value("Lead", {"mobile_no": phone_number}, "name")
        contact = frappe.db.get_value("Contact", {"mobile_no": phone_number}, "name")
        
        if lead:
            message_log.lead = lead
        elif contact:
            message_log.contact = contact
            
        message_log.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return message_log.name