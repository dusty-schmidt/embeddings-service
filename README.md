# README.md

# Embedding Service with Automatic Knowledge Base

A production-ready, always-running embedding service with automatic file ingestion and vector storage. Drop files in a folder, they get embedded automatically. Call the API from your chatbots. Search your knowledge base semantically.

## 🎯 What This Does

### Core Service (runs 24/7)
- **Generates embeddings** via Ollama (local, free) and HuggingFace (cloud backup)
- **Caches everything** in Redis for 80%+ cost savings
- **Handles API requests** from multiple chatbots/agents simultaneously
- **Rate limiting** and API key authentication built-in
- **Auto-restarts** on system reboot

### File Watcher (runs 24/7)
- **Monitors** `./knowledge/` folder continuously
- **Automatically embeds** new `.txt` and `.md` files within seconds
- **Chunks large files** intelligently at sentence boundaries
- **Stores in Qdrant** vector database for instant search
- **Tracks changes** - only re-embeds modified files

### Knowledge Search
- **Semantic search** across all ingested files
- **Query by similarity** with optional score thresholds
- **Filter by metadata** (source, date, custom tags)
- **Returns relevant context** perfect for RAG systems

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Your Chatbots/Agents               │
│  - Call API for embeddings          │
│  - Search knowledge base            │
└────────────┬────────────────────────┘
             │ HTTP Requests
             ▼
┌─────────────────────────────────────┐
│  Embedding Service API (Port 8000)  │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │
│  POST /api/embed                    │
│  POST /api/embed/batch              │
│  POST /knowledge/search             │
│  GET  /health, /metrics             │
└────────────┬────────────────────────┘
             │
    ┌────────┼────────┬────────┐
    │        │        │        │
    ▼        ▼        ▼        ▼
┌─────┐  ┌──────┐  ┌────────┐  ┌──────────┐
│Redis│  │Ollama│  │Qdrant  │  │HuggingFace│
│Cache│  │Local │  │Vectors │  │Cloud API  │
└─────┘  └──────┘  └────────┘  └──────────┘
                        ▲
                        │ Auto-stores
            ┌───────────┴───────────┐
            │  File Watcher Service │
            │  ━━━━━━━━━━━━━━━━━━━━ │
            │  Monitors ./knowledge/ │
            │  Auto-embeds files     │
            └────────────────────────┘
```

## 🚀 Quick Start (5 Minutes)

### 1. Setup Project Structure

```bash
# Create directory structure
mkdir -p embedding-service && cd embedding-service
# Copy all provided code files into their respective locations
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your settings
nano .env
```

**Required changes:**
```bash
# IMPORTANT: Change these to secure random strings!
API_KEYS=your-secret-key-here,another-key
ADMIN_KEYS=your-admin-secret-key

# Optional: HuggingFace for cloud fallback
HUGGINGFACE_API_KEY=hf_your_key_here
```

### 3. Start Everything

```bash
# Start all services (one command!)
cd docker
docker-compose up -d

# Wait 30 seconds for containers to start

# Initialize Ollama model
docker exec embedding-ollama ollama pull nomic-embed-text

# Verify everything is running
curl http://localhost:8000/health
```

**That's it!** The service is now running 24/7.

## 📁 Using the File Watcher

### Drop Files and Forget

```bash
# Create knowledge folder (if not exists)
mkdir -p knowledge

# Drop in ANY text file
echo "Machine learning is a subset of AI" > knowledge/ml_basics.txt
cp ~/Documents/important_notes.md knowledge/

# Watch it get processed automatically
docker logs -f file-watcher
```

**You'll see:**
```
📄 Processing: /watch/ml_basics.txt
✂️  Split into 1 chunks
🔄 Embedding chunk 1/1...
✓ Stored chunk 1 (ID: a1b2c3d4...)
✅ Completed: /watch/ml_basics.txt
```

### Supported Formats
- `.txt` - Plain text files
- `.md` - Markdown files  
- `.markdown` - Markdown files

### What Happens Automatically
1. File watcher detects new/modified file (within 5 seconds)
2. Reads content and chunks intelligently (~1000 chars per chunk)
3. Calls embedding API for each chunk (uses cache if available)
4. Stores in Qdrant with metadata (filename, chunk index, timestamp)
5. **Ready for search instantly!**

## 🔍 Searching Your Knowledge Base

### From Python

```python
import requests

# Search for relevant context
response = requests.post(
    "http://localhost:8000/knowledge/search",
    headers={"X-API-Key": "your-secret-key-here"},
    json={
        "query": "Tell me about machine learning",
        "limit": 5,
        "score_threshold": 0.7  # Optional: only results above 70% similarity
    }
)

results = response.json()
for result in results["results"]:
    print(f"Score: {result['score']:.3f}")
    print(f"Text: {result['text']}")
    print(f"Source: {result['metadata']['filename']}")
    print("---")
```

### Using the Python Client

```python
from client.embedding_client import EmbeddingClient

client = EmbeddingClient(
    base_url="http://localhost:8000",
    api_key="your-secret-key-here"
)

# Search knowledge base
results = client.search_knowledge(
    query="What is AI?",
    limit=3
)

# Get embedding
embedding = client.embed("Some text")['embedding']

# Batch embeddings
batch = client.embed_batch(["text1", "text2", "text3"])
```

## 🤖 Integrating with Your Chatbots

### Simple RAG Example

```python
import requests

class MyChatbot:
    def __init__(self, embedding_api_key):
        self.api_base = "http://localhost:8000"
        self.api_key = embedding_api_key
    
    def answer_question(self, user_question):
        # 1. Search knowledge base for context
        search_response = requests.post(
            f"{self.api_base}/knowledge/search",
            headers={"X-API-Key": self.api_key},
            json={"query": user_question, "limit": 3}
        )
        
        context_results = search_response.json()["results"]
        
        # 2. Build context string
        context = "\n\n".join([r["text"] for r in context_results])
        
        # 3. Send to your LLM (OpenAI, Claude, etc.)
        prompt = f"""Context from knowledge base:
{context}

User question: {user_question}

Answer based on the context:"""
        
        # ... call your LLM here ...
        return llm_response

# Use it
bot = MyChatbot(api_key="your-secret-key-here")
answer = bot.answer_question("What is machine learning?")
```

### Real-time Embedding in Conversation

```python
import requests

def embed_conversation_turn(user_message, api_key):
    """Embed each conversation turn for similarity search later"""
    response = requests.post(
        "http://localhost:8000/api/embed",
        headers={"X-API-Key": api_key},
        json={"text": user_message}
    )
    
    return response.json()["embedding"]

# In your chatbot loop
while True:
    user_input = input("You: ")
    
    # Embed for storage/search
    embedding = embed_conversation_turn(user_input, "your-key")
    
    # Store in your database with the embedding
    # ... your logic here ...
```

## 📊 Monitoring & Management

### Health Check
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "embedding-service",
  "version": "1.0.0",
  "cache_available": true,
  "providers": {
    "ollama": true,
    "huggingface": true
  }
}
```

### Metrics
```bash
curl http://localhost:8000/metrics
```

**Response:**
```json
{
  "total_requests": 1543,
  "cache_hits": 1234,
  "cache_misses": 309,
  "cache_hit_rate": 79.97,
  "provider_usage": {
    "ollama": 1500,
    "huggingface": 43
  },
  "uptime_seconds": 86400
}
```

### Knowledge Base Stats
```bash
curl -H "X-API-Key: your-key" \
  http://localhost:8000/knowledge/stats
```

**Response:**
```json
{
  "collection_name": "knowledge_base",
  "total_vectors": 247,
  "total_points": 247,
  "status": "green"
}
```

### View Logs
```bash
# API logs
docker logs -f embedding-service

# File watcher logs (see files being processed)
docker logs -f file-watcher

# Qdrant logs
docker logs -f embedding-qdrant

# All services
docker-compose logs -f
```

## 🛠️ Common Tasks

### Add More Knowledge Files
```bash
# Just drop them in!
cp ~/Documents/*.txt knowledge/
cp ~/Downloads/article.md knowledge/

# They're auto-processed within 5 seconds
# Check progress:
docker logs -f file-watcher
```

### Clear Cache (Admin Only)
```bash
curl -X POST http://localhost:8000/admin/cache/clear \
  -H "X-API-Key: your-admin-key"
```

### Get Detailed Stats (Admin Only)
```bash
curl -H "X-API-Key: your-admin-key" \
  http://localhost:8000/admin/stats
```

### Restart Services
```bash
cd docker
docker-compose restart

# Or restart individual services
docker restart embedding-service
docker restart file-watcher
```

### Stop Everything
```bash
cd docker
docker-compose down

# Stop and remove volumes (deletes data!)
docker-compose down -v
```

### Backup Your Data
```bash
# Backup Qdrant vectors
docker cp embedding-qdrant:/qdrant/storage ./backup-qdrant-$(date +%Y%m%d)

# Backup knowledge files
tar -czf knowledge-backup-$(date +%Y%m%d).tar.gz knowledge/

# Backup Redis (optional, it's just cache)
docker exec embedding-redis redis-cli SAVE
docker cp embedding-redis:/data/dump.rdb ./backup-redis-$(date +%Y%m%d).rdb
```

## 🔑 API Endpoints Reference

### Embedding Endpoints
- `POST /api/embed` - Generate single embedding
  - Body: `{"text": "...", "model": "...", "provider": "..."}`
- `POST /api/embed/batch` - Generate batch embeddings
  - Body: `{"texts": [...], "model": "...", "provider": "..."}`

### Knowledge Base Endpoints
- `POST /knowledge/search` - Semantic search
  - Body: `{"query": "...", "limit": 5, "score_threshold": 0.7}`
- `GET /knowledge/stats` - Collection statistics
- `GET /knowledge/health` - Vector DB health

### System Endpoints
- `GET /health` - Service health check
- `GET /metrics` - Usage metrics
- `GET /providers` - Available providers and models

### Admin Endpoints (require admin key)
- `GET /admin/stats` - Detailed statistics
- `GET /admin/cache/info` - Cache information
- `POST /admin/cache/clear` - Clear all cache

## ⚙️ Configuration Options

### Provider Settings
```bash
# Which provider to use by default
DEFAULT_PROVIDER=ollama  # or huggingface

# Auto-fallback if primary fails
FALLBACK_ENABLED=true

# Ollama settings
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_DEFAULT_MODEL=nomic-embed-text

# HuggingFace settings
HUGGINGFACE_API_KEY=your-key
HUGGINGFACE_DEFAULT_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

### Caching Settings
```bash
CACHE_ENABLED=true
CACHE_TTL=86400  # 24 hours in seconds
```

### Rate Limiting
```bash
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000
```

### File Watcher Settings
```bash
WATCH_DIRECTORY=/watch  # Inside container
POLL_INTERVAL=5  # Check every 5 seconds
```

### Qdrant Settings
```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=  # Optional, leave empty for local
QDRANT_COLLECTION=knowledge_base
```

## 🐛 Troubleshooting

### Ollama Not Working?
```bash
# Pull the model manually
docker exec -it embedding-ollama ollama pull nomic-embed-text

# Check if Ollama is running
curl http://localhost:11434/api/tags

# Check logs
docker logs embedding-ollama
```

### File Watcher Not Processing?
```bash
# Check logs for errors
docker logs file-watcher

# Verify folder is mounted
docker exec -it file-watcher ls -la /watch

# Verify files are supported format
ls -la knowledge/*.txt knowledge/*.md

# Manually trigger by touching a file
touch knowledge/test.txt
```

### Qdrant Connection Issues?
```bash
# Check Qdrant is running
curl http://localhost:6333/collections

# Check logs
docker logs embedding-qdrant

# Verify file watcher can reach it
docker exec -it file-watcher ping qdrant
```

### High Memory Usage?
```bash
# Check what's using memory
docker stats

# Redis using too much? Clear cache
curl -X POST http://localhost:8000/admin/cache/clear \
  -H "X-API-Key: your-admin-key"

# Qdrant using too much? Check collection size
curl http://localhost:6333/collections/knowledge_base
```

### Service Won't Start?
```bash
# Check all containers
docker ps -a

# Check specific service logs
docker logs embedding-service

# Verify ports aren't in use
sudo lsof -i :8000
sudo lsof -i :6379
sudo lsof -i :6333
sudo lsof -i :11434

# Rebuild if needed
cd docker
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📈 Performance & Optimization

### Expected Performance
- **Single embedding**: 50-200ms (cached: <5ms)
- **Batch embeddings (10 texts)**: 500-2000ms  
- **Knowledge search**: 10-100ms
- **Cache hit rate**: 80%+ after initial warm-up

### Optimization Tips

**1. Use Caching Aggressively**
- Cache hit rate should be >80%
- Monitor with `/metrics` endpoint
- Identical queries = instant results

**2. Batch When Possible**
```python
# Instead of this (slow):
for text in texts:
    embed(text)

# Do this (fast):
embed_batch(texts)
```

**3. Use Ollama for Development**
- Local = free + fast
- No API costs
- HuggingFace as production backup

**4. Chunk Sizes Matter**
- Default: 1000 chars (good for most cases)
- Smaller chunks = more precise search
- Larger chunks = more context per result

**5. Monitor Resource Usage**
```bash
# Check what's using resources
docker stats

# Expected usage (idle):
# - API: ~100MB RAM
# - Redis: ~50MB RAM
# - Ollama: ~500MB RAM
# - Qdrant: ~100MB RAM
# - File Watcher: ~50MB RAM
```

## 🔒 Security Best Practices

### Production Deployment

**1. Change All Default Keys**
```bash
# Generate secure keys
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Use in .env
API_KEYS=generated-secure-key-here
ADMIN_KEYS=another-secure-key-here
```

**2. Use HTTPS in Production**
```bash
# Add nginx reverse proxy
# Example nginx config:
server {
    listen 443 ssl;
    server_name embeddings.yourdomain.com;
    
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**3. Firewall Rules**
```bash
# Only expose HTTPS (443) and SSH (22)
# Block direct access to internal ports
sudo ufw allow 22/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct API access
sudo ufw deny 6379/tcp  # Block Redis
sudo ufw deny 6333/tcp  # Block Qdrant
sudo ufw enable
```

**4. Regular Security Updates**
```bash
# Update Docker images
docker-compose pull
docker-compose up -d

# Update system packages
sudo apt update && sudo apt upgrade
```

**5. Monitor for Abuse**
```bash
# Check metrics regularly
curl http://localhost:8000/metrics

# Look for:
# - Unusual request spikes
# - Low cache hit rates (could indicate key sharing)
# - High error rates
```

## 🚀 Scaling Considerations

### When to Scale?

**You're ready to scale when:**
- API latency >500ms consistently
- Cache hit rate <50%
- CPU usage >80% sustained
- Memory usage approaching limits

### Horizontal Scaling

**The service is designed to scale horizontally:**

```yaml
# docker-compose.yml (scaled version)
services:
  api:
    # ... existing config ...
    deploy:
      replicas: 3  # Run 3 instances
      
  # Add load balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

**What scales easily:**
- ✅ API service (stateless)
- ✅ File watcher (one instance sufficient)
- ✅ Redis (can use Redis Cluster)
- ✅ Qdrant (supports sharding)

### Cloud Deployment

**AWS Example:**
- API: ECS/Fargate or EKS
- Redis: ElastiCache
- Qdrant: EC2 or Qdrant Cloud
- Files: S3 + EventBridge for ingestion

**GCP Example:**
- API: Cloud Run or GKE
- Redis: Memorystore
- Qdrant: GCE or Qdrant Cloud
- Files: Cloud Storage + Cloud Functions

## 🎓 Advanced Usage

### Custom Metadata Filtering

```python
# Add files with custom metadata
# In file content, use frontmatter:

"""
---
category: technical
priority: high
department: engineering
---

Your actual content here...
"""

# Then search with filters:
results = client.search_knowledge(
    query="deployment process",
    filters={"category": "technical", "department": "engineering"}
)
```

### Multi-Collection Strategy

```python
# Use different collections for different knowledge domains
# Modify QDRANT_COLLECTION in file watcher config

# Collection 1: Technical docs
# Collection 2: Customer FAQs  
# Collection 3: Internal policies

# Search specific collection:
# (Requires code modification or pass collection name as param)
```

### Webhook Integration

```python
# Trigger embeddings via webhook (requires custom endpoint)
# Useful for:
# - CMS integration
# - Slack message archiving
# - Email thread embedding
# - Document management systems
```

## 📚 Additional Resources

### Documentation
- **API Docs**: http://localhost:8000/docs (when DEBUG=true)
- **Qdrant UI**: http://localhost:6333/dashboard
- **Redis CLI**: `docker exec -it embedding-redis redis-cli`

### Monitoring Tools
```bash
# Redis monitoring
docker exec -it embedding-redis redis-cli INFO stats

# Qdrant monitoring  
curl http://localhost:6333/collections/knowledge_base

# Container health
docker ps
docker stats
```

### Useful Commands
```bash
# See all running services
docker ps

# Follow all logs
docker-compose logs -f

# Restart everything
docker-compose restart

# Update and restart
docker-compose pull && docker-compose up -d

# Clean up old images
docker system prune -a
```

## 🤝 Contributing

This is your project! Modify, extend, and adapt as needed.

Common enhancements:
- Add more embedding providers
- Implement semantic caching
- Add webhook support
- Create admin dashboard
- Add more file formats (PDF, DOCX, etc.)

## 📄 License

Choose your own license!

## 💡 Tips & Tricks

1. **Use descriptive filenames** - They're stored in metadata
2. **Organize files in subfolders** - File watcher is recursive
3. **Monitor cache hit rate** - Higher = better performance
4. **Test with small files first** - Verify setup before bulk ingestion
5. **Keep Ollama updated** - `docker pull ollama/ollama:latest`

---

**Questions?** Check the logs first - they're very verbose and helpful!

**Having issues?** See the Troubleshooting section above.

**Ready to deploy?** See the Security Best Practices section.

🚀 **Happy Embedding!**
```

