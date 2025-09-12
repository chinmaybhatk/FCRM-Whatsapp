frappe.ui.form.on('Lead', {
    refresh: function(frm) {
        if (frm.doc.mobile_no) {
            add_whatsapp_tab(frm);
            add_call_button(frm);
        }
    }
});

frappe.ui.form.on('Contact', {
    refresh: function(frm) {
        if (frm.doc.mobile_no) {
            add_whatsapp_tab(frm);
            add_call_button(frm);
        }
    }
});

frappe.ui.form.on('Customer', {
    refresh: function(frm) {
        if (frm.doc.mobile_no) {
            add_whatsapp_tab(frm);
            add_call_button(frm);
        }
    }
});

function add_whatsapp_tab(frm) {
    if (!frm.doc.mobile_no) return;
    
    // Add WhatsApp tab
    frm.add_custom_button(__('WhatsApp'), function() {
        open_whatsapp_dialog(frm);
    }, __('Communication'));
    
    // Load WhatsApp conversation history
    load_whatsapp_history(frm);
}

function add_call_button(frm) {
    if (!frm.doc.mobile_no) return;
    
    frm.add_custom_button(__('Call'), function() {
        initiate_whatsapp_call(frm);
    }, __('Communication'));
}

function open_whatsapp_dialog(frm) {
    const dialog = new frappe.ui.Dialog({
        title: __('WhatsApp Conversation'),
        size: 'large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'conversation_area',
                options: '<div id="whatsapp-conversation" style="height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px;"></div>'
            },
            {
                fieldtype: 'Text Editor',
                fieldname: 'message',
                label: __('Message'),
                reqd: 1
            }
        ],
        primary_action_label: __('Send'),
        primary_action: function() {
            send_whatsapp_message(frm, dialog);
        }
    });
    
    dialog.show();
    load_conversation_in_dialog(frm, dialog);
}

function load_whatsapp_history(frm) {
    frappe.call({
        method: 'whatsapp_calling.whatsapp_integration.api_client.get_conversation_history',
        args: {
            phone_number: frm.doc.mobile_no,
            doctype: frm.doctype,
            docname: frm.docname
        },
        callback: function(r) {
            if (r.message && r.message.length > 0) {
                add_whatsapp_timeline_entries(frm, r.message);
            }
        }
    });
}

function load_conversation_in_dialog(frm, dialog) {
    frappe.call({
        method: 'whatsapp_calling.whatsapp_integration.api_client.get_conversation_history',
        args: {
            phone_number: frm.doc.mobile_no,
            limit: 50
        },
        callback: function(r) {
            if (r.message) {
                render_conversation(r.message, '#whatsapp-conversation');
            }
        }
    });
}

function render_conversation(messages, container) {
    const conversationDiv = $(container);
    conversationDiv.empty();
    
    messages.forEach(message => {
        const messageClass = message.direction === 'sent' ? 'sent' : 'received';
        const messageHtml = `
            <div class="message ${messageClass}" style="margin-bottom: 10px;">
                <div class="message-content" style="
                    background: ${message.direction === 'sent' ? '#dcf8c6' : '#ffffff'};
                    padding: 8px 12px;
                    border-radius: 8px;
                    max-width: 70%;
                    margin-left: ${message.direction === 'sent' ? 'auto' : '0'};
                    margin-right: ${message.direction === 'sent' ? '0' : 'auto'};
                    border: 1px solid #e1e1e1;
                ">
                    <div class="message-text">${message.message_body}</div>
                    <div class="message-time" style="font-size: 11px; color: #999; margin-top: 4px;">
                        ${moment(message.timestamp).format('MMM DD, HH:mm')}
                        ${message.direction === 'sent' ? '<span class="message-status">' + get_status_icon(message.status) + '</span>' : ''}
                    </div>
                </div>
            </div>
        `;
        conversationDiv.append(messageHtml);
    });
    
    // Scroll to bottom
    conversationDiv.scrollTop(conversationDiv[0].scrollHeight);
}

function get_status_icon(status) {
    switch (status) {
        case 'sent':
            return '<i class="fa fa-check" style="color: #999;"></i>';
        case 'delivered':
            return '<i class="fa fa-check-double" style="color: #999;"></i>';
        case 'read':
            return '<i class="fa fa-check-double" style="color: #4fc3f7;"></i>';
        case 'failed':
            return '<i class="fa fa-exclamation-triangle" style="color: #f44336;"></i>';
        default:
            return '';
    }
}

function send_whatsapp_message(frm, dialog) {
    const message = dialog.get_value('message');
    if (!message) {
        frappe.msgprint(__('Please enter a message'));
        return;
    }
    
    frappe.call({
        method: 'whatsapp_calling.whatsapp_integration.api_client.send_message',
        args: {
            to_number: frm.doc.mobile_no,
            message: message,
            doctype: frm.doctype,
            docname: frm.docname
        },
        callback: function(r) {
            if (r.message && r.message.success) {
                frappe.show_alert({
                    message: __('Message sent successfully'),
                    indicator: 'green'
                });
                
                dialog.set_value('message', '');
                load_conversation_in_dialog(frm, dialog);
                
                // Add timeline entry
                frm.timeline.insert_comment('Communication', __('WhatsApp message sent: {0}', [message]));
            } else {
                frappe.show_alert({
                    message: __('Failed to send message'),
                    indicator: 'red'
                });
            }
        }
    });
}

function initiate_whatsapp_call(frm) {
    if (!window.whatsappWebRTC) {
        frappe.msgprint(__('WebRTC client not available'));
        return;
    }
    
    const phone_number = frm.doc.mobile_no;
    const lead_id = frm.doctype === 'Lead' ? frm.docname : null;
    
    frappe.confirm(
        __('Initiate WhatsApp call to {0}?', [phone_number]),
        function() {
            window.whatsappWebRTC.initiateCall(phone_number, lead_id)
                .then(success => {
                    if (success) {
                        // Add timeline entry
                        frm.timeline.insert_comment('Communication', __('WhatsApp call initiated to {0}', [phone_number]));
                    }
                })
                .catch(error => {
                    frappe.msgprint(__('Failed to initiate call: {0}', [error.message]));
                });
        }
    );
}

function add_whatsapp_timeline_entries(frm, messages) {
    messages.forEach(message => {
        const direction = message.direction === 'sent' ? 'Outgoing' : 'Incoming';
        const content = `${direction} WhatsApp message: ${message.message_body.substring(0, 100)}${message.message_body.length > 100 ? '...' : ''}`;
        
        frm.timeline.insert_comment('Communication', content, message.timestamp);
    });
}

// Auto-refresh conversation every 30 seconds if dialog is open
let conversationRefreshInterval;

$(document).on('show.bs.modal', function() {
    const dialog = $('.modal:visible').last();
    if (dialog.find('#whatsapp-conversation').length > 0) {
        conversationRefreshInterval = setInterval(() => {
            const frm = cur_frm;
            if (frm && frm.doc.mobile_no) {
                load_conversation_in_dialog(frm, { get_value: () => {} });
            }
        }, 30000);
    }
});

$(document).on('hide.bs.modal', function() {
    if (conversationRefreshInterval) {
        clearInterval(conversationRefreshInterval);
        conversationRefreshInterval = null;
    }
});

// Real-time message updates via Socket.IO
if (typeof io !== 'undefined') {
    const socket = io('/whatsapp-messages');
    
    socket.on('new_message', function(data) {
        if (cur_frm && cur_frm.doc.mobile_no === data.phone_number) {
            // Refresh conversation if dialog is open
            if ($('#whatsapp-conversation:visible').length > 0) {
                load_conversation_in_dialog(cur_frm, { get_value: () => {} });
            }
            
            // Add timeline entry
            const direction = data.direction === 'sent' ? 'Outgoing' : 'Incoming';
            const content = `${direction} WhatsApp message: ${data.message_body}`;
            cur_frm.timeline.insert_comment('Communication', content);
            
            // Show notification for incoming messages
            if (data.direction === 'received') {
                frappe.show_alert({
                    message: __('New WhatsApp message from {0}', [data.phone_number]),
                    indicator: 'blue'
                });
            }
        }
    });
    
    socket.on('message_status_update', function(data) {
        if (cur_frm && cur_frm.doc.mobile_no === data.phone_number) {
            // Update message status in conversation if dialog is open
            if ($('#whatsapp-conversation:visible').length > 0) {
                load_conversation_in_dialog(cur_frm, { get_value: () => {} });
            }
        }
    });
}