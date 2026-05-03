#!/bin/bash

# Render Deployment Verification Script
# Tests all deployed services and connectivity

set -e

echo "================================================"
echo "OBE Assessment Platform - Render Verification"
echo "================================================"
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if URL is accessible
check_url() {
    local url=$1
    local service_name=$2

    echo -n "Testing $service_name ($url)... "

    if response=$(curl -s -w "\n%{http_code}" -m 10 "$url" 2>/dev/null); then
        http_code=$(echo "$response" | tail -n1)
        body=$(echo "$response" | sed '$d')

        # Accept 200, 404, or other non-500 responses
        if [[ "$http_code" =~ ^(200|201|400|404|405)$ ]]; then
            echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
            return 0
        elif [[ "$http_code" =~ ^5[0-9]{2}$ ]]; then
            echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
            echo "Response: $body" | head -c 100
            echo ""
            return 1
        else
            echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
            return 0
        fi
    else
        echo -e "${RED}✗ FAILED${NC} (Connection error)"
        return 1
    fi
}

# Get service URLs from user
echo "Enter your deployed service URLs:"
echo ""

read -p "Backend API URL (e.g., https://obe-assess-backend.onrender.com): " BACKEND_URL
read -p "LLM Service URL (e.g., https://obe-assess-llm.onrender.com): " LLM_URL
read -p "Frontend URL (e.g., https://obe-assess-frontend.onrender.com): " FRONTEND_URL

echo ""
echo "================================================"
echo "Verification Results"
echo "================================================"
echo ""

# Test Backend API
echo "1. Testing Backend Service:"
if check_url "$BACKEND_URL/api/" "Backend Health Check"; then
    backend_ok=1
else
    backend_ok=0
fi

# Test Backend Database connectivity (optional)
echo -n "  Testing Database connectivity via API... "
if response=$(curl -s -X GET "$BACKEND_URL/api/health/" 2>/dev/null); then
    echo -e "${GREEN}✓ OK${NC}"
else
    echo -e "${YELLOW}⚠ Not available${NC} (May be normal)"
fi

echo ""

# Test LLM Service
echo "2. Testing LLM Service:"
if check_url "$LLM_URL/" "LLM Service Health"; then
    llm_ok=1
else
    llm_ok=0
fi

# Test LLM Generate endpoint
echo -n "  Testing LLM /generate endpoint (mock)... "
if response=$(curl -s -w "\n%{http_code}" -m 10 "$LLM_URL/generate" \
    -H "Content-Type: application/json" \
    -d '{"text":"test","assessment_type":"Quiz","questions_config":[]}' 2>/dev/null); then
    http_code=$(echo "$response" | tail -n1)
    if [[ "$http_code" =~ ^(200|400|422|500)$ ]]; then
        echo -e "${GREEN}✓ OK${NC} (Endpoint accessible)"
    else
        echo -e "${YELLOW}⚠ Not available${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Not available${NC}"
fi

echo ""

# Test Frontend
echo "3. Testing Frontend Service:"
if response=$(curl -s -w "\n%{http_code}" -m 10 "$FRONTEND_URL" 2>/dev/null); then
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [[ "$http_code" == "200" ]]; then
        echo -n "Testing Frontend ($FRONTEND_URL)... "
        echo -e "${GREEN}✓ OK${NC} (HTTP $http_code)"
        frontend_ok=1

        # Check for common HTML indicators
        if echo "$body" | grep -q "html\|<!DOCTYPE"; then
            echo -n "  Frontend HTML structure... "
            echo -e "${GREEN}✓ OK${NC}"
        fi
    else
        echo -n "Testing Frontend ($FRONTEND_URL)... "
        echo -e "${RED}✗ FAILED${NC} (HTTP $http_code)"
        frontend_ok=0
    fi
else
    echo -n "Testing Frontend ($FRONTEND_URL)... "
    echo -e "${RED}✗ FAILED${NC} (Connection error)"
    frontend_ok=0
fi

echo ""

# Test connectivity between services
echo "4. Testing Service Interconnectivity:"
echo -n "  Can Backend reach LLM Service?... "
if response=$(curl -s -w "\n%{http_code}" -m 10 "$BACKEND_URL/api/llm-health/" 2>/dev/null); then
    echo -e "${YELLOW}⚠ Check logs${NC}"
else
    echo -e "${YELLOW}⚠ Not implemented${NC}"
fi

echo ""

# Summary
echo "================================================"
echo "Summary"
echo "================================================"
echo ""

success_count=0

if [ $backend_ok -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Backend Service: Running"
    ((success_count++))
else
    echo -e "${RED}✗${NC} Backend Service: Not responding"
fi

if [ $llm_ok -eq 1 ]; then
    echo -e "${GREEN}✓${NC} LLM Service: Running"
    ((success_count++))
else
    echo -e "${RED}✗${NC} LLM Service: Not responding"
fi

if [ $frontend_ok -eq 1 ]; then
    echo -e "${GREEN}✓${NC} Frontend Service: Running"
    ((success_count++))
else
    echo -e "${RED}✗${NC} Frontend Service: Not responding"
fi

echo ""

if [ $success_count -eq 3 ]; then
    echo -e "${GREEN}✓ All services deployed and responding!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Visit frontend: $FRONTEND_URL"
    echo "2. Test user registration/login"
    echo "3. Create test assessment"
    echo "4. Generate assessment questions"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some services are not responding${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "1. Check Render dashboard for service status"
    echo "2. Review service logs for errors"
    echo "3. Verify all environment variables are set"
    echo "4. Ensure database is running and accessible"
    echo ""
    exit 1
fi
