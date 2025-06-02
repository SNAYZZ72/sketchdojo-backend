#!/bin/bash

echo "🔍 Checking Grafana Datasource Configuration"
echo "============================================"

# Check if Grafana is running
echo "1. Checking if Grafana is accessible..."
curl -f -s http://localhost:3000/api/health > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Grafana is running"
else
    echo "❌ Grafana is not accessible"
    exit 1
fi

# Check current datasources
echo -e "\n2. Checking current datasources..."
curl -s -u admin:sketchdojo http://localhost:3000/api/datasources | python3 -m json.tool

# Check if Prometheus service is reachable from Grafana container
echo -e "\n3. Testing Prometheus connectivity from Grafana container..."
docker-compose -f docker/docker-compose.yml exec -T grafana curl -s -f http://prometheus:9090/api/v1/targets
if [ $? -eq 0 ]; then
    echo "✅ Grafana can reach Prometheus"
else
    echo "❌ Grafana cannot reach Prometheus"
fi

# Check if Prometheus is accessible from host
echo -e "\n4. Testing Prometheus from host..."
curl -f -s http://localhost:9090/api/v1/targets > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Prometheus is accessible from host"
else
    echo "❌ Prometheus is not accessible from host"
fi
