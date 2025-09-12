class WhatsAppWebRTCClient {
    constructor() {
        this.janus = null;
        this.janusSession = null;
        this.videocallHandle = null;
        this.localStream = null;
        this.socket = io('/whatsapp-calling');
        this.currentCall = null;
        this.isCallActive = false;
        this.janusConfig = null;
        
        this.bindEvents();
        this.initJanus();
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
                await this.setupJanusConnection();
                await this.makeCall(phoneNumber);
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
    
    async initJanus() {
        if (typeof Janus === 'undefined') {
            console.error('Janus library not loaded');
            return;
        }
        
        Janus.init({
            debug: "all",
            callback: () => {
                console.log('Janus initialized successfully');
            }
        });
    }
    
    async setupJanusConnection() {
        try {
            // Get Janus configuration
            const response = await frappe.call({
                method: 'whatsapp_calling.whatsapp_calling.doctype.janus_webrtc_settings.api.get_janus_config'
            });
            
            this.janusConfig = response.message;
            
            // Create Janus instance
            this.janus = new Janus({
                server: this.janusConfig.server_url,
                apisecret: this.janusConfig.api_secret,
                iceServers: this.janusConfig.ice_servers,
                success: () => {
                    console.log('Janus connection successful');
                    this.attachVideoCallPlugin();
                },
                error: (error) => {
                    console.error('Janus connection error:', error);
                    this.showError('Failed to connect to Janus server');
                },
                destroyed: () => {
                    console.log('Janus connection destroyed');
                }
            });
            
        } catch (error) {
            console.error('Error setting up Janus:', error);
            this.showError('Failed to setup call connection');
        }
    }
    
    async attachVideoCallPlugin() {
        this.janus.attach({
            plugin: "janus.plugin.videocall",
            opaqueId: "videocall-" + Janus.randomString(12),
            success: (pluginHandle) => {
                this.videocallHandle = pluginHandle;
                console.log('VideoCall plugin attached:', pluginHandle.getPlugin());
            },
            error: (error) => {
                console.error('Error attaching VideoCall plugin:', error);
                this.showError('Failed to initialize call plugin');
            },
            onmessage: (msg, jsep) => {
                this.handleJanusMessage(msg, jsep);
            },
            onlocalstream: (stream) => {
                console.log('Local stream received');
                this.localStream = stream;
            },
            onremotestream: (stream) => {
                console.log('Remote stream received');
                const remoteAudio = document.getElementById('remoteAudio');
                if (remoteAudio) {
                    Janus.attachMediaStream(remoteAudio, stream);
                }
                this.updateCallStatus('connected');
            },
            oncleanup: () => {
                console.log('VideoCall plugin cleanup');
                this.cleanup();
            }
        });
    }
    
    async makeCall(username) {
        if (!this.videocallHandle) {
            this.showError('Call plugin not ready');
            return;
        }
        
        // Get user media first
        try {
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                },
                video: false
            });
        } catch (error) {
            console.error('Error getting user media:', error);
            this.showError('Failed to access microphone');
            return;
        }
        
        // Register username and make call
        const register = {
            request: "register",
            username: frappe.session.user
        };
        
        this.videocallHandle.send({
            message: register,
            success: () => {
                console.log('Registered with Janus');
                // Now make the call
                const call = {
                    request: "call",
                    username: username
                };
                
                this.videocallHandle.send({
                    message: call,
                    media: {
                        audioSend: true,
                        audioRecv: true,
                        videoSend: false,
                        videoRecv: false
                    },
                    stream: this.localStream,
                    success: (jsep) => {
                        console.log('Call initiated', jsep);
                    },
                    error: (error) => {
                        console.error('Error making call:', error);
                        this.showError('Failed to make call');
                    }
                });
            },
            error: (error) => {
                console.error('Error registering:', error);
                this.showError('Failed to register for calling');
            }
        });
    }
    
    handleJanusMessage(msg, jsep) {
        console.log('Janus message received:', msg);
        
        const event = msg['videocall'];
        if (event) {
            if (event === 'event') {
                const result = msg['result'];
                if (result && result['event']) {
                    const eventType = result['event'];
                    
                    switch (eventType) {
                        case 'registered':
                            console.log('Successfully registered');
                            break;
                        case 'calling':
                            this.updateCallStatus('connecting');
                            break;
                        case 'accepted':
                            console.log('Call accepted');
                            if (jsep) {
                                this.videocallHandle.handleRemoteJsep({ jsep: jsep });
                            }
                            break;
                        case 'hangup':
                            console.log('Call ended');
                            this.updateCallStatus('disconnected');
                            break;
                    }
                }
            }
        }
        
        if (jsep) {
            console.log('Handling remote JSEP:', jsep);
            this.videocallHandle.handleRemoteJsep({ jsep: jsep });
        }
    }
    
    async endJanusCall() {
        if (this.videocallHandle) {
            const hangup = { request: "hangup" };
            this.videocallHandle.send({ message: hangup });
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
            
            // End Janus call
            await this.endJanusCall();
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
        
        if (this.videocallHandle) {
            this.videocallHandle.detach();
            this.videocallHandle = null;
        }
        
        if (this.janus) {
            this.janus.destroy();
            this.janus = null;
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