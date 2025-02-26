#!/bin/bash

# Phase 1: Core Infrastructure Preparation
# AI-Generated Modular Infrastructure Setup

set -e

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="/root/mcp-kong-gateway/outputs/phase1"
DOCKER_DIR="/root/mcp-kong-gateway/docker"
mkdir -p "${OUTPUT_DIR}" "${DOCKER_DIR}"

# Logging Function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*"
}

# 1. Docker Containerization
prepare_kong_container() {
    log "Preparing Kong Gateway Docker Container"
    
    cat > "${DOCKER_DIR}/kong-gateway-dockerfile" << EOL
FROM kong/kong-gateway:3.4.1

# MCP Custom Configuration
LABEL mcp.version="1.0"
LABEL mcp.component="api-gateway"

# Custom Kong Configuration
COPY kong.yml /etc/kong/kong.yml
ENV KONG_DATABASE=off
ENV KONG_DECLARATIVE_CONFIG=/etc/kong/kong.yml

# Health Check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/status || exit 1

# Expose Ports
EXPOSE 8000 8443 8001 8444
EOL

    cat > "${DOCKER_DIR}/docker-compose.yml" << EOL
version: '3.8'
services:
  kong-gateway:
    build: 
      context: .
      dockerfile: kong-gateway-dockerfile
    container_name: mcp-kong-gateway
    restart: always
    ports:
      - "8000:8000"
      - "8443:8443"
    volumes:
      - ./kong.yml:/etc/kong/kong.yml
    networks:
      - mcp_network

networks:
  mcp_network:
    driver: bridge
EOL

    echo "Docker container configuration complete" > "${OUTPUT_DIR}/container_setup_${TIMESTAMP}.log"
}

# 2. Service Discovery & Registration
create_service_discovery() {
    log "Implementing Service Discovery Protocol"
    
    cat > "${DOCKER_DIR}/service_discovery.py" << EOL
import json
import os
import requests
from typing import Dict, List

class MCPServiceDiscovery:
    def __init__(self, kong_admin_url='http://localhost:8001'):
        self.kong_admin_url = kong_admin_url
        self.services = {}
    
    def register_service(self, name: str, url: str, routes: List[Dict]):
        service_payload = {
            'name': name,
            'url': url
        }
        
        # Register service
        response = requests.post(f'{self.kong_admin_url}/services', json=service_payload)
        
        # Register routes
        for route in routes:
            route_payload = {
                'service': {'name': name},
                **route
            }
            requests.post(f'{self.kong_admin_url}/routes', json=route_payload)
        
        return response.json()

    def list_services(self):
        response = requests.get(f'{self.kong_admin_url}/services')
        return response.json()

# Example Usage
if __name__ == '__main__':
    discovery = MCPServiceDiscovery()
    services = [
        {
            'name': 'memory-mcp',
            'url': 'http://memory-service:8080',
            'routes': [{'paths': ['/memory']}]
        }
    ]
EOL

    echo "Service discovery protocol generated" > "${OUTPUT_DIR}/service_discovery_${TIMESTAMP}.log"
}

# 3. Authentication Layer
create_auth_middleware() {
    log "Developing Authentication Middleware"
    
    cat > "${DOCKER_DIR}/auth_middleware.py" << EOL
import jwt
import datetime
from functools import wraps
from flask import request, jsonify

class MCPAuthMiddleware:
    def __init__(self, secret_key):
        self.secret_key = secret_key
    
    def generate_token(self, user_id, expiration=30):
        payload = {
            'user_id': user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=expiration)
        }
        return jwt.encode(payload, self.secret_key, algorithm='HS256')
    
    def validate_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def token_required(self, f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'No authentication token'}), 401
            
            payload = self.validate_token(token)
            if not payload:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            return f(*args, **kwargs)
        return decorated
EOL

    echo "Authentication middleware created" > "${OUTPUT_DIR}/auth_middleware_${TIMESTAMP}.log"
}

# Main Execution
main() {
    prepare_kong_container
    create_service_discovery
    create_auth_middleware
    
    log "Phase 1: Infrastructure Preparation Complete"
}

main
exit 0
