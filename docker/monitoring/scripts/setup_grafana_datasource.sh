#!/bin/bash

# Function to extract JSON field using Python
json_field() {
    python3 -c "import sys, json; print($1)" 2>/dev/null
}

echo "🔧 Adding Prometheus Datasource to Grafana"
echo "=========================================="

# Wait for Grafana to be ready
echo "1. Waiting for Grafana to be ready..."
until curl -f -s http://localhost:3000/api/health > /dev/null; do
    echo "Waiting for Grafana..."
    sleep 5
done
echo "✅ Grafana is ready"

# Delete existing Prometheus datasource if it exists
echo -e "\n2. Removing any existing Prometheus datasources..."
# Get all datasources and extract Prometheus datasource IDs
DATASOURCES_JSON=$(curl -s -u admin:sketchdojo http://localhost:3000/api/datasources)
EXISTING_DS=$(echo "$DATASOURCES_JSON" | python3 -c "
import sys, json
try:
    datasources = json.load(sys.stdin)
    for ds in datasources:
        if ds.get('type') == 'prometheus':
            print(ds['id'])
except:
    pass
" 2>/dev/null)
if [ ! -z "$EXISTING_DS" ]; then
    for id in $EXISTING_DS; do
        echo "Deleting datasource ID: $id"
        curl -s -u admin:sketchdojo -X DELETE http://localhost:3000/api/datasources/$id
    done
fi

# Add Prometheus datasource
echo -e "\n3. Adding Prometheus datasource..."
cat << 'EOF' > /tmp/prometheus_datasource.json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "access": "proxy",
  "isDefault": true,
  "jsonData": {
    "httpMethod": "GET",
    "manageAlerts": true,
    "prometheusType": "Prometheus",
    "prometheusVersion": "2.40.0"
  },
  "secureJsonData": {}
}
EOF

RESPONSE=$(curl -s -u admin:sketchdojo \
  -X POST \
  -H "Content-Type: application/json" \
  -d @/tmp/prometheus_datasource.json \
  http://localhost:3000/api/datasources)

echo "Response: $RESPONSE"

# Test the datasource
echo -e "\n4. Testing the datasource..."
# Extract datasource ID from response
DS_ID=$(echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('datasource', {}).get('id') or data.get('id') or '')
except:
    print('')
" 2>/dev/null)
if [ "$DS_ID" != "null" ] && [ ! -z "$DS_ID" ]; then
    TEST_RESPONSE=$(curl -s -u admin:sketchdojo \
      -X GET \
      http://localhost:3000/api/datasources/$DS_ID)
    echo "✅ Datasource created successfully with ID: $DS_ID"

    # Test connectivity
    curl -s -u admin:sketchdojo \
      -X POST \
      -H "Content-Type: application/json" \
      http://localhost:3000/api/datasources/proxy/$DS_ID/api/v1/query?query=up

    echo -e "\n✅ Datasource should now be working!"
else
    echo "❌ Failed to create datasource"
    echo "Response: $RESPONSE"
fi

# Clean up
rm -f /tmp/prometheus_datasource.json
