import frappe
from frappe.model.document import Document
from datetime import datetime


class WhatsAppMessage(Document):
    def before_insert(self):
        """Auto-generate message ID if not provided"""
        if not self.message_id:
            self.message_id = frappe.generate_hash(length=15)
        
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    def validate(self):
        """Validate message data"""
        if not self.conversation_id:
            # Auto-generate conversation ID based on phone numbers
            phone_numbers = sorted([self.from_number, self.to_number])
            date_str = datetime.now().strftime('%Y%m%d')
            self.conversation_id = f"CONV-{'-'.join(phone_numbers)}-{date_str}"
    
    def after_insert(self):
        """Post-processing after message insertion"""
        # Link to CRM records if not already linked
        if not (self.lead or self.contact or self.customer):
            self.link_to_crm_record()
        
        # Emit real-time update
        frappe.publish_realtime(
            event="whatsapp_message_created",
            message={
                "message_id": self.message_id,
                "conversation_id": self.conversation_id,
                "from_number": self.from_number,
                "to_number": self.to_number,
                "direction": self.direction,
                "message_body": self.message_body,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None
            },
            room="whatsapp_messages"
        )
    
    def link_to_crm_record(self):
        """Auto-link message to existing CRM records"""
        try:
            # Determine the customer's phone number
            customer_phone = self.from_number if self.direction == "received" else self.to_number
            
            # Check for existing Lead
            lead = frappe.db.get_value("Lead", {
                "mobile_no": customer_phone
            }, "name")
            
            if lead:
                self.lead = lead
                self.save(ignore_permissions=True)
                return
            
            # Check for existing Contact  
            contact = frappe.db.get_value("Contact", {
                "mobile_no": customer_phone
            }, "name")
            
            if contact:
                self.contact = contact
                self.save(ignore_permissions=True)
                return
                
            # Check for existing Customer
            customer = frappe.db.get_value("Customer", {
                "mobile_no": customer_phone
            }, "name")
            
            if customer:
                self.customer = customer
                self.save(ignore_permissions=True)
                return
            
        except Exception as e:
            frappe.logger().error(f"Error linking message to CRM: {str(e)}")
    
    def mark_as_read(self):
        """Mark message as read"""
        if self.direction == "received" and self.status != "read":
            self.status = "read"
            self.save(ignore_permissions=True)
            frappe.db.commit()
    
    def get_conversation_messages(self, limit=50):
        """Get all messages in this conversation"""
        return frappe.get_all(
            "WhatsApp Message",
            filters={"conversation_id": self.conversation_id},
            fields=[
                "message_id", "from_number", "to_number", "message_body", 
                "direction", "status", "timestamp", "message_type", "media_url"
            ],
            order_by="timestamp asc",
            limit=limit
        )
    
    @staticmethod
    def get_conversation_by_phone(phone_number, limit=50):
        """Get conversation messages for a specific phone number"""
        return frappe.get_all(
            "WhatsApp Message", 
            filters=[
                ["from_number", "=", phone_number],
                ["to_number", "=", phone_number]
            ],
            fields=[
                "message_id", "from_number", "to_number", "message_body",
                "direction", "status", "timestamp", "message_type", "media_url",
                "conversation_id"
            ],
            order_by="timestamp desc",
            limit=limit
        )
    
    @staticmethod
    def update_message_status(message_id, new_status):
        """Update message delivery status"""
        try:
            frappe.db.set_value("WhatsApp Message", message_id, "status", new_status)
            frappe.db.commit()
            
            # Emit real-time status update
            frappe.publish_realtime(
                event="whatsapp_message_status_update",
                message={
                    "message_id": message_id,
                    "status": new_status
                },
                room="whatsapp_messages" 
            )
            
        except Exception as e:
            frappe.logger().error(f"Error updating message status: {str(e)}")