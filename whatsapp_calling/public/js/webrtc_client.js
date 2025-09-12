class WhatsAppWebRTCClient {
    constructor() {
        this.pc = null;
        this.localStream = null;
        this.socket = io('/whatsapp-calling');
        this.currentCall = null;
        this.isCallActive = false;
        
        this.bindEvents();
    }
    
    bindEvents() {
        // Socket.IO event listeners
        this.socket.on('call:incoming', (data) => this.handleIncomingCall(data));
        this.socket.on('call:answered', (data) => this.handleCallAnswered(data));
        this.socket.on('call:ended', (data) => this.handleCallEnded(data));
        this.socket.on('call:offer', (data) => this.handleOffer(data));
        this.socket.on('call:answer', (data) => this.handleAnswer(data));
        this.socket.on('call:ice-candidate', (data) => this.handleIceCandidate(data));
        this.socket.on('call:quality-update', (data) => this.handleQualityUpdate(data));
    }
    
    async initiateCall(phoneNumber, leadId = null) {
        try {
            // Show calling UI
            this.showCallingInterface(phoneNumber);
            
            // Request call initiation from server
            const response = await frappe.call({
                method: 'whatsapp_calling.calling.webrtc_manager.initiate_call',
                args: {
                    to_number: phoneNumber,
                    lead_id: leadId
                }
            });
            
            if (response.message.success) {
                this.currentCall = response.message;
                await this.setupWebRTCConnection();
                return true;
            } else {
                this.showError('Failed to initiate call');
                return false;
            }
            
        } catch (error) {
            console.error('Error initiating call:', error);
            this.showError('Failed to initiate call: ' + error.message);
            return false;
        }
    }
    
    async setupWebRTCConnection() {
        try {
            // Get user media (audio only for WhatsApp calling)
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                },
                video: false
            });
            
            // Create peer connection
            const config = await this.getICEConfiguration();
            this.pc = new RTCPeerConnection(config);
            
            // Add local stream tracks
            this.localStream.getTracks().forEach(track => {
                this.pc.addTrack(track, this.localStream);
            });
            
            // Handle remote stream
            this.pc.ontrack = (event) => {
                const remoteAudio = document.getElementById('remoteAudio');
                if (remoteAudio) {
                    remoteAudio.srcObject = event.streams[0];
                }
            };
            
            // Handle ICE candidates
            this.pc.onicecandidate = (event) => {
                if (event.candidate) {
                    this.socket.emit('call:ice-candidate', {
                        sessionId: this.currentCall.session_id,
                        candidate: event.candidate
                    });
                }
            };
            
            // Handle connection state changes
            this.pc.onconnectionstatechange = () => {
                this.updateCallStatus(this.pc.connectionState);
            };
            
            // Create and send offer
            const offer = await this.pc.createOffer();
            await this.pc.setLocalDescription(offer);
            
            this.socket.emit('call:initiate', {
                phoneNumber: this.currentCall.to_number,
                sessionId: this.currentCall.session_id,
                offer: offer
            });
            
        } catch (error) {
            console.error('Error setting up WebRTC:', error);
            this.showError('Failed to setup call connection');
        }
    }
    
    async getICEConfiguration() {
        try {
            const response = await frappe.call({
                method: 'whatsapp_calling.calling.webrtc_manager.get_ice_servers'
            });
            
            return {
                iceServers: response.message || [
                    { urls: 'stun:stun.l.google.com:19302' }
                ]
            };
        } catch (error) {
            console.error('Error getting ICE config:', error);
            return {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' }
                ]
            };
        }
    }
    
    async handleOffer(data) {
        try {
            if (!this.pc) {
                await this.setupWebRTCConnection();
            }
            
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.offer));
            
            const answer = await this.pc.createAnswer();
            await this.pc.setLocalDescription(answer);
            
            this.socket.emit('call:answer', {
                sessionId: data.sessionId,
                answer: answer
            });
            
        } catch (error) {
            console.error('Error handling offer:', error);
        }
    }
    
    async handleAnswer(data) {
        try {
            await this.pc.setRemoteDescription(new RTCSessionDescription(data.answer));
        } catch (error) {
            console.error('Error handling answer:', error);
        }
    }
    
    async handleIceCandidate(data) {
        try {
            if (this.pc && this.pc.remoteDescription) {
                await this.pc.addIceCandidate(new RTCIceCandidate(data.candidate));
            }
        } catch (error) {
            console.error('Error handling ICE candidate:', error);
        }
    }
    
    async endCall(endReason = 'user_hangup') {
        try {
            if (this.currentCall) {
                await frappe.call({
                    method: 'whatsapp_calling.calling.webrtc_manager.end_call',
                    args: {
                        session_id: this.currentCall.session_id,
                        end_reason: endReason
                    }
                });
            }
            
            this.cleanup();
            this.hideCallingInterface();
            
        } catch (error) {
            console.error('Error ending call:', error);
            this.cleanup();
        }
    }
    
    cleanup() {
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        
        if (this.pc) {
            this.pc.close();
            this.pc = null;
        }
        
        this.currentCall = null;
        this.isCallActive = false;
    }
    
    showCallingInterface(phoneNumber) {
        // Create calling modal
        const modal = $(`
            <div class="modal fade" id="whatsapp-calling-modal" tabindex="-1" role="dialog">
                <div class="modal-dialog modal-sm" role="document">
                    <div class="modal-content">
                        <div class="modal-body text-center">
                            <div class="calling-animation">
                                <div class="pulse-ring"></div>
                                <div class="pulse-ring"></div>
                                <div class="pulse-ring"></div>
                            </div>
                            <h4 class="calling-number">${phoneNumber}</h4>
                            <p class="call-status">Connecting...</p>
                            <div class="call-controls mt-3">
                                <button class="btn btn-danger btn-sm" id="end-call-btn">
                                    <i class="fa fa-phone"></i> End Call
                                </button>
                                <button class="btn btn-secondary btn-sm ml-2" id="mute-call-btn">
                                    <i class="fa fa-microphone"></i> Mute
                                </button>
                            </div>
                            <div class="call-quality mt-2">
                                <small class="text-muted">Quality: <span id="call-quality">Good</span></small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <audio id="remoteAudio" autoplay></audio>
        `);
        
        $('body').append(modal);
        $('#whatsapp-calling-modal').modal('show');
        
        // Bind control events
        $('#end-call-btn').click(() => this.endCall());
        $('#mute-call-btn').click(() => this.toggleMute());
        
        // Prevent modal from being closed
        $('#whatsapp-calling-modal').on('hide.bs.modal', (e) => {
            if (this.isCallActive) {
                e.preventDefault();
            }
        });
        
        this.isCallActive = true;
    }
    
    hideCallingInterface() {
        $('#whatsapp-calling-modal').modal('hide');
        setTimeout(() => {
            $('#whatsapp-calling-modal').remove();
        }, 500);
    }
    
    updateCallStatus(status) {
        const statusElement = $('.call-status');
        const qualityElement = $('#call-quality');
        
        switch (status) {
            case 'connecting':
                statusElement.text('Connecting...');
                break;
            case 'connected':
                statusElement.text('Connected');
                this.startCallTimer();
                break;
            case 'disconnected':
                statusElement.text('Call Ended');
                break;
            case 'failed':
                statusElement.text('Call Failed');
                this.showError('Call connection failed');
                break;
        }
    }
    
    startCallTimer() {
        const startTime = Date.now();
        const timer = setInterval(() => {
            if (!this.isCallActive) {
                clearInterval(timer);
                return;
            }
            
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            $('.call-status').text(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        }, 1000);
    }
    
    toggleMute() {
        if (this.localStream) {
            const audioTrack = this.localStream.getAudioTracks()[0];
            if (audioTrack) {
                audioTrack.enabled = !audioTrack.enabled;
                const btn = $('#mute-call-btn');
                const icon = btn.find('i');
                
                if (audioTrack.enabled) {
                    icon.removeClass('fa-microphone-slash').addClass('fa-microphone');
                    btn.removeClass('btn-warning').addClass('btn-secondary');
                } else {
                    icon.removeClass('fa-microphone').addClass('fa-microphone-slash');
                    btn.removeClass('btn-secondary').addClass('btn-warning');
                }
            }
        }
    }
    
    handleQualityUpdate(data) {
        const qualityScore = data.quality_score || 'Unknown';
        $('#call-quality').text(qualityScore);
        
        // Update quality indicator color
        const qualityElement = $('#call-quality');
        qualityElement.removeClass('text-success text-warning text-danger');
        
        if (data.quality_score >= 80) {
            qualityElement.addClass('text-success');
        } else if (data.quality_score >= 60) {
            qualityElement.addClass('text-warning');
        } else {
            qualityElement.addClass('text-danger');
        }
    }
    
    handleIncomingCall(data) {
        // Handle incoming call (for future enhancement)
        console.log('Incoming call:', data);
    }
    
    handleCallAnswered(data) {
        this.updateCallStatus('connected');
    }
    
    handleCallEnded(data) {
        this.updateCallStatus('disconnected');
        setTimeout(() => {
            this.endCall();
        }, 2000);
    }
    
    showError(message) {
        frappe.show_alert({
            message: message,
            indicator: 'red'
        });
    }
}

// Global instance
window.whatsappWebRTC = new WhatsAppWebRTCClient();

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WhatsAppWebRTCClient;
}