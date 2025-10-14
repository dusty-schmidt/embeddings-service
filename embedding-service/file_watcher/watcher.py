# file_watcher/watcher.py

import os
import time
import hashlib
import requests
from pathlib import Path
from typing import Set, Dict, Any
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid


class KnowledgeFileHandler(FileSystemEventHandler):
    """Handles file system events for knowledge ingestion"""
    
    def __init__(
        self,
        embedding_service_url: str,
        api_key: str,
        qdrant_client: QdrantClient,
        collection_name: str
    ):
        self.embedding_service_url = embedding_service_url.rstrip('/')
        self.api_key = api_key
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.processed_files: Set[str] = set()
        self.file_hashes: Dict[str, str] = {}
        
        # Ensure collection exists
        self._ensure_collection()
    
    def _ensure_collection(self):
        """Ensure Qdrant collection exists"""
        try:
            collections = self.qdrant_client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if not exists:
                # Create with default 768 dimensions
                self.qdrant_client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=768,
                        distance=Distance.COSINE
                    )
                )
                print(f"✓ Created collection: {self.collection_name}")
        except Exception as e:
            print(f"Error ensuring collection: {e}")
    
    def _get_file_hash(self, filepath: str) -> str:
        """Calculate hash of file content"""
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    def _should_process_file(self, filepath: str) -> bool:
        """Check if file should be processed"""
        # Only process text files
        if not filepath.endswith(('.txt', '.md', '.markdown')):
            return False
        
        # Check if file was modified
        file_hash = self._get_file_hash(filepath)
        
        if filepath in self.file_hashes:
            if self.file_hashes[filepath] == file_hash:
                return False  # File unchanged
        
        self.file_hashes[filepath] = file_hash
        return True
    
    def _read_file(self, filepath: str) -> str:
        """Read file content"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> list:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size // 2:
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - overlap
        
        return chunks
    
    def _embed_text(self, text: str) -> Dict[str, Any]:
        """Get embedding from embedding service"""
        try:
            response = requests.post(
                f"{self.embedding_service_url}/api/embed",
                headers={
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": text,
                    "use_cache": True
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error getting embedding: {e}")
            raise
    
    def _store_in_qdrant(
        self,
        text: str,
        embedding: list,
        metadata: Dict[str, Any]
    ):
        """Store embedding in Qdrant"""
        point_id = str(uuid.uuid4())
        
        payload = {
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            **metadata
        }
        
        point = PointStruct(
            id=point_id,
            vector=embedding,
            payload=payload
        )
        
        self.qdrant_client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )
        
        return point_id
    
    def process_file(self, filepath: str):
        """Process a single file"""
        if not self._should_process_file(filepath):
            print(f"⊘ Skipping {filepath} (unchanged or unsupported)")
            return
        
        print(f"\n📄 Processing: {filepath}")
        
        try:
            # Read file
            content = self._read_file(filepath)
            
            if not content.strip():
                print(f"  ⚠️  Empty file, skipping")
                return
            
            # Split into chunks
            chunks = self._chunk_text(content)
            print(f"  ✂️  Split into {len(chunks)} chunks")
            
            # Process each chunk
            for i, chunk in enumerate(chunks):
                print(f"  🔄 Embedding chunk {i+1}/{len(chunks)}...")
                
                # Get embedding
                result = self._embed_text(chunk)
                
                # Store in Qdrant
                metadata = {
                    "source": filepath,
                    "filename": os.path.basename(filepath),
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "provider": result.get("provider"),
                    "model": result.get("model"),
                    "cached": result.get("cached", False)
                }
                
                point_id = self._store_in_qdrant(
                    text=chunk,
                    embedding=result["embedding"],
                    metadata=metadata
                )
                
                print(f"  ✓ Stored chunk {i+1} (ID: {point_id[:8]}...)")
            
            self.processed_files.add(filepath)
            print(f"✅ Completed: {filepath}\n")
            
        except Exception as e:
            print(f"❌ Error processing {filepath}: {e}\n")
    
    def on_created(self, event):
        """Called when a file is created"""
        if not event.is_directory:
            print(f"\n🆕 New file detected: {event.src_path}")
            time.sleep(1)  # Wait for file to be fully written
            self.process_file(event.src_path)
    
    def on_modified(self, event):
        """Called when a file is modified"""
        if not event.is_directory:
            print(f"\n📝 File modified: {event.src_path}")
            time.sleep(1)  # Wait for file to be fully written
            self.process_file(event.src_path)


def main():
    """Main file watcher loop"""
    # Configuration from environment
    EMBEDDING_SERVICE_URL = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "dev-key-123")
    QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
    QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
    COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "knowledge_base")
    WATCH_DIRECTORY = os.getenv("WATCH_DIRECTORY", "./knowledge")
    POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "5"))
    
    print("=" * 60)
    print("🔍 KNOWLEDGE BASE FILE WATCHER")
    print("=" * 60)
    print(f"Watch Directory: {WATCH_DIRECTORY}")
    print(f"Embedding Service: {EMBEDDING_SERVICE_URL}")
    print(f"Qdrant: {QDRANT_HOST}:{QDRANT_PORT}")
    print(f"Collection: {COLLECTION_NAME}")
    print("=" * 60)
    
    # Ensure watch directory exists
    os.makedirs(WATCH_DIRECTORY, exist_ok=True)
    
    # Initialize Qdrant client
    if QDRANT_API_KEY:
        qdrant_client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT,
            api_key=QDRANT_API_KEY
        )
    else:
        qdrant_client = QdrantClient(
            host=QDRANT_HOST,
            port=QDRANT_PORT
        )
    
    # Create event handler
    event_handler = KnowledgeFileHandler(
        embedding_service_url=EMBEDDING_SERVICE_URL,
        api_key=API_KEY,
        qdrant_client=qdrant_client,
        collection_name=COLLECTION_NAME
    )
    
    # Process existing files
    print("\n📂 Processing existing files...")
    for filepath in Path(WATCH_DIRECTORY).rglob('*.txt'):
        event_handler.process_file(str(filepath))
    for filepath in Path(WATCH_DIRECTORY).rglob('*.md'):
        event_handler.process_file(str(filepath))
    
    print("\n👀 Watching for new files...")
    print("   (Press Ctrl+C to stop)\n")
    
    # Start watching
    observer = Observer()
    observer.schedule(event_handler, WATCH_DIRECTORY, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping file watcher...")
        observer.stop()
    
    observer.join()
    print("✓ File watcher stopped\n")


if __name__ == "__main__":
    main()