#!/bin/bash

# scripts/init.sh - Complete initialization script

set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BOLD}${BLUE}"
echo "================================================================"
echo "  Embedding Service - Complete Initialization"
echo "================================================================"
echo -e "${NC}"

# Step 1: Pull Ollama model
echo -e "${GREEN}Step 1: Pulling Ollama embedding model...${NC}"
if docker ps | grep -q embedding-ollama; then
    echo "Pulling nomic-embed-text model (this may take a few minutes)..."
    docker exec embedding-ollama ollama pull nomic-embed-text
    echo -e "${GREEN}✓ Model downloaded${NC}"
else
    echo -e "${YELLOW}⚠ Ollama container not running. Start with 'make docker-up' first${NC}"
    exit 1
fi

# Step 2: Verify Ollama
echo -e "\n${GREEN}Step 2: Verifying Ollama...${NC}"
if docker exec embedding-ollama ollama list | grep -q nomic-embed-text; then
    echo -e "${GREEN}✓ Ollama model ready${NC}"
else
    echo -e "${YELLOW}⚠ Model verification failed${NC}"
    exit 1
fi

# Step 3: Test embedding service
echo -e "\n${GREEN}Step 3: Testing embedding service...${NC}"
sleep 2  # Give service time to be ready

API_KEY=$(grep "^API_KEYS=" ../.env | cut -d'=' -f2 | cut -d',' -f1)

RESPONSE=$(curl -s -X POST http://localhost:8000/api/embed \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"test"}')

if echo "$RESPONSE" | grep -q "embedding"; then
    echo -e "${GREEN}✓ Embedding service working${NC}"
else
    echo -e "${YELLOW}⚠ Embedding service test failed${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

# Step 4: Create knowledge folder
echo -e "\n${GREEN}Step 4: Setting up knowledge folder...${NC}"
mkdir -p ../knowledge
echo -e "${GREEN}✓ Created ./knowledge folder${NC}"

# Step 5: Create test file
echo -e "\n${GREEN}Step 5: Creating test knowledge file...${NC}"
cat > ../knowledge/welcome.txt << 'EOF'
# Welcome to Your Knowledge Base

This is your first knowledge file! The file watcher will automatically:

1. Detect this file
2. Read the content
3. Split it into chunks
4. Generate embeddings
5. Store in Qdrant

You can now:
- Drop any .txt or .md files into the ./knowledge folder
- They'll be automatically embedded
- Search them via the /knowledge/search API endpoint

## Example Topics

- Machine Learning: ML is a subset of AI focused on learning from data
- Neural Networks: Computational models inspired by the human brain
- Embeddings: Dense vector representations of text or data

Try searching for "machine learning" using the API!
EOF

echo -e "${GREEN}✓ Created welcome.txt${NC}"

# Step 6: Wait for file watcher to process
echo -e "\n${GREEN}Step 6: Waiting for file watcher to process...${NC}"
echo "This may take 10-20 seconds..."
sleep 15

# Step 7: Test knowledge search
echo -e "\n${GREEN}Step 7: Testing knowledge search...${NC}"

SEARCH_RESPONSE=$(curl -s -X POST http://localhost:8000/knowledge/search \
  -H "X-API-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning","limit":3}')

if echo "$SEARCH_RESPONSE" | grep -q "results"; then
    RESULT_COUNT=$(echo "$SEARCH_RESPONSE" | grep -o '"count":[0-9]*' | cut -d':' -f2)
    echo -e "${GREEN}✓ Knowledge search working (found ${RESULT_COUNT} results)${NC}"
else
    echo -e "${YELLOW}⚠ Knowledge search test inconclusive${NC}"
    echo "This is normal if the file is still being processed"
fi

# Step 8: Show status
echo -e "\n${BOLD}${BLUE}================================================================${NC}"
echo -e "${BOLD}${GREEN}✓ Initialization Complete!${NC}"
echo -e "${BOLD}${BLUE}================================================================${NC}"
echo ""
echo -e "${BOLD}Service Status:${NC}"
echo "  • Embedding API: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Qdrant Dashboard: http://localhost:6333/dashboard"
echo ""
echo -e "${BOLD}Quick Commands:${NC}"
echo "  • View API logs: docker logs -f embedding-service"
echo "  • View file watcher logs: docker logs -f file-watcher"
echo "  • Add knowledge: cp yourfile.txt knowledge/"
echo "  • Search: curl -X POST http://localhost:8000/knowledge/search \\"
echo "             -H 'X-API-Key: ${API_KEY}' \\"
echo "             -d '{\"query\":\"your query\"}'"
echo ""
echo -e "${BOLD}Next Steps:${NC}"
echo "  1. Add your own files to ./knowledge/"
echo "  2. Integrate with your chatbots (see README.md)"
echo "  3. Monitor with: curl http://localhost:8000/metrics"
echo ""
echo -e "${GREEN}Happy embedding! 🚀${NC}"
echo ""