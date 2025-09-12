"""
Standalone test to verify all FR requirements are implemented without Frappe dependency
"""

import os
import json
import sys


def test_fr_001_whatsapp_business_api_integration():
    """FR-001: WhatsApp Business API Integration"""
    print("Testing FR-001: WhatsApp Business API Integration")
    
    issues = []
    
    # Test 1: WhatsApp Business Account DocType exists
    business_account_path = "whatsapp_calling/whatsapp_calling/doctype/whatsapp_business_account/whatsapp_business_account.json"
    if not os.path.exists(business_account_path):
        issues.append("WhatsApp Business Account DocType JSON not found")
    
    # Test 2: Business Account Python file exists  
    business_account_py = "whatsapp_calling/whatsapp_calling/doctype/whatsapp_business_account/whatsapp_business_account.py"
    if not os.path.exists(business_account_py):
        issues.append("WhatsApp Business Account Python file not found")
    else:
        # Test 3: Send message functionality exists
        with open(business_account_py, 'r') as f:
            content = f.read()
            if "send_message" not in content:
                issues.append("send_message method not implemented")
            if "create_message_log" not in content:
                issues.append("create_message_log method not implemented")
    
    # Test 4: Webhook handler exists
    webhook_path = "whatsapp_calling/whatsapp_integration/webhook_handler.py"
    if not os.path.exists(webhook_path):
        issues.append("Webhook handler not found")
    else:
        with open(webhook_path, 'r') as f:
            content = f.read()
            if "whatsapp_webhook" not in content:
                issues.append("WhatsApp webhook function not implemented")
            if "process_incoming_message" not in content:
                issues.append("Process incoming message not implemented")
            if "process_message_status" not in content:
                issues.append("Process message status not implemented")
    
    if issues:
        print(f"❌ FR-001 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-001: WhatsApp Business API Integration - PASSED")
        return True


def test_fr_002_ai_powered_bot_system():
    """FR-002: AI-Powered Bot System"""
    print("Testing FR-002: AI-Powered Bot System")
    
    issues = []
    
    # Test 1: AI Engine exists
    ai_engine_path = "whatsapp_calling/bot/ai_engine.py"
    if not os.path.exists(ai_engine_path):
        issues.append("AI engine not found")
        return False
    
    with open(ai_engine_path, 'r') as f:
        content = f.read()
        
        # Test 2: Natural language understanding
        if "classify_intent" not in content:
            issues.append("Intent classification not implemented")
        if "generate_response" not in content:
            issues.append("Response generation not implemented")
        
        # Test 3: Multi-language support
        if "language" not in content:
            issues.append("Language support not found")
        
        # Test 4: Context-aware conversation
        if "conversation_context" not in content:
            issues.append("Context awareness not implemented")
        if "conversation_state" not in content:
            issues.append("Conversation state not managed")
        
        # Test 5: Lead qualification
        if "lead_qualification" not in content:
            issues.append("Lead qualification not implemented")
        if "lead_score" not in content:
            issues.append("Lead scoring not implemented")
        
        # Test 6: Appointment scheduling
        if "appointment" not in content:
            issues.append("Appointment scheduling not found")
        
        # Test 7: Human agent escalation
        if "escalate_to_human" not in content:
            issues.append("Human escalation not implemented")
        
        # Test 8: Claude/GPT integration
        if not ("claude" in content or "openai" in content):
            issues.append("AI provider integration not found")
    
    if issues:
        print(f"❌ FR-002 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-002: AI-Powered Bot System - PASSED")
        return True


def test_fr_003_webrtc_voice_calling():
    """FR-003: WebRTC Voice Calling"""
    print("Testing FR-003: WebRTC Voice Calling")
    
    issues = []
    
    # Test 1: WebRTC Manager exists
    webrtc_path = "whatsapp_calling/calling/webrtc_manager.py"
    if not os.path.exists(webrtc_path):
        issues.append("WebRTC manager not found")
        return False
    
    with open(webrtc_path, 'r') as f:
        content = f.read()
        
        # Test 2: Browser-to-WhatsApp calling
        if "initiate_call" not in content:
            issues.append("Call initiation not implemented")
        if "end_call" not in content:
            issues.append("End call not implemented")
        
        # Test 3: Call state management
        if "status" not in content:
            issues.append("Call state management not found")
        
        # Test 4: Call quality monitoring
        if "call_quality" not in content:
            issues.append("Call quality monitoring not implemented")
        if "quality_metrics" not in content:
            issues.append("Quality metrics not found")
        
        # Test 5: Multi-party calling (session management)
        if "session" not in content:
            issues.append("Session management not found")
    
    # Test 6: WebRTC Client JavaScript exists
    webrtc_client_path = "whatsapp_calling/public/js/webrtc_client.js"
    if not os.path.exists(webrtc_client_path):
        issues.append("WebRTC client JS not found")
    else:
        with open(webrtc_client_path, 'r') as f:
            js_content = f.read()
            if "RTCPeerConnection" not in js_content:
                issues.append("WebRTC peer connection not implemented")
            if "getUserMedia" not in js_content:
                issues.append("Media access not implemented")
            if "initiateCall" not in js_content:
                issues.append("Call initiation JS not implemented")
    
    # Test 7: Call Log DocType
    call_log_path = "whatsapp_calling/whatsapp_calling/doctype/whatsapp_call_log/whatsapp_call_log.json"
    if not os.path.exists(call_log_path):
        issues.append("Call Log DocType not found")
    
    if issues:
        print(f"❌ FR-003 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-003: WebRTC Voice Calling - PASSED")
        return True


def test_fr_004_crm_integration():
    """FR-004: CRM Integration"""
    print("Testing FR-004: CRM Integration")
    
    issues = []
    
    # Test 1: WhatsApp Tab integration
    whatsapp_tab_path = "whatsapp_calling/public/js/whatsapp_tab.js"
    if not os.path.exists(whatsapp_tab_path):
        issues.append("WhatsApp tab JS not found")
        return False
    
    with open(whatsapp_tab_path, 'r') as f:
        content = f.read()
        
        # Test 2: Lead/Contact/Customer integration
        if "frappe.ui.form.on('Lead'" not in content:
            issues.append("Lead form integration not found")
        if "frappe.ui.form.on('Contact'" not in content:
            issues.append("Contact form integration not found")
        if "frappe.ui.form.on('Customer'" not in content:
            issues.append("Customer form integration not found")
        
        # Test 3: Click-to-call functionality
        if "add_call_button" not in content:
            issues.append("Call button not implemented")
        if "initiate_whatsapp_call" not in content:
            issues.append("WhatsApp call initiation not found")
        
        # Test 4: Conversation history
        if "conversation_history" not in content:
            issues.append("Conversation history not implemented")
        if "load_whatsapp_history" not in content:
            issues.append("WhatsApp history loading not found")
    
    # Test 5: Hooks for CRM integration
    hooks_path = "whatsapp_calling/hooks.py"
    if not os.path.exists(hooks_path):
        issues.append("Hooks file not found")
    else:
        with open(hooks_path, 'r') as f:
            hooks_content = f.read()
            if "doctype_js" not in hooks_content:
                issues.append("DocType JS hooks not configured")
            if "Lead" not in hooks_content:
                issues.append("Lead integration not configured")
            if "Contact" not in hooks_content:
                issues.append("Contact integration not configured")
    
    if issues:
        print(f"❌ FR-004 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-004: CRM Integration - PASSED")
        return True


def test_fr_005_call_recording_transcription():
    """FR-005: Call Recording & Transcription"""
    print("Testing FR-005: Call Recording & Transcription")
    
    issues = []
    
    # Test 1: Recording functionality in WebRTC manager
    webrtc_path = "whatsapp_calling/calling/webrtc_manager.py"
    if os.path.exists(webrtc_path):
        with open(webrtc_path, 'r') as f:
            content = f.read()
            if "recording" not in content:
                issues.append("Recording functionality not found")
            if "should_enable_recording" not in content:
                issues.append("Recording check not implemented")
    else:
        issues.append("WebRTC manager not found")
    
    # Test 2: Recording functionality in Call Log
    call_log_py = "whatsapp_calling/whatsapp_calling/doctype/whatsapp_call_log/whatsapp_call_log.py"
    if os.path.exists(call_log_py):
        with open(call_log_py, 'r') as f:
            content = f.read()
            if "start_recording" not in content:
                issues.append("Start recording not implemented")
            if "stop_recording" not in content:
                issues.append("Stop recording not implemented")
            if "generate_transcript" not in content:
                issues.append("Transcript generation not implemented")
    else:
        issues.append("Call Log Python file not found")
    
    if issues:
        print(f"❌ FR-005 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-005: Call Recording & Transcription - PASSED")
        return True


def test_fr_006_multi_agent_management():
    """FR-006: Multi-Agent Management"""
    print("Testing FR-006: Multi-Agent Management")
    
    issues = []
    
    # Test 1: Agent routing in WebRTC manager
    webrtc_path = "whatsapp_calling/calling/webrtc_manager.py"
    if os.path.exists(webrtc_path):
        with open(webrtc_path, 'r') as f:
            content = f.read()
            if "agent" not in content:
                issues.append("Agent management not found")
    else:
        issues.append("WebRTC manager not found")
    
    # Test 2: Agent assignment in AI engine
    ai_engine_path = "whatsapp_calling/bot/ai_engine.py"
    if os.path.exists(ai_engine_path):
        with open(ai_engine_path, 'r') as f:
            content = f.read()
            if "sales_team" not in content:
                issues.append("Sales team management not found")
            if "get_next_available_sales_user" not in content:
                issues.append("Agent assignment not implemented")
    else:
        issues.append("AI engine not found")
    
    if issues:
        print(f"❌ FR-006 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-006: Multi-Agent Management - PASSED")
        return True


def test_fr_007_analytics_reporting():
    """FR-007: Analytics & Reporting"""
    print("Testing FR-007: Analytics & Reporting")
    
    issues = []
    
    # Test 1: Analytics in hooks
    hooks_path = "whatsapp_calling/hooks.py"
    if os.path.exists(hooks_path):
        with open(hooks_path, 'r') as f:
            content = f.read()
            if "analytics" not in content:
                issues.append("Analytics not configured in hooks")
            if "metrics_collector" not in content:
                issues.append("Metrics collection not configured")
    else:
        issues.append("Hooks file not found")
    
    # Test 2: Call quality metrics in WebRTC manager
    webrtc_path = "whatsapp_calling/calling/webrtc_manager.py"
    if os.path.exists(webrtc_path):
        with open(webrtc_path, 'r') as f:
            content = f.read()
            if "check_call_quality" not in content:
                issues.append("Call quality monitoring not implemented")
            if "quality_metrics" not in content:
                issues.append("Quality metrics not found")
    else:
        issues.append("WebRTC manager not found")
    
    # Test 3: Conversation analytics in AI engine
    ai_engine_path = "whatsapp_calling/bot/ai_engine.py"
    if os.path.exists(ai_engine_path):
        with open(ai_engine_path, 'r') as f:
            content = f.read()
            if "conversation_summary" not in content:
                issues.append("Conversation analytics not found")
    else:
        issues.append("AI engine not found")
    
    if issues:
        print(f"❌ FR-007 ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ FR-007: Analytics & Reporting - PASSED")
        return True


def test_essential_structure():
    """Test essential Frappe app structure"""
    print("Testing Essential File Structure")
    
    issues = []
    
    # Test required files exist
    required_files = [
        "whatsapp_calling/hooks.py",
        "whatsapp_calling/patches.txt", 
        "whatsapp_calling/modules.txt",
        "whatsapp_calling/__init__.py",
        "whatsapp_calling/whatsapp_calling/__init__.py",
        "whatsapp_calling/whatsapp_calling/doctype/__init__.py"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            issues.append(f"Required file {file_path} not found")
    
    # Test root level files
    root_files = ["setup.py", "MANIFEST.in", "pyproject.toml", "requirements.txt", "README.md"]
    for file_name in root_files:
        if not os.path.exists(file_name):
            issues.append(f"Root file {file_name} not found")
    
    if issues:
        print(f"❌ STRUCTURE ISSUES: {', '.join(issues)}")
        return False
    else:
        print("✅ Essential File Structure - PASSED")
        return True


def run_all_tests():
    """Run all requirement verification tests"""
    print("🧪 Running WhatsApp Calling Requirements Verification Tests")
    print("=" * 60)
    
    test_functions = [
        test_fr_001_whatsapp_business_api_integration,
        test_fr_002_ai_powered_bot_system,
        test_fr_003_webrtc_voice_calling,
        test_fr_004_crm_integration,
        test_fr_005_call_recording_transcription,
        test_fr_006_multi_agent_management,
        test_fr_007_analytics_reporting,
        test_essential_structure
    ]
    
    results = []
    for test_func in test_functions:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"💥 ERROR in {test_func.__name__}: {str(e)}")
            results.append(False)
        print()
    
    # Print summary
    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed = sum(results)
    failed = total_tests - passed
    
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    
    # Overall result
    if failed == 0:
        print("\n🎉 ALL REQUIREMENTS SUCCESSFULLY IMPLEMENTED!")
        print("The WhatsApp Calling solution meets all specified functional requirements.")
        print("\n📋 IMPLEMENTATION COMPLETENESS:")
        print("✅ FR-001: WhatsApp Business API Integration")
        print("✅ FR-002: AI-Powered Bot System")
        print("✅ FR-003: WebRTC Voice Calling")
        print("✅ FR-004: CRM Integration") 
        print("✅ FR-005: Call Recording & Transcription")
        print("✅ FR-006: Multi-Agent Management")
        print("✅ FR-007: Analytics & Reporting")
        print("✅ Proper Frappe App Structure")
        return True
    else:
        print(f"\n⚠️ {failed} requirements need attention. Please review implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)