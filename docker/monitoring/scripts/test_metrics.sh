#!/bin/bash

echo "🔍 Testing SketchDojo Application Metrics"
echo "========================================"

# First, let's generate some traffic to create metrics
echo "1. Generating test traffic..."
for i in {1..20}; do
    echo "Request $i/20"
    curl -s http://localhost:8000/health > /dev/null
    curl -s http://localhost:8000/api/v1/webtoons/ > /dev/null
    curl -s http://localhost:8000/docs > /dev/null
    sleep 1
done

echo -e "\n2. Checking available SketchDojo metrics..."
curl -s "http://localhost:9090/api/v1/label/__name__/values" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for metric in sorted(data.get('data', [])):
    if metric.startswith('sketchdojo'):
        print(metric)
"

echo -e "\n3. Testing specific metrics queries..."

# Test basic request count
echo "Testing sketchdojo_requests_total:"
curl -s "http://localhost:9090/api/v1/query?query=sketchdojo_requests_total" | python3 -m json.tool

echo -e "\nTesting sum of all requests:"
curl -s "http://localhost:9090/api/v1/query?query=sum(sketchdojo_requests_total)" | python3 -m json.tool

echo -e "\nTesting request rate:"
curl -s "http://localhost:9090/api/v1/query?query=rate(sketchdojo_requests_total[5m])" | python3 -m json.tool

echo -e "\nTesting active requests:"
curl -s "http://localhost:9090/api/v1/query?query=sketchdojo_active_requests" | python3 -m json.tool

echo -e "\n4. Checking if request duration metrics exist..."
curl -s "http://localhost:9090/api/v1/query?query=sketchdojo_request_duration_seconds_bucket" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for result in data.get('data', {}).get('result', []):
        print(result.get('metric', {}))
except Exception as e:
    print(f"Error: {e}")
"

echo -e "\n✅ Metrics test completed!"
