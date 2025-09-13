# MediaSoup Signaling Server

This is a separate Node.js server that bridges the Frappe WhatsApp Calling app with MediaSoup WebRTC.

## Requirements

- Node.js >= 20.0.0
- MediaSoup dependencies

## Installation

```bash
cd mediasoup-server
npm install
```

## Configuration

Set environment variables:

```bash
export FRAPPE_URL="https://your-frappe-site.com"
export PORT=3000
```

## Running

```bash
# Development
npm run dev

# Production
npm start
```

## Health Check

```bash
curl http://localhost:3000/health
```

## Deployment

This server should be deployed separately from your Frappe application, ideally on a server with good network connectivity and the required Node.js version.

### Docker Deployment

```dockerfile
FROM node:20-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

### PM2 Deployment

```bash
npm install -g pm2
pm2 start server.js --name "mediasoup-signaling"
pm2 save
pm2 startup
```