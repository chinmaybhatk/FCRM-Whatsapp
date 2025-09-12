import frappe
import json
import requests
from datetime import datetime
import openai
import anthropic
from frappe.utils import cstr


class AIBotEngine:
    def __init__(self):
        self.settings = frappe.get_single("WhatsApp Business Account")
        self.ai_provider = self.settings.ai_provider if self.settings else "claude"
        
        if self.ai_provider == "claude":
            self.client = anthropic.Anthropic(api_key=self.settings.claude_api_key)
        elif self.ai_provider == "openai":
            openai.api_key = self.settings.openai_api_key
    
    def process_message(self, phone_number, message_body, conversation_state, message_id):
        """Process incoming message with AI bot"""
        try:
            # Get conversation context
            context = self.get_conversation_context(conversation_state)
            
            # Classify intent
            intent = self.classify_intent(message_body, context)
            
            # Generate response based on intent
            response = self.generate_response(intent, message_body, context)
            
            # Update conversation state
            self.update_conversation_state(conversation_state, intent, message_body, response)
            
            # Send response if not escalated to human
            if not conversation_state.is_escalated:
                self.send_bot_response(phone_number, response)
            
            # Check for lead qualification
            self.evaluate_lead_qualification(conversation_state, message_body)
            
        except Exception as e:
            frappe.logger().error(f"Error processing AI message: {str(e)}")
            # Send fallback response
            self.send_fallback_response(phone_number)
    
    def classify_intent(self, message_body, context):
        """Classify user intent using AI"""
        try:
            system_prompt = """
            You are an intent classifier for a CRM WhatsApp bot. Classify the user's message into one of these intents:
            - greeting: Hello, hi, good morning, etc.
            - product_inquiry: Questions about products/services
            - pricing: Questions about cost, price, rates
            - support: Technical support, help requests
            - appointment: Booking meetings, demos, calls
            - complaint: Issues, problems, dissatisfaction
            - lead_qualification: Ready to purchase, interested in buying
            - goodbye: Bye, thanks, end conversation
            - other: Anything else
            
            Respond with only the intent name.
            """
            
            if self.ai_provider == "claude":
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=50,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": f"Context: {context}\n\nMessage: {message_body}"
                    }]
                )
                intent = response.content[0].text.strip().lower()
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Context: {context}\n\nMessage: {message_body}"}
                    ],
                    max_tokens=50,
                    temperature=0.1
                )
                intent = response.choices[0].message.content.strip().lower()
            
            return intent if intent in ['greeting', 'product_inquiry', 'pricing', 'support', 'appointment', 'complaint', 'lead_qualification', 'goodbye', 'other'] else 'other'
            
        except Exception as e:
            frappe.logger().error(f"Error classifying intent: {str(e)}")
            return 'other'
    
    def generate_response(self, intent, message_body, context):
        """Generate appropriate response based on intent"""
        try:
            # Get company information
            company_info = self.get_company_info()
            
            system_prompt = f"""
            You are a helpful WhatsApp bot for {company_info['company_name']}. 
            
            Company Information:
            - Name: {company_info['company_name']}
            - Industry: {company_info['industry']}
            - Products/Services: {company_info['products']}
            - Contact: {company_info['contact']}
            
            Current Intent: {intent}
            Conversation Context: {context}
            
            Guidelines:
            - Be friendly and professional
            - Keep responses concise (under 160 characters when possible)
            - For pricing inquiries, mention that a sales representative will contact them
            - For appointments, offer to schedule a call or demo
            - For support issues, try to help or escalate to human agent
            - For lead qualification, gather contact details and requirements
            - Use emojis appropriately
            - Always end with a question to keep conversation flowing
            
            Respond naturally to the user's message.
            """
            
            if self.ai_provider == "claude":
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=200,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": message_body
                    }]
                )
                return response.content[0].text.strip()
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message_body}
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            frappe.logger().error(f"Error generating response: {str(e)}")
            return self.get_fallback_response(intent)
    
    def get_conversation_context(self, conversation_state):
        """Get conversation context for AI processing"""
        try:
            context_data = json.loads(conversation_state.context_data) if conversation_state.context_data else {}
            
            # Get recent messages
            recent_messages = frappe.get_all(
                "WhatsApp Message",
                filters={"conversation_id": conversation_state.conversation_id},
                fields=["message_body", "direction", "timestamp"],
                order_by="timestamp desc",
                limit=5
            )
            
            context = {
                "current_intent": conversation_state.current_intent,
                "lead_score": conversation_state.lead_score,
                "language": conversation_state.language,
                "recent_messages": recent_messages,
                "user_data": context_data.get("user_data", {}),
                "session_data": context_data.get("session_data", {})
            }
            
            return json.dumps(context)
            
        except Exception as e:
            frappe.logger().error(f"Error getting conversation context: {str(e)}")
            return "{}"
    
    def update_conversation_state(self, conversation_state, intent, message, response):
        """Update conversation state with new interaction"""
        try:
            conversation_state.current_intent = intent
            conversation_state.last_interaction = datetime.now()
            
            # Update context data
            context_data = json.loads(conversation_state.context_data) if conversation_state.context_data else {}
            
            # Track conversation history
            if "conversation_history" not in context_data:
                context_data["conversation_history"] = []
            
            context_data["conversation_history"].append({
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "bot_response": response,
                "intent": intent
            })
            
            # Keep only last 10 exchanges
            context_data["conversation_history"] = context_data["conversation_history"][-10:]
            
            # Update lead score based on intent
            self.update_lead_score(conversation_state, intent)
            
            conversation_state.context_data = json.dumps(context_data)
            conversation_state.save(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.logger().error(f"Error updating conversation state: {str(e)}")
    
    def update_lead_score(self, conversation_state, intent):
        """Update lead score based on interaction"""
        score_mapping = {
            "greeting": 5,
            "product_inquiry": 15,
            "pricing": 25,
            "appointment": 30,
            "lead_qualification": 40,
            "support": 5,
            "complaint": -5,
            "goodbye": 0,
            "other": 2
        }
        
        score_increase = score_mapping.get(intent, 0)
        new_score = min(conversation_state.lead_score + score_increase, 100)
        conversation_state.lead_score = max(new_score, 0)
    
    def send_bot_response(self, phone_number, response):
        """Send bot response via WhatsApp API"""
        try:
            account = frappe.get_single("WhatsApp Business Account")
            if not account:
                return
            
            headers = {
                'Authorization': f'Bearer {account.access_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": response
                }
            }
            
            url = f"https://graph.facebook.com/v17.0/{account.phone_number_id}/messages"
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                # Log bot message
                self.log_bot_message(phone_number, response, "sent", "delivered")
            else:
                frappe.logger().error(f"Failed to send bot response: {response.text}")
                
        except Exception as e:
            frappe.logger().error(f"Error sending bot response: {str(e)}")
    
    def log_bot_message(self, phone_number, message_body, direction, status):
        """Log bot message in WhatsApp Message"""
        try:
            message_log = frappe.new_doc("WhatsApp Message")
            message_log.conversation_id = f"CONV-{phone_number}-{datetime.now().strftime('%Y%m%d')}"
            message_log.from_number = self.get_business_phone_number()
            message_log.to_number = phone_number
            message_log.message_body = message_body
            message_log.message_type = "text"
            message_log.status = status
            message_log.direction = direction
            message_log.timestamp = datetime.now()
            message_log.is_bot_message = True
            
            message_log.insert(ignore_permissions=True)
            frappe.db.commit()
            
        except Exception as e:
            frappe.logger().error(f"Error logging bot message: {str(e)}")
    
    def evaluate_lead_qualification(self, conversation_state, message_body):
        """Evaluate if lead should be qualified based on conversation"""
        try:
            if conversation_state.lead_score >= 70:
                # High score - escalate to human agent
                self.escalate_to_human(conversation_state)
                
                # Create/update lead record
                self.create_qualified_lead(conversation_state)
                
        except Exception as e:
            frappe.logger().error(f"Error evaluating lead qualification: {str(e)}")
    
    def escalate_to_human(self, conversation_state):
        """Escalate conversation to human agent"""
        try:
            conversation_state.is_escalated = True
            conversation_state.escalated_at = datetime.now()
            conversation_state.save(ignore_permissions=True)
            
            # Notify sales team
            self.notify_sales_team(conversation_state)
            
            # Send escalation message to customer
            escalation_message = "Thank you for your interest! A member of our sales team will contact you shortly to discuss your requirements in detail. 😊"
            self.send_bot_response(conversation_state.phone_number, escalation_message)
            
        except Exception as e:
            frappe.logger().error(f"Error escalating to human: {str(e)}")
    
    def notify_sales_team(self, conversation_state):
        """Notify sales team about qualified lead"""
        try:
            # Create notification
            frappe.publish_realtime(
                event="qualified_lead",
                message={
                    "phone_number": conversation_state.phone_number,
                    "lead_score": conversation_state.lead_score,
                    "conversation_id": conversation_state.conversation_id,
                    "escalated_at": conversation_state.escalated_at.isoformat()
                },
                room="sales_team"
            )
            
            # Send email notification to sales team
            sales_users = frappe.get_all("User", 
                filters={"enabled": 1, "role_profile_name": "Sales User"},
                fields=["email"]
            )
            
            for user in sales_users:
                frappe.sendmail(
                    recipients=[user.email],
                    subject=f"Qualified WhatsApp Lead - {conversation_state.phone_number}",
                    message=f"""
                    <p>A new lead has been qualified from WhatsApp conversation:</p>
                    <ul>
                        <li>Phone: {conversation_state.phone_number}</li>
                        <li>Lead Score: {conversation_state.lead_score}</li>
                        <li>Conversation ID: {conversation_state.conversation_id}</li>
                        <li>Escalated At: {conversation_state.escalated_at}</li>
                    </ul>
                    <p>Please contact the lead as soon as possible.</p>
                    """
                )
                
        except Exception as e:
            frappe.logger().error(f"Error notifying sales team: {str(e)}")
    
    def create_qualified_lead(self, conversation_state):
        """Create or update lead record for qualified prospect"""
        try:
            # Check if lead already exists
            lead_name = frappe.db.get_value("Lead", {"mobile_no": conversation_state.phone_number}, "name")
            
            if lead_name:
                # Update existing lead
                lead = frappe.get_doc("Lead", lead_name)
                lead.status = "Qualified"
                lead.lead_score = conversation_state.lead_score
                lead.qualification_date = datetime.now().date()
            else:
                # Create new lead
                lead = frappe.new_doc("Lead")
                lead.first_name = f"WhatsApp Lead {conversation_state.phone_number[-4:]}"
                lead.mobile_no = conversation_state.phone_number
                lead.source = "WhatsApp Bot"
                lead.status = "Qualified"
                lead.lead_score = conversation_state.lead_score
                lead.qualification_date = datetime.now().date()
                lead.lead_owner = self.get_next_available_sales_user()
            
            # Add conversation summary to notes
            context_data = json.loads(conversation_state.context_data) if conversation_state.context_data else {}
            conversation_summary = self.generate_conversation_summary(context_data.get("conversation_history", []))
            
            lead.notes = f"Qualified via WhatsApp Bot\nLead Score: {conversation_state.lead_score}\nConversation Summary:\n{conversation_summary}"
            
            lead.save(ignore_permissions=True)
            frappe.db.commit()
            
            frappe.logger().info(f"Qualified lead {lead.name} from WhatsApp conversation")
            
        except Exception as e:
            frappe.logger().error(f"Error creating qualified lead: {str(e)}")
    
    def generate_conversation_summary(self, conversation_history):
        """Generate AI summary of conversation"""
        try:
            if not conversation_history:
                return "No conversation history available"
            
            # Create conversation text
            conversation_text = "\n".join([
                f"User: {msg['user_message']}\nBot: {msg['bot_response']}\n"
                for msg in conversation_history[-5:]  # Last 5 exchanges
            ])
            
            system_prompt = """
            Summarize this WhatsApp conversation between a user and a sales bot. 
            Focus on:
            - User's main interests/requirements
            - Key information gathered
            - Reasons for qualification
            - Next steps needed
            
            Keep it concise and actionable for sales team.
            """
            
            if self.ai_provider == "claude":
                response = self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=150,
                    system=system_prompt,
                    messages=[{
                        "role": "user",
                        "content": conversation_text
                    }]
                )
                return response.content[0].text.strip()
            else:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": conversation_text}
                    ],
                    max_tokens=150,
                    temperature=0.3
                )
                return response.choices[0].message.content.strip()
                
        except Exception as e:
            frappe.logger().error(f"Error generating conversation summary: {str(e)}")
            return "Error generating summary"
    
    def get_company_info(self):
        """Get company information for bot responses"""
        try:
            company = frappe.get_doc("Company", frappe.defaults.get_user_default("Company"))
            
            return {
                "company_name": company.company_name,
                "industry": getattr(company, 'industry', 'Technology'),
                "products": getattr(company, 'products', 'CRM Solutions'),
                "contact": getattr(company, 'phone_no', 'Contact Sales')
            }
            
        except Exception:
            return {
                "company_name": "Your Company",
                "industry": "Technology",
                "products": "CRM Solutions",
                "contact": "Contact Sales"
            }
    
    def get_fallback_response(self, intent):
        """Get fallback response when AI fails"""
        fallback_responses = {
            "greeting": "Hello! 👋 How can I help you today?",
            "product_inquiry": "I'd be happy to help with product information! Can you tell me more about what you're looking for?",
            "pricing": "For pricing information, I'll connect you with our sales team who can provide detailed quotes. What's your specific requirement?",
            "support": "I'm here to help! Can you describe the issue you're experiencing?",
            "appointment": "I'd be happy to help you schedule a meeting. When would be a good time for you?",
            "complaint": "I'm sorry to hear about the issue. Let me help you resolve this. Can you provide more details?",
            "lead_qualification": "Great! I'd love to learn more about your requirements. A sales representative will contact you soon.",
            "goodbye": "Thank you for contacting us! Feel free to reach out anytime. Have a great day! 😊",
            "other": "I understand. Let me connect you with someone who can better assist you."
        }
        
        return fallback_responses.get(intent, "Thank you for your message. Someone will get back to you soon!")
    
    def send_fallback_response(self, phone_number):
        """Send fallback response when AI processing fails"""
        fallback_message = "I apologize, but I'm having trouble processing your message right now. A team member will respond to you shortly. Thank you for your patience! 🙏"
        self.send_bot_response(phone_number, fallback_message)
    
    def get_business_phone_number(self):
        """Get business phone number"""
        account = frappe.get_single("WhatsApp Business Account")
        return account.phone_number if account else None
    
    def get_next_available_sales_user(self):
        """Get next available sales user for lead assignment"""
        try:
            # Simple round-robin assignment
            sales_users = frappe.get_all("User", 
                filters={"enabled": 1, "role_profile_name": "Sales User"},
                fields=["name"],
                order_by="last_login desc"
            )
            
            if sales_users:
                return sales_users[0].name
            else:
                return "Administrator"
                
        except Exception:
            return "Administrator"


@frappe.whitelist()
def process_message(phone_number, message_body, conversation_state, message_id):
    """Queue function to process message with AI bot"""
    try:
        engine = AIBotEngine()
        state_doc = frappe.get_doc("Bot Conversation State", conversation_state)
        engine.process_message(phone_number, message_body, state_doc, message_id)
        
    except Exception as e:
        frappe.logger().error(f"Error in bot message processing: {str(e)}")


@frappe.whitelist()
def escalate_conversation(phone_number, reason="user_request"):
    """Manually escalate conversation to human agent"""
    try:
        conversation_state = frappe.get_value("Bot Conversation State", {"phone_number": phone_number}, "name")
        
        if conversation_state:
            state_doc = frappe.get_doc("Bot Conversation State", conversation_state)
            engine = AIBotEngine()
            engine.escalate_to_human(state_doc)
            
            return {"success": True, "message": "Conversation escalated to human agent"}
        else:
            return {"success": False, "message": "Conversation not found"}
            
    except Exception as e:
        frappe.logger().error(f"Error escalating conversation: {str(e)}")
        return {"success": False, "message": str(e)}