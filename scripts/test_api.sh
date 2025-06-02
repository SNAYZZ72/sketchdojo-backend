#!/bin/bash

set -e

echo "🧪 Testing SketchDojo API"

API_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check if API is running
print_info "Checking if API is running..."
if ! curl -s -f "$API_URL/health" > /dev/null; then
    print_error "API is not running at $API_URL"
    echo "Please start the API first with: make dev"
    exit 1
fi

print_success "API is running"

# Test health endpoint
print_info "Testing health endpoint..."
response=$(curl -s "$API_URL/health")
if echo "$response" | grep -q "healthy"; then
    print_success "Health check passed"
else
    print_error "Health check failed"
    echo "Response: $response"
fi

# Test detailed health endpoint
print_info "Testing detailed health endpoint..."
response=$(curl -s "$API_URL/health/detailed")
if echo "$response" | grep -q "status"; then
    print_success "Detailed health check passed"
else
    print_error "Detailed health check failed"
    echo "Response: $response"
fi

# Test API documentation
print_info "Testing API documentation..."
if curl -s -f "$API_URL/docs" > /dev/null; then
    print_success "API documentation accessible"
else
    print_error "API documentation not accessible"
fi

# Test sync generation endpoint (if AI keys are configured)
print_info "Testing sync generation endpoint..."
response=$(curl -s "$API_URL/api/v1/generation/sync-test?prompt=A%20brave%20hero&num_panels=2")
if echo "$response" | grep -q "webtoon_id\|error"; then
    if echo "$response" | grep -q "webtoon_id"; then
        print_success "Sync generation test passed"
    else
        print_info "Sync generation returned error (expected if no API keys configured)"
        echo "Response: $response"
    fi
else
    print_error "Sync generation test failed"
    echo "Response: $response"
fi

# Test WebSocket connection
print_info "Testing WebSocket connection..."
# Note: This is a basic test - a full WebSocket test would require more complex scripting
if command -v wscat > /dev/null; then
    echo '{"type":"ping"}' | timeout 5 wscat -c "ws://localhost:8000/ws" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "WebSocket connection test passed"
    else
        print_error "WebSocket connection test failed"
    fi
else
    print_info "wscat not installed, skipping WebSocket test"
fi

print_success "API testing completed!"
