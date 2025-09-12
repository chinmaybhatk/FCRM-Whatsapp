import frappe
import json
import hashlib
import hmac
from datetime import datetime
import requests


@frappe.whitelist(allow_guest=True)
def whatsapp_webhook():
    """Handle incoming WhatsApp webhook messages"""
    try:
        # Verify webhook signature
        if not verify_webhook_signature():
            frappe.throw("Invalid webhook signature", frappe.AuthenticationError)
        
        data = json.loads(frappe.request.data)
        
        # Handle webhook verification
        if frappe.request.method == "GET":
            return handle_webhook_verification()
        
        # Process webhook data
        if "messages" in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            process_incoming_message(data)
        
        if "statuses" in data.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}):
            process_message_status(data)
        
        return {"status": "success"}
        
    except Exception as e:
        frappe.logger().error(f"WhatsApp webhook error: {str(e)}")
        frappe.log_error(f"WhatsApp webhook error: {str(e)}", "WhatsApp Webhook")
        return {"status": "error", "message": str(e)}


def handle_webhook_verification():
    """Handle WhatsApp webhook verification"""
    verify_token = frappe.request.args.get("hub.verify_token")
    challenge = frappe.request.args.get("hub.challenge")
    
    account = frappe.get_single("WhatsApp Business Account")
    if account and verify_token == account.webhook_verify_token:
        return challenge
    else:
        frappe.throw("Invalid verify token", frappe.AuthenticationError)


def verify_webhook_signature():
    """Verify webhook signature from WhatsApp"""
    try:
        account = frappe.get_single("WhatsApp Business Account")
        if not account or not account.webhook_verify_token:
            return False
        
        signature = frappe.request.headers.get("X-Hub-Signature-256", "").replace("sha256=", "")
        expected_signature = hmac.new(
            account.webhook_verify_token.encode(),
            frappe.request.data,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
        
    except Exception as e:
        frappe.logger().error(f"Signature verification error: {str(e)}")
        return False


def process_incoming_message(data):
    """Process incoming WhatsApp message"""
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        for message in messages:
            phone_number = message.get("from")
            message_body = get_message_text(message)
            message_type = message.get("type", "text")
            message_id = message.get("id")
            timestamp = datetime.fromtimestamp(int(message.get("timestamp", 0)))
            
            # Create message log
            create_message_log(
                phone_number=phone_number,
                message_body=message_body,
                message_type=message_type,
                message_id=message_id,
                direction="received",
                status="delivered",
                timestamp=timestamp
            )
            
            # Process with AI bot if enabled
            process_with_bot(phone_number, message_body, message_id)
            
            # Emit real-time update
            emit_message_update(phone_number, message_body, "received")
            
    except Exception as e:
        frappe.logger().error(f"Error processing incoming message: {str(e)}")


def process_message_status(data):
    """Process message delivery status updates"""
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        statuses = value.get("statuses", [])
        
        for status in statuses:
            message_id = status.get("id")
            new_status = status.get("status")  # sent, delivered, read, failed
            timestamp = datetime.fromtimestamp(int(status.get("timestamp", 0)))
            
            # Update message status
            update_message_status(message_id, new_status, timestamp)
            
    except Exception as e:
        frappe.logger().error(f"Error processing message status: {str(e)}")


def get_message_text(message):
    """Extract text from different message types"""
    message_type = message.get("type", "text")
    
    if message_type == "text":
        return message.get("text", {}).get("body", "")
    elif message_type == "image":
        caption = message.get("image", {}).get("caption", "")
        return f"[Image] {caption}".strip()
    elif message_type == "audio":
        return "[Audio Message]"
    elif message_type == "video":
        caption = message.get("video", {}).get("caption", "")
        return f"[Video] {caption}".strip()
    elif message_type == "document":
        filename = message.get("document", {}).get("filename", "")
        return f"[Document] {filename}".strip()
    else:
        return f"[{message_type.title()} Message]"


def create_message_log(phone_number, message_body, message_type, message_id, direction, status, timestamp):
    """Create WhatsApp Message log entry"""
    try:
        # Check if message already exists
        existing = frappe.db.get_value("WhatsApp Message", {"message_id": message_id}, "name")
        if existing:
            return existing
        
        message_log = frappe.new_doc("WhatsApp Message")
        message_log.message_id = message_id
        message_log.conversation_id = f"CONV-{phone_number}-{datetime.now().strftime('%Y%m%d')}"
        message_log.from_number = phone_number if direction == "received" else get_business_phone_number()
        message_log.to_number = get_business_phone_number() if direction == "received" else phone_number
        message_log.message_body = message_body
        message_log.message_type = message_type
        message_log.status = status
        message_log.direction = direction
        message_log.timestamp = timestamp
        
        # Link to Lead/Contact/Customer if exists
        link_to_crm_record(message_log, phone_number)
        
        message_log.insert(ignore_permissions=True)
        frappe.db.commit()
        
        return message_log.name
        
    except Exception as e:
        frappe.logger().error(f"Error creating message log: {str(e)}")
        return None


def link_to_crm_record(message_log, phone_number):
    """Link message to existing CRM records"""
    try:
        # Format phone number for searching
        formatted_phone = format_phone_number(phone_number)
        
        # Check for Lead
        lead = frappe.db.get_value("Lead", {
            "mobile_no": ["in", [phone_number, formatted_phone]]
        }, "name")
        
        if lead:
            message_log.lead = lead
            return
        
        # Check for Contact
        contact = frappe.db.get_value("Contact", {
            "mobile_no": ["in", [phone_number, formatted_phone]]
        }, "name")
        
        if contact:
            message_log.contact = contact
            return
        
        # Check for Customer
        customer = frappe.db.get_value("Customer", {
            "mobile_no": ["in", [phone_number, formatted_phone]]
        }, "name")
        
        if customer:
            message_log.customer = customer
            return
        
        # Create new Lead if no existing record
        if not lead and not contact and not customer:
            create_lead_from_whatsapp(phone_number, message_log.message_body)
            
    except Exception as e:
        frappe.logger().error(f"Error linking to CRM record: {str(e)}")


def create_lead_from_whatsapp(phone_number, first_message):
    """Create new Lead from WhatsApp conversation"""
    try:
        lead = frappe.new_doc("Lead")
        lead.first_name = f"WhatsApp Lead {phone_number[-4:]}"
        lead.mobile_no = phone_number
        lead.source = "WhatsApp"
        lead.status = "Lead"
        lead.lead_owner = get_default_lead_owner()
        lead.notes = f"Auto-created from WhatsApp. First message: {first_message}"
        
        lead.insert(ignore_permissions=True)
        frappe.db.commit()
        
        frappe.logger().info(f"Created new lead {lead.name} from WhatsApp {phone_number}")
        return lead.name
        
    except Exception as e:
        frappe.logger().error(f"Error creating lead from WhatsApp: {str(e)}")
        return None


def process_with_bot(phone_number, message_body, message_id):
    """Process message with AI bot if enabled"""
    try:
        account = frappe.get_single("WhatsApp Business Account")
        if not account or not account.enable_bot:
            return
        
        # Get or create bot conversation state
        conversation_state = get_bot_conversation_state(phone_number)
        
        # Process with AI bot
        frappe.enqueue(
            "whatsapp_calling.bot.ai_engine.process_message",
            phone_number=phone_number,
            message_body=message_body,
            conversation_state=conversation_state,
            message_id=message_id,
            queue="short"
        )
        
    except Exception as e:
        frappe.logger().error(f"Error processing with bot: {str(e)}")


def get_bot_conversation_state(phone_number):
    """Get or create bot conversation state"""
    try:
        state_name = frappe.db.get_value("Bot Conversation State", {"phone_number": phone_number}, "name")
        
        if state_name:
            return frappe.get_doc("Bot Conversation State", state_name)
        else:
            # Create new conversation state
            state = frappe.new_doc("Bot Conversation State")
            state.phone_number = phone_number
            state.conversation_id = f"CONV-{phone_number}-{datetime.now().strftime('%Y%m%d')}"
            state.current_intent = "greeting"
            state.context_data = "{}"
            state.lead_score = 0
            state.language = "en"
            state.is_active = True
            
            state.insert(ignore_permissions=True)
            frappe.db.commit()
            
            return state
            
    except Exception as e:
        frappe.logger().error(f"Error getting bot conversation state: {str(e)}")
        return None


def update_message_status(message_id, new_status, timestamp):
    """Update message delivery status"""
    try:
        message_log = frappe.get_value("WhatsApp Message", {"message_id": message_id}, "name")
        
        if message_log:
            frappe.db.set_value("WhatsApp Message", message_log, {
                "status": new_status,
                "modified": timestamp
            })
            frappe.db.commit()
            
            # Emit real-time status update
            emit_status_update(message_id, new_status)
            
    except Exception as e:
        frappe.logger().error(f"Error updating message status: {str(e)}")


def emit_message_update(phone_number, message_body, direction):
    """Emit real-time message update via Socket.IO"""
    try:
        frappe.publish_realtime(
            event="whatsapp_message_received",
            message={
                "phone_number": phone_number,
                "message_body": message_body,
                "direction": direction,
                "timestamp": datetime.now().isoformat()
            },
            room="whatsapp_messages"
        )
        
    except Exception as e:
        frappe.logger().error(f"Error emitting message update: {str(e)}")


def emit_status_update(message_id, status):
    """Emit real-time status update"""
    try:
        frappe.publish_realtime(
            event="whatsapp_message_status_update",
            message={
                "message_id": message_id,
                "status": status,
                "timestamp": datetime.now().isoformat()
            },
            room="whatsapp_messages"
        )
        
    except Exception as e:
        frappe.logger().error(f"Error emitting status update: {str(e)}")


def format_phone_number(phone_number):
    """Format phone number for consistent searching"""
    # Remove non-digit characters
    digits_only = ''.join(filter(str.isdigit, phone_number))
    
    # Add country code if missing
    if len(digits_only) == 10:
        return f"+1{digits_only}"  # Default to US
    elif len(digits_only) == 11 and digits_only.startswith('1'):
        return f"+{digits_only}"
    elif not digits_only.startswith('+'):
        return f"+{digits_only}"
    
    return phone_number


def get_business_phone_number():
    """Get business phone number from settings"""
    account = frappe.get_single("WhatsApp Business Account")
    return account.phone_number if account else None


def get_default_lead_owner():
    """Get default lead owner for auto-created leads"""
    # Try to get from WhatsApp settings first
    account = frappe.get_single("WhatsApp Business Account")
    if account and account.default_lead_owner:
        return account.default_lead_owner
    
    # Fallback to first sales user
    sales_users = frappe.get_all("User", 
        filters={"enabled": 1, "user_type": "System User"},
        fields=["name"],
        limit=1
    )
    
    return sales_users[0].name if sales_users else "Administrator"