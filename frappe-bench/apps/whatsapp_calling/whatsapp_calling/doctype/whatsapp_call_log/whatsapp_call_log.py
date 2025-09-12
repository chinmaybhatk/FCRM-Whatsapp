import frappe
from frappe.model.document import Document
from datetime import datetime, timedelta
import json


class WhatsAppCallLog(Document):
    def before_insert(self):
        """Generate unique call ID and set initial status"""
        if not self.call_id:
            self.call_id = frappe.generate_hash(length=10).upper()
        
        if not self.status:
            self.status = "Initiated"
    
    def validate(self):
        """Validate call log data"""
        if self.end_time and self.start_time:
            # Calculate duration
            start = datetime.fromisoformat(str(self.start_time))
            end = datetime.fromisoformat(str(self.end_time))
            duration = end - start
            self.duration = duration.total_seconds()
    
    def start_call(self, agent_id=None):
        """Mark call as started"""
        self.status = "Ringing"
        self.start_time = datetime.now()
        
        if agent_id:
            self.agent = agent_id
            
        self.save(ignore_permissions=True)
        frappe.db.commit()
    
    def connect_call(self):
        """Mark call as connected"""
        self.status = "Connected"
        self.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Start recording if enabled for Professional/Enterprise tier
        if self.should_record_call():
            self.start_recording()
    
    def end_call(self, end_reason="user_hangup"):
        """End the call and calculate metrics"""
        self.status = "Ended"
        self.end_time = datetime.now()
        
        if self.start_time:
            duration = self.end_time - self.start_time
            self.duration = duration.total_seconds()
        
        # Stop recording if active
        if self.recording_url:
            self.stop_recording()
        
        # Generate transcript if available
        if self.recording_url and self.should_generate_transcript():
            self.generate_transcript()
        
        # Update lead scoring based on call interaction
        if self.lead:
            self.update_lead_score()
        
        self.save(ignore_permissions=True)
        frappe.db.commit()
        
        # Trigger analytics collection
        frappe.enqueue(
            "whatsapp_calling.analytics.metrics_collector.process_call_end",
            call_log=self.name,
            queue="short"
        )
    
    def should_record_call(self):
        """Check if call recording is enabled based on tier"""
        account = frappe.get_single("WhatsApp Business Account")
        return account and account.tier in ["Professional", "Enterprise"]
    
    def should_generate_transcript(self):
        """Check if transcript generation is enabled"""
        account = frappe.get_single("WhatsApp Business Account")
        return account and account.tier in ["Professional", "Enterprise"]
    
    def start_recording(self):
        """Start call recording via Valve WebRTC Gateway"""
        try:
            # Call Valve API to start recording
            import requests
            
            valve_config = frappe.get_single("Valve WebRTC Settings")
            headers = {
                'Authorization': f'Bearer {valve_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "session_id": self.session_id,
                "action": "start_recording",
                "format": "mp3",
                "quality": "high"
            }
            
            response = requests.post(
                f"{valve_config.base_url}/api/v1/recording/start",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                result = response.json()
                self.recording_url = result.get("recording_url")
                frappe.logger().info(f"Started recording for call {self.call_id}")
            else:
                frappe.logger().error(f"Failed to start recording: {response.text}")
                
        except Exception as e:
            frappe.logger().error(f"Error starting recording: {str(e)}")
    
    def stop_recording(self):
        """Stop call recording"""
        try:
            import requests
            
            valve_config = frappe.get_single("Valve WebRTC Settings")
            headers = {
                'Authorization': f'Bearer {valve_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                "session_id": self.session_id,
                "action": "stop_recording"
            }
            
            response = requests.post(
                f"{valve_config.base_url}/api/v1/recording/stop",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                frappe.logger().info(f"Stopped recording for call {self.call_id}")
            else:
                frappe.logger().error(f"Failed to stop recording: {response.text}")
                
        except Exception as e:
            frappe.logger().error(f"Error stopping recording: {str(e)}")
    
    def generate_transcript(self):
        """Generate AI-powered transcript from recording"""
        if not self.recording_url:
            return
        
        try:
            # Use Claude/OpenAI API for transcription
            frappe.enqueue(
                "whatsapp_calling.calling.recording_service.generate_transcript",
                call_log=self.name,
                recording_url=self.recording_url,
                queue="long"
            )
            
        except Exception as e:
            frappe.logger().error(f"Error generating transcript: {str(e)}")
    
    def update_lead_score(self):
        """Update lead scoring based on call interaction"""
        if not self.lead:
            return
        
        try:
            lead_doc = frappe.get_doc("Lead", self.lead)
            
            # Scoring logic based on call duration and outcome
            score_increase = 0
            
            if self.status == "Connected" and self.duration:
                if self.duration > 300:  # 5+ minutes
                    score_increase = 25
                elif self.duration > 120:  # 2+ minutes
                    score_increase = 15
                elif self.duration > 60:  # 1+ minute
                    score_increase = 10
                else:
                    score_increase = 5
            
            # Apply score increase
            current_score = lead_doc.get("lead_score") or 0
            new_score = min(current_score + score_increase, 100)
            
            frappe.db.set_value("Lead", self.lead, "lead_score", new_score)
            frappe.db.commit()
            
        except Exception as e:
            frappe.logger().error(f"Error updating lead score: {str(e)}")
    
    def get_call_quality_score(self):
        """Calculate call quality score based on metrics"""
        if not self.call_quality_score:
            return None
            
        try:
            quality_data = json.loads(self.call_quality_score) if isinstance(self.call_quality_score, str) else self.call_quality_score
            
            # Simple quality calculation
            mos_score = quality_data.get("mos_score", 3.5)
            packet_loss = quality_data.get("packet_loss", 0)
            latency = quality_data.get("latency", 50)
            jitter = quality_data.get("jitter", 10)
            
            # Normalize scores (0-100)
            mos_normalized = (mos_score / 5.0) * 100
            packet_loss_normalized = max(0, 100 - (packet_loss * 10))
            latency_normalized = max(0, 100 - (latency / 2))
            jitter_normalized = max(0, 100 - jitter)
            
            # Weighted average
            quality_score = (
                mos_normalized * 0.4 +
                packet_loss_normalized * 0.3 +
                latency_normalized * 0.2 +
                jitter_normalized * 0.1
            )
            
            return round(quality_score, 1)
            
        except Exception as e:
            frappe.logger().error(f"Error calculating quality score: {str(e)}")
            return None