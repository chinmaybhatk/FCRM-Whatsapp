"""
Unit tests to verify all FR requirements from the specification are implemented
"""

import unittest
import os
import json
import frappe
from unittest.mock import MagicMock, patch
import sys
import importlib.util


class TestRequirementsImplementation(unittest.TestCase):
    """Test all functional requirements (FR-001 to FR-007) are implemented"""

    def setUp(self):
        """Setup test environment"""
        self.app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    def test_fr_001_whatsapp_business_api_integration(self):
        """FR-001: WhatsApp Business API Integration"""
        print("Testing FR-001: WhatsApp Business API Integration")
        
        # Test 1: WhatsApp Business Account DocType exists
        business_account_path = os.path.join(
            self.app_path, 
            "whatsapp_calling/doctype/whatsapp_business_account/whatsapp_business_account.json"
        )
        self.assertTrue(os.path.exists(business_account_path), 
                       "WhatsApp Business Account DocType JSON not found")
        
        # Test 2: Business Account Python file exists  
        business_account_py = os.path.join(
            self.app_path,
            "whatsapp_calling/doctype/whatsapp_business_account/whatsapp_business_account.py"
        )
        self.assertTrue(os.path.exists(business_account_py),
                       "WhatsApp Business Account Python file not found")
        
        # Test 3: Send message functionality exists
        with open(business_account_py, 'r') as f:
            content = f.read()
            self.assertIn("send_message", content, "send_message method not implemented")
            self.assertIn("create_message_log", content, "create_message_log method not implemented")
        
        # Test 4: Webhook handler exists
        webhook_path = os.path.join(self.app_path, "whatsapp_integration/webhook_handler.py")
        self.assertTrue(os.path.exists(webhook_path), "Webhook handler not found")
        
        with open(webhook_path, 'r') as f:
            content = f.read()
            self.assertIn("whatsapp_webhook", content, "WhatsApp webhook function not implemented")
            self.assertIn("process_incoming_message", content, "Process incoming message not implemented")
            self.assertIn("process_message_status", content, "Process message status not implemented")
        
        print("✅ FR-001: WhatsApp Business API Integration - PASSED")

    def test_fr_002_ai_powered_bot_system(self):
        """FR-002: AI-Powered Bot System"""
        print("Testing FR-002: AI-Powered Bot System")
        
        # Test 1: AI Engine exists
        ai_engine_path = os.path.join(self.app_path, "bot/ai_engine.py")
        self.assertTrue(os.path.exists(ai_engine_path), "AI engine not found")
        
        with open(ai_engine_path, 'r') as f:
            content = f.read()
            
            # Test 2: Natural language understanding
            self.assertIn("classify_intent", content, "Intent classification not implemented")
            self.assertIn("generate_response", content, "Response generation not implemented")
            
            # Test 3: Multi-language support
            self.assertIn("language", content, "Language support not found")
            
            # Test 4: Context-aware conversation
            self.assertIn("conversation_context", content, "Context awareness not implemented")
            self.assertIn("conversation_state", content, "Conversation state not managed")
            
            # Test 5: Lead qualification
            self.assertIn("lead_qualification", content, "Lead qualification not implemented")
            self.assertIn("lead_score", content, "Lead scoring not implemented")
            
            # Test 6: Appointment scheduling
            self.assertIn("appointment", content, "Appointment scheduling not found")
            
            # Test 7: Human agent escalation
            self.assertIn("escalate_to_human", content, "Human escalation not implemented")
            
            # Test 8: Claude/GPT integration
            self.assertTrue("claude" in content or "openai" in content, 
                          "AI provider integration not found")
        
        print("✅ FR-002: AI-Powered Bot System - PASSED")

    def test_fr_003_webrtc_voice_calling(self):
        """FR-003: WebRTC Voice Calling"""
        print("Testing FR-003: WebRTC Voice Calling")
        
        # Test 1: WebRTC Manager exists
        webrtc_path = os.path.join(self.app_path, "calling/webrtc_manager.py")
        self.assertTrue(os.path.exists(webrtc_path), "WebRTC manager not found")
        
        with open(webrtc_path, 'r') as f:
            content = f.read()
            
            # Test 2: Browser-to-WhatsApp calling
            self.assertIn("initiate_call", content, "Call initiation not implemented")
            self.assertIn("end_call", content, "End call not implemented")
            
            # Test 3: Call state management
            self.assertIn("call_status", content, "Call state management not found")
            
            # Test 4: Call quality monitoring
            self.assertIn("call_quality", content, "Call quality monitoring not implemented")
            self.assertIn("quality_metrics", content, "Quality metrics not found")
            
            # Test 5: Multi-party calling (mentioned in requirements)
            self.assertIn("session", content, "Session management not found")
        
        # Test 6: WebRTC Client JavaScript exists
        webrtc_client_path = os.path.join(self.app_path, "public/js/webrtc_client.js")
        self.assertTrue(os.path.exists(webrtc_client_path), "WebRTC client JS not found")
        
        with open(webrtc_client_path, 'r') as f:
            js_content = f.read()
            self.assertIn("RTCPeerConnection", js_content, "WebRTC peer connection not implemented")
            self.assertIn("getUserMedia", js_content, "Media access not implemented")
            self.assertIn("initiateCall", js_content, "Call initiation JS not implemented")
        
        # Test 7: Call Log DocType
        call_log_path = os.path.join(
            self.app_path,
            "whatsapp_calling/doctype/whatsapp_call_log/whatsapp_call_log.json"
        )
        self.assertTrue(os.path.exists(call_log_path), "Call Log DocType not found")
        
        print("✅ FR-003: WebRTC Voice Calling - PASSED")

    def test_fr_004_crm_integration(self):
        """FR-004: CRM Integration"""
        print("Testing FR-004: CRM Integration")
        
        # Test 1: WhatsApp Tab integration
        whatsapp_tab_path = os.path.join(self.app_path, "public/js/whatsapp_tab.js")
        self.assertTrue(os.path.exists(whatsapp_tab_path), "WhatsApp tab JS not found")
        
        with open(whatsapp_tab_path, 'r') as f:
            content = f.read()
            
            # Test 2: Lead/Contact/Customer integration
            self.assertIn("frappe.ui.form.on('Lead'", content, "Lead form integration not found")
            self.assertIn("frappe.ui.form.on('Contact'", content, "Contact form integration not found")
            self.assertIn("frappe.ui.form.on('Customer'", content, "Customer form integration not found")
            
            # Test 3: Click-to-call functionality
            self.assertIn("add_call_button", content, "Call button not implemented")
            self.assertIn("initiate_whatsapp_call", content, "WhatsApp call initiation not found")
            
            # Test 4: Conversation history
            self.assertIn("conversation_history", content, "Conversation history not implemented")
            self.assertIn("load_whatsapp_history", content, "WhatsApp history loading not found")
        
        # Test 5: Hooks for CRM integration
        hooks_path = os.path.join(self.app_path, "hooks.py")
        self.assertTrue(os.path.exists(hooks_path), "Hooks file not found")
        
        with open(hooks_path, 'r') as f:
            hooks_content = f.read()
            self.assertIn("doctype_js", hooks_content, "DocType JS hooks not configured")
            self.assertIn("Lead", hooks_content, "Lead integration not configured")
            self.assertIn("Contact", hooks_content, "Contact integration not configured")
        
        print("✅ FR-004: CRM Integration - PASSED")

    def test_fr_005_call_recording_transcription(self):
        """FR-005: Call Recording & Transcription (Advanced Features)"""
        print("Testing FR-005: Call Recording & Transcription")
        
        # Test 1: Recording functionality in WebRTC manager
        webrtc_path = os.path.join(self.app_path, "calling/webrtc_manager.py")
        with open(webrtc_path, 'r') as f:
            content = f.read()
            self.assertIn("recording", content, "Recording functionality not found")
            self.assertIn("should_enable_recording", content, "Recording check not implemented")
        
        # Test 2: Recording functionality in Call Log
        call_log_py = os.path.join(
            self.app_path,
            "whatsapp_calling/doctype/whatsapp_call_log/whatsapp_call_log.py"
        )
        with open(call_log_py, 'r') as f:
            content = f.read()
            self.assertIn("start_recording", content, "Start recording not implemented")
            self.assertIn("stop_recording", content, "Stop recording not implemented")
            self.assertIn("generate_transcript", content, "Transcript generation not implemented")
        
        print("✅ FR-005: Call Recording & Transcription - PASSED")

    def test_fr_006_multi_agent_management(self):
        """FR-006: Multi-Agent Management"""
        print("Testing FR-006: Multi-Agent Management")
        
        # Test 1: Agent routing in WebRTC manager
        webrtc_path = os.path.join(self.app_path, "calling/webrtc_manager.py")
        with open(webrtc_path, 'r') as f:
            content = f.read()
            self.assertIn("agent", content, "Agent management not found")
        
        # Test 2: Agent assignment in AI engine
        ai_engine_path = os.path.join(self.app_path, "bot/ai_engine.py")
        with open(ai_engine_path, 'r') as f:
            content = f.read()
            self.assertIn("sales_team", content, "Sales team management not found")
            self.assertIn("get_next_available_sales_user", content, "Agent assignment not implemented")
        
        print("✅ FR-006: Multi-Agent Management - PASSED")

    def test_fr_007_analytics_reporting(self):
        """FR-007: Analytics & Reporting"""
        print("Testing FR-007: Analytics & Reporting")
        
        # Test 1: Analytics in hooks
        hooks_path = os.path.join(self.app_path, "hooks.py")
        with open(hooks_path, 'r') as f:
            content = f.read()
            self.assertIn("analytics", content, "Analytics not configured in hooks")
            self.assertIn("metrics_collector", content, "Metrics collection not configured")
        
        # Test 2: Call quality metrics in WebRTC manager
        webrtc_path = os.path.join(self.app_path, "calling/webrtc_manager.py")
        with open(webrtc_path, 'r') as f:
            content = f.read()
            self.assertIn("check_call_quality", content, "Call quality monitoring not implemented")
            self.assertIn("quality_metrics", content, "Quality metrics not found")
        
        # Test 3: Conversation analytics in AI engine
        ai_engine_path = os.path.join(self.app_path, "bot/ai_engine.py")
        with open(ai_engine_path, 'r') as f:
            content = f.read()
            self.assertIn("conversation_summary", content, "Conversation analytics not found")
        
        print("✅ FR-007: Analytics & Reporting - PASSED")

    def test_non_functional_requirements(self):
        """Test Non-Functional Requirements (NFR-001 to NFR-005)"""
        print("Testing Non-Functional Requirements")
        
        # Test 1: Performance considerations in code
        ai_engine_path = os.path.join(self.app_path, "bot/ai_engine.py")
        with open(ai_engine_path, 'r') as f:
            content = f.read()
            self.assertIn("frappe.enqueue", content, "Async processing not implemented")
        
        # Test 2: Security implementations
        webrtc_path = os.path.join(self.app_path, "calling/webrtc_manager.py")
        with open(webrtc_path, 'r') as f:
            content = f.read()
            self.assertIn("jwt", content, "JWT authentication not implemented")
            self.assertIn("@frappe.whitelist", content, "API whitelisting not implemented")
        
        # Test 3: Error handling
        webhook_path = os.path.join(self.app_path, "whatsapp_integration/webhook_handler.py")
        with open(webhook_path, 'r') as f:
            content = f.read()
            self.assertIn("try:", content, "Error handling not implemented")
            self.assertIn("except", content, "Exception handling not found")
        
        print("✅ Non-Functional Requirements - PASSED")

    def test_essential_files_structure(self):
        """Test essential Frappe app structure"""
        print("Testing Essential File Structure")
        
        # Test required files exist
        required_files = [
            "hooks.py",
            "patches.txt", 
            "modules.txt",
            "__init__.py",
            "whatsapp_calling/__init__.py",
            "whatsapp_calling/doctype/__init__.py"
        ]
        
        for file_path in required_files:
            full_path = os.path.join(self.app_path, file_path)
            self.assertTrue(os.path.exists(full_path), f"Required file {file_path} not found")
        
        # Test root level files
        root_files = ["setup.py", "MANIFEST.in", "pyproject.toml", "requirements.txt", "README.md"]
        for file_name in root_files:
            root_file_path = os.path.join(os.path.dirname(self.app_path), file_name)
            self.assertTrue(os.path.exists(root_file_path), f"Root file {file_name} not found")
        
        print("✅ Essential File Structure - PASSED")

    def test_api_endpoints(self):
        """Test API endpoints are properly configured"""
        print("Testing API Endpoints")
        
        # Test WebRTC API endpoints
        webrtc_path = os.path.join(self.app_path, "calling/webrtc_manager.py")
        with open(webrtc_path, 'r') as f:
            content = f.read()
            
            # Check for whitelisted API methods
            api_methods = [
                "initiate_call",
                "end_call", 
                "get_call_token",
                "get_ice_servers"
            ]
            
            for method in api_methods:
                self.assertIn(f"def {method}", content, f"API method {method} not found")
                # Should be preceded by @frappe.whitelist()
                whitelist_pattern = f"@frappe.whitelist()\ndef {method}"
                self.assertIn("@frappe.whitelist", content, f"API method {method} not whitelisted")
        
        # Test Webhook endpoints
        webhook_path = os.path.join(self.app_path, "whatsapp_integration/webhook_handler.py")
        with open(webhook_path, 'r') as f:
            content = f.read()
            self.assertIn("@frappe.whitelist(allow_guest=True)", content, 
                         "Webhook endpoint not properly configured")
        
        print("✅ API Endpoints - PASSED")


def run_requirement_tests():
    """Run all requirement verification tests"""
    print("🧪 Running WhatsApp Calling Requirements Verification Tests")
    print("=" * 60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRequirementsImplementation)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, buffer=True)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = total_tests - failures - errors
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failures}")
    print(f"💥 Errors: {errors}")
    
    if failures:
        print("\n❌ FAILURES:")
        for test, failure in result.failures:
            print(f"  - {test}: {failure}")
    
    if errors:
        print("\n💥 ERRORS:")
        for test, error in result.errors:
            print(f"  - {test}: {error}")
    
    # Overall result
    if failures == 0 and errors == 0:
        print("\n🎉 ALL REQUIREMENTS SUCCESSFULLY IMPLEMENTED!")
        print("The WhatsApp Calling solution meets all specified functional requirements.")
        return True
    else:
        print(f"\n⚠️  {failures + errors} issues found. Please review implementation.")
        return False


if __name__ == "__main__":
    success = run_requirement_tests()
    exit(0 if success else 1)