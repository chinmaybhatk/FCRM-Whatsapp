import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    """Setup custom fields for WhatsApp integration"""
    
    custom_fields = {
        "Lead": [
            {
                "fieldname": "whatsapp_phone",
                "label": "WhatsApp Phone",
                "fieldtype": "Phone",
                "insert_after": "mobile_no",
                "in_list_view": 1
            },
            {
                "fieldname": "lead_score",
                "label": "Lead Score",
                "fieldtype": "Int",
                "insert_after": "status",
                "default": 0,
                "description": "AI-calculated lead qualification score (0-100)"
            },
            {
                "fieldname": "whatsapp_conversation_id",
                "label": "WhatsApp Conversation ID",
                "fieldtype": "Data",
                "insert_after": "whatsapp_phone",
                "hidden": 1
            }
        ],
        "Contact": [
            {
                "fieldname": "whatsapp_phone",
                "label": "WhatsApp Phone",
                "fieldtype": "Phone",
                "insert_after": "mobile_no",
                "in_list_view": 1
            },
            {
                "fieldname": "whatsapp_conversation_id",
                "label": "WhatsApp Conversation ID",
                "fieldtype": "Data",
                "insert_after": "whatsapp_phone",
                "hidden": 1
            }
        ],
        "Customer": [
            {
                "fieldname": "whatsapp_phone",
                "label": "WhatsApp Phone",
                "fieldtype": "Phone",
                "insert_after": "mobile_no",
                "in_list_view": 1
            },
            {
                "fieldname": "whatsapp_conversation_id",
                "label": "WhatsApp Conversation ID", 
                "fieldtype": "Data",
                "insert_after": "whatsapp_phone",
                "hidden": 1
            }
        ]
    }
    
    create_custom_fields(custom_fields, update=True)
    frappe.db.commit()
    
    print("WhatsApp custom fields created successfully")