import frappe
from frappe.model.document import Document
from datetime import datetime
import json


class BotConversationState(Document):
    def before_insert(self):
        """Initialize conversation state"""
        if not self.conversation_id:
            self.conversation_id = f"CONV-{self.phone_number}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        if not self.context_data:
            self.context_data = json.dumps({
                "conversation_history": [],
                "user_data": {},
                "session_data": {}
            })
        
        if not self.last_interaction:
            self.last_interaction = datetime.now()
    
    def update_context(self, new_data):
        """Update conversation context data"""
        try:
            current_data = json.loads(self.context_data) if self.context_data else {}
            current_data.update(new_data)
            self.context_data = json.dumps(current_data)
            self.last_interaction = datetime.now()
            self.save(ignore_permissions=True)
        except Exception as e:
            frappe.logger().error(f"Error updating context: {str(e)}")
    
    def add_conversation_entry(self, user_message, bot_response, intent):
        """Add new conversation entry to history"""
        try:
            context_data = json.loads(self.context_data) if self.context_data else {}
            
            if "conversation_history" not in context_data:
                context_data["conversation_history"] = []
            
            context_data["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "bot_response": bot_response,
                "intent": intent
            })
            
            # Keep only last 20 conversation entries
            context_data["conversation_history"] = context_data["conversation_history"][-20:]
            
            self.context_data = json.dumps(context_data)
            self.current_intent = intent
            self.last_interaction = datetime.now()
            self.save(ignore_permissions=True)
            
        except Exception as e:
            frappe.logger().error(f"Error adding conversation entry: {str(e)}")
    
    def escalate(self, reason="user_request"):
        """Escalate conversation to human agent"""
        self.is_escalated = True
        self.escalated_at = datetime.now()
        self.escalated_reason = reason
        self.is_active = False
        self.save(ignore_permissions=True)
        
        # Create notification for sales team
        frappe.publish_realtime(
            event="conversation_escalated",
            message={
                "phone_number": self.phone_number,
                "conversation_id": self.conversation_id,
                "lead_score": self.lead_score,
                "reason": reason
            },
            room="sales_team"
        )
    
    def get_conversation_summary(self):
        """Get AI-generated conversation summary"""
        try:
            context_data = json.loads(self.context_data) if self.context_data else {}
            history = context_data.get("conversation_history", [])
            
            if not history:
                return "No conversation history available"
            
            # Simple summary based on intents and messages
            intents = [entry.get("intent", "unknown") for entry in history]
            intent_counts = {}
            for intent in intents:
                intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            
            summary = f"Lead Score: {self.lead_score}/100\\n"
            summary += f"Top Interests: {', '.join([intent for intent, count in top_intents])}\\n"
            summary += f"Total Interactions: {len(history)}\\n"
            
            if self.is_escalated:
                summary += f"Escalated: {self.escalated_reason}\\n"
            
            return summary
            
        except Exception as e:
            frappe.logger().error(f"Error generating summary: {str(e)}")
            return "Error generating summary"
    
    @staticmethod
    def get_or_create(phone_number):
        """Get existing conversation state or create new one"""
        existing = frappe.db.get_value(
            "Bot Conversation State", 
            {"phone_number": phone_number, "is_active": 1},
            "name"
        )
        
        if existing:
            return frappe.get_doc("Bot Conversation State", existing)
        else:
            # Create new conversation state
            new_state = frappe.new_doc("Bot Conversation State")
            new_state.phone_number = phone_number
            new_state.current_intent = "greeting"
            new_state.lead_score = 0
            new_state.language = "en"
            new_state.is_active = True
            new_state.insert(ignore_permissions=True)
            return new_state
    
    @staticmethod
    def cleanup_inactive_conversations():
        """Cleanup old inactive conversations (called via scheduler)"""
        try:
            # Mark conversations inactive after 24 hours of no activity
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            inactive_conversations = frappe.get_all(
                "Bot Conversation State",
                filters={
                    "is_active": 1,
                    "last_interaction": ["<", cutoff_time]
                },
                fields=["name"]
            )
            
            for conv in inactive_conversations:
                frappe.db.set_value("Bot Conversation State", conv.name, "is_active", 0)
            
            frappe.db.commit()
            frappe.logger().info(f"Cleaned up {len(inactive_conversations)} inactive conversations")
            
        except Exception as e:
            frappe.logger().error(f"Error cleaning up conversations: {str(e)}")