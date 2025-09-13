/**
 * MediaSoup Signaling Server for Frappe WhatsApp Calling
 * This server bridges the Frappe frontend with MediaSoup WebRTC
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const mediasoup = require('mediasoup');
const axios = require('axios');

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*", // Configure this for your Frappe domain in production
    methods: ["GET", "POST"],
    credentials: true
  }
});

// MediaSoup objects
let worker;
let router;
const transports = new Map();
const producers = new Map();
const consumers = new Map();

// Configuration - should match Frappe MediaSoup settings
const config = {
  mediasoup: {
    worker: {
      logLevel: 'warn',
      rtcMinPort: 10000,
      rtcMaxPort: 10100,
    },
    router: {
      mediaCodecs: [
        {
          kind: 'audio',
          mimeType: 'audio/opus',
          clockRate: 48000,
          channels: 2,
        },
        {
          kind: 'audio',  
          mimeType: 'audio/PCMU',
          clockRate: 8000,
        },
      ],
    },
    webRtcTransport: {
      listenIps: [
        { ip: '0.0.0.0', announcedIp: null }, // Replace with your public IP for production
      ],
      enableUdp: true,
      enableTcp: true,
      preferUdp: true,
    },
  },
  frappe: {
    baseUrl: process.env.FRAPPE_URL || 'http://localhost:8000',
    // Add authentication if needed
  }
};

/**
 * Initialize MediaSoup Worker and Router
 */
async function initializeMediaSoup() {
  try {
    // Create MediaSoup worker
    worker = await mediasoup.createWorker(config.mediasoup.worker);
    console.log('✅ MediaSoup worker created');

    worker.on('died', (error) => {
      console.error('❌ MediaSoup worker died:', error);
      process.exit(1);
    });

    // Create router
    router = await worker.createRouter({
      mediaCodecs: config.mediasoup.router.mediaCodecs,
    });
    console.log('✅ MediaSoup router created');

  } catch (error) {
    console.error('❌ Failed to initialize MediaSoup:', error);
    process.exit(1);
  }
}

/**
 * Validate session with Frappe backend
 */
async function validateFrappeSession(sessionToken, userId) {
  try {
    const response = await axios.post(`${config.frappe.baseUrl}/api/method/whatsapp_calling.calling.webrtc_manager.validate_session`, {
      session_token: sessionToken,
      user_id: userId
    });
    
    return response.data.message.valid;
  } catch (error) {
    console.error('❌ Frappe session validation failed:', error);
    return false;
  }
}

/**
 * Socket.IO connection handling
 */
io.on('connection', (socket) => {
  console.log('🔗 Client connected:', socket.id);

  // Store client session info
  socket.frappeUser = null;
  socket.callSession = null;

  /**
   * Authenticate with Frappe session
   */
  socket.on('authenticate', async (data, callback) => {
    const { sessionToken, userId } = data;
    
    try {
      const isValid = await validateFrappeSession(sessionToken, userId);
      
      if (isValid) {
        socket.frappeUser = userId;
        socket.join(`user:${userId}`); // Join user-specific room
        callback({ success: true });
        console.log(`✅ User ${userId} authenticated`);
      } else {
        callback({ success: false, error: 'Invalid session' });
      }
    } catch (error) {
      callback({ success: false, error: error.message });
    }
  });

  /**
   * Get router RTP capabilities
   */
  socket.on('get-rtp-capabilities', (callback) => {
    if (!socket.frappeUser) {
      return callback({ error: 'Not authenticated' });
    }
    
    callback(router.rtpCapabilities);
  });

  /**
   * Create WebRTC transport
   */
  socket.on('create-transport', async (data, callback) => {
    if (!socket.frappeUser) {
      return callback({ error: 'Not authenticated' });
    }

    try {
      const { producing, consuming } = data;

      const transport = await router.createWebRtcTransport({
        ...config.mediasoup.webRtcTransport,
        appData: { 
          producing, 
          consuming, 
          userId: socket.frappeUser 
        },
      });

      transports.set(transport.id, transport);

      // Handle transport events
      transport.on('dtlsstatechange', (dtlsState) => {
        if (dtlsState === 'closed') {
          transport.close();
          transports.delete(transport.id);
        }
      });

      transport.on('@close', () => {
        transports.delete(transport.id);
      });

      callback({
        id: transport.id,
        iceParameters: transport.iceParameters,
        iceCandidates: transport.iceCandidates,
        dtlsParameters: transport.dtlsParameters,
      });

      console.log(`✅ Transport created: ${transport.id} for user ${socket.frappeUser}`);

    } catch (error) {
      console.error('❌ Error creating transport:', error);
      callback({ error: error.message });
    }
  });

  /**
   * Connect transport
   */
  socket.on('transport-connect', async (data) => {
    const { transportId, dtlsParameters } = data;
    const transport = transports.get(transportId);

    if (!transport) {
      console.error('❌ Transport not found:', transportId);
      return;
    }

    try {
      await transport.connect({ dtlsParameters });
      console.log(`✅ Transport connected: ${transportId}`);
    } catch (error) {
      console.error('❌ Error connecting transport:', error);
    }
  });

  /**
   * Create producer (send audio)
   */
  socket.on('transport-produce', async (data, callback) => {
    const { transportId, kind, rtpParameters, appData } = data;
    const transport = transports.get(transportId);

    if (!transport) {
      return callback({ error: 'Transport not found' });
    }

    try {
      const producer = await transport.produce({
        kind,
        rtpParameters,
        appData: { 
          ...appData, 
          userId: socket.frappeUser 
        },
      });

      producers.set(producer.id, producer);

      // Handle producer events
      producer.on('transportclose', () => {
        producer.close();
        producers.delete(producer.id);
      });

      callback({ id: producer.id });
      console.log(`✅ Producer created: ${producer.id} for user ${socket.frappeUser}`);

      // Notify other clients in the call about new producer
      socket.to(`call:${socket.callSession}`).emit('new-producer', {
        producerId: producer.id,
        userId: socket.frappeUser,
        kind: kind
      });

    } catch (error) {
      console.error('❌ Error creating producer:', error);
      callback({ error: error.message });
    }
  });

  /**
   * Join call session
   */
  socket.on('join-call', (data) => {
    const { callSessionId } = data;
    socket.callSession = callSessionId;
    socket.join(`call:${callSessionId}`);
    
    console.log(`✅ User ${socket.frappeUser} joined call: ${callSessionId}`);
    
    // Notify Frappe backend about call participation
    notifyFrappeCallEvent('call_joined', {
      userId: socket.frappeUser,
      callSessionId: callSessionId
    });
  });

  /**
   * Leave call session
   */
  socket.on('leave-call', () => {
    if (socket.callSession) {
      socket.leave(`call:${socket.callSession}`);
      
      // Notify Frappe backend
      notifyFrappeCallEvent('call_left', {
        userId: socket.frappeUser,
        callSessionId: socket.callSession
      });
      
      socket.callSession = null;
    }
  });

  /**
   * Handle client disconnect
   */
  socket.on('disconnect', () => {
    console.log('🔌 Client disconnected:', socket.id);
    
    // Clean up resources
    if (socket.callSession) {
      socket.leave(`call:${socket.callSession}`);
    }
    
    // Clean up producers for this user
    producers.forEach((producer, producerId) => {
      if (producer.appData.userId === socket.frappeUser) {
        producer.close();
        producers.delete(producerId);
      }
    });
    
    // Clean up transports for this user
    transports.forEach((transport, transportId) => {
      if (transport.appData.userId === socket.frappeUser) {
        transport.close();
        transports.delete(transportId);
      }
    });
  });
});

/**
 * Notify Frappe backend about call events
 */
async function notifyFrappeCallEvent(eventType, data) {
  try {
    await axios.post(`${config.frappe.baseUrl}/api/method/whatsapp_calling.calling.webrtc_manager.handle_call_event`, {
      event_type: eventType,
      ...data
    });
  } catch (error) {
    console.error('❌ Failed to notify Frappe:', error);
  }
}

/**
 * Health check endpoint
 */
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    mediasoup: {
      worker: worker ? 'connected' : 'disconnected',
      router: router ? 'connected' : 'disconnected',
      transports: transports.size,
      producers: producers.size
    },
    frappe: {
      baseUrl: config.frappe.baseUrl
    }
  });
});

/**
 * Start server
 */
async function startServer() {
  await initializeMediaSoup();
  
  const PORT = process.env.PORT || 3000;
  server.listen(PORT, () => {
    console.log(`🚀 MediaSoup Signaling Server running on port ${PORT}`);
    console.log(`🔗 Frappe integration: ${config.frappe.baseUrl}`);
    console.log(`📊 Health check: http://localhost:${PORT}/health`);
  });
}

// Handle graceful shutdown
process.on('SIGINT', () => {
  console.log('🛑 Shutting down MediaSoup server...');
  if (worker) {
    worker.close();
  }
  process.exit(0);
});

// Start the server
startServer().catch(console.error);