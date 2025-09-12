class WhatsAppWebRTCClient {
    constructor() {
        this.device = null;
        this.socket = io('/whatsapp-calling');
        this.currentCall = null;
        this.isCallActive = false;
        this.localStream = null;
        this.sendTransport = null;
        this.recvTransport = null;
        this.producer = null;
        this.consumer = null;
        this.mediasoupConfig = null;
        
        this.bindEvents();
        this.initMediaSoup();
    }
    
    bindEvents() {
        // Socket.IO event listeners for signaling
        this.socket.on('call:incoming', (data) => this.handleIncomingCall(data));
        this.socket.on('call:answered', (data) => this.handleCallAnswered(data));
        this.socket.on('call:ended', (data) => this.handleCallEnded(data));
        this.socket.on('transport-connect', (data) => this.handleTransportConnect(data));
        this.socket.on('transport-produce', (data) => this.handleTransportProduce(data));
        this.socket.on('new-consumer', (data) => this.handleNewConsumer(data));
        this.socket.on('call:quality-update', (data) => this.handleQualityUpdate(data));
    }
    
    async initMediaSoup() {
        if (typeof mediasoupClient === 'undefined') {
            console.error('MediaSoup client library not loaded');
            return;
        }
        
        try {
            // Create MediaSoup device
            this.device = new mediasoupClient.Device();
            console.log('MediaSoup device created successfully');
        } catch (error) {
            console.error('Error creating MediaSoup device:', error);
        }
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
                this.mediasoupConfig = response.message.mediasoup_config;
                
                await this.setupMediaSoupConnection();
                await this.startCall(phoneNumber);
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
    
    async setupMediaSoupConnection() {
        try {
            // Get MediaSoup configuration from server
            const response = await frappe.call({
                method: 'whatsapp_calling.whatsapp_calling.doctype.mediasoup_webrtc_settings.api.get_mediasoup_config'
            });
            
            this.mediasoupConfig = response.message;
            
            // Get router RTP capabilities from server
            const rtpCapabilities = await this.getRtpCapabilities();
            
            // Load the device with RTP capabilities
            if (!this.device.loaded) {
                await this.device.load({ routerRtpCapabilities: rtpCapabilities });
                console.log('MediaSoup device loaded with RTP capabilities');
            }
            
        } catch (error) {
            console.error('Error setting up MediaSoup:', error);
            this.showError('Failed to setup call connection');
        }
    }
    
    async getRtpCapabilities() {
        // In a real implementation, this would come from the MediaSoup server
        // For now, return default audio capabilities
        return {
            codecs: [
                {
                    kind: 'audio',
                    mimeType: 'audio/opus',
                    clockRate: 48000,
                    channels: 2,
                    parameters: {
                        'useinbandfec': 1,
                        'usedtx': 1
                    }
                }
            ],
            headerExtensions: [
                {
                    kind: 'audio',
                    uri: 'urn:ietf:params:rtp-hdrext:ssrc-audio-level',
                    preferredId: 1
                }
            ]
        };
    }
    
    async startCall(phoneNumber) {
        try {
            // Get user media (audio only)
            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                },
                video: false
            });
            
            // Create send transport
            await this.createSendTransport();
            
            // Create receive transport
            await this.createRecvTransport();
            
            // Produce audio
            await this.produce();
            
            // Update UI
            this.updateCallStatus('connecting');
            
        } catch (error) {
            console.error('Error starting call:', error);
            this.showError('Failed to start call');
        }
    }
    
    async createSendTransport() {
        // Get transport options from server (in real implementation)
        const transportOptions = {
            id: frappe.utils.get_random(10),
            iceParameters: {
                usernameFragment: frappe.utils.get_random(4),
                password: frappe.utils.get_random(24),
                iceLite: true
            },
            iceCandidates: [],
            dtlsParameters: {
                role: 'auto',
                fingerprints: [
                    {
                        algorithm: 'sha-256',
                        value: '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00'
                    }
                ]
            }
        };
        
        this.sendTransport = this.device.createSendTransport(transportOptions);
        
        this.sendTransport.on('connect', async ({ dtlsParameters }, callback, errback) => {
            try {
                // Signal transport connect to server
                this.socket.emit('transport-connect', {
                    transportId: this.sendTransport.id,
                    dtlsParameters: dtlsParameters
                });
                callback();
            } catch (error) {
                errback(error);
            }
        });
        
        this.sendTransport.on('produce', async ({ kind, rtpParameters, appData }, callback, errback) => {
            try {
                // Signal produce to server
                this.socket.emit('transport-produce', {
                    transportId: this.sendTransport.id,
                    kind: kind,
                    rtpParameters: rtpParameters,
                    appData: appData
                });
                
                // Server would respond with producer ID
                const producerId = frappe.utils.get_random(10);
                callback({ id: producerId });
            } catch (error) {
                errback(error);
            }
        });
    }
    
    async createRecvTransport() {
        // Similar to send transport but for receiving
        const transportOptions = {
            id: frappe.utils.get_random(10),
            iceParameters: {
                usernameFragment: frappe.utils.get_random(4),
                password: frappe.utils.get_random(24),
                iceLite: true
            },
            iceCandidates: [],
            dtlsParameters: {
                role: 'auto',
                fingerprints: [
                    {
                        algorithm: 'sha-256',
                        value: '00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00'
                    }
                ]
            }
        };
        
        this.recvTransport = this.device.createRecvTransport(transportOptions);
        
        this.recvTransport.on('connect', async ({ dtlsParameters }, callback, errback) => {
            try {
                // Signal transport connect to server
                this.socket.emit('transport-connect', {
                    transportId: this.recvTransport.id,
                    dtlsParameters: dtlsParameters
                });
                callback();
            } catch (error) {
                errback(error);
            }
        });
    }
    
    async produce() {
        if (!this.localStream) return;
        
        const audioTrack = this.localStream.getAudioTracks()[0];
        if (audioTrack) {
            this.producer = await this.sendTransport.produce({
                track: audioTrack,
                codecOptions: {
                    opusStereo: 1,
                    opusFec: 1,
                    opusDtx: 1,
                    opusMaxPlaybackRate: 48000
                }
            });
            
            console.log('Audio producer created:', this.producer.id);
        }
    }
    
    async consume(consumerInfo) {
        const { producerId, id, kind, rtpParameters } = consumerInfo;
        
        this.consumer = await this.recvTransport.consume({
            id: id,
            producerId: producerId,
            kind: kind,
            rtpParameters: rtpParameters
        });
        
        // Attach remote audio
        const remoteAudio = document.getElementById('remoteAudio');
        if (remoteAudio && this.consumer.track) {
            const remoteStream = new MediaStream([this.consumer.track]);
            remoteAudio.srcObject = remoteStream;
            this.updateCallStatus('connected');
        }
        
        console.log('Audio consumer created:', this.consumer.id);
    }
    
    async handleTransportConnect(data) {
        // Handle transport connection from server
        console.log('Transport connected:', data);
    }
    
    async handleTransportProduce(data) {
        // Handle produce response from server
        console.log('Producer created:', data);
    }
    
    async handleNewConsumer(data) {
        // Handle new consumer from server
        await this.consume(data);
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
        // Close producer
        if (this.producer) {
            this.producer.close();
            this.producer = null;
        }
        
        // Close consumer
        if (this.consumer) {
            this.consumer.close();
            this.consumer = null;
        }
        
        // Close transports
        if (this.sendTransport) {
            this.sendTransport.close();
            this.sendTransport = null;
        }
        
        if (this.recvTransport) {
            this.recvTransport.close();
            this.recvTransport = null;
        }
        
        // Stop local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
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
        if (this.producer && this.producer.track) {
            this.producer.track.enabled = !this.producer.track.enabled;
            const btn = $('#mute-call-btn');
            const icon = btn.find('i');
            
            if (this.producer.track.enabled) {
                icon.removeClass('fa-microphone-slash').addClass('fa-microphone');
                btn.removeClass('btn-warning').addClass('btn-secondary');
            } else {
                icon.removeClass('fa-microphone').addClass('fa-microphone-slash');
                btn.removeClass('btn-secondary').addClass('btn-warning');
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