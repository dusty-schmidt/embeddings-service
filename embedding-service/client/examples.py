# client/examples.py

"""
Usage examples for the Embedding Client
"""

from embedding_client import EmbeddingClient
import numpy as np


def example_single_embedding():
    """Example: Generate a single embedding"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    # Generate embedding
    result = client.embed("What is machine learning?")
    
    print(f"Embedding dimensions: {result['dimensions']}")
    print(f"Tokens used: {result['tokens']}")
    print(f"Cached: {result['cached']}")
    print(f"Provider: {result['provider']}")
    print(f"First 5 values: {result['embedding'][:5]}")
    
    return result['embedding']


def example_batch_embeddings():
    """Example: Generate multiple embeddings"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    texts = [
        "What is artificial intelligence?",
        "How does machine learning work?",
        "Explain neural networks",
        "What is deep learning?"
    ]
    
    result = client.embed_batch(texts)
    
    print(f"Total embeddings: {result['count']}")
    print(f"Total tokens: {result['total_tokens']}")
    print(f"Cached count: {result['cached_count']}")
    print(f"Cache hit rate: {result['cached_count'] / result['count'] * 100:.1f}%")
    
    return result['embeddings']


def example_knowledge_search():
    """Example: Search the knowledge base"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    # Search for relevant information
    results = client.search_knowledge(
        query="Tell me about machine learning",
        limit=5,
        score_threshold=0.7
    )
    
    print(f"\nFound {results['count']} results:")
    for i, result in enumerate(results['results'], 1):
        print(f"\n{i}. Score: {result['score']:.3f}")
        print(f"   Text: {result['text'][:100]}...")
        print(f"   Source: {result['metadata'].get('filename', 'unknown')}")


def example_rag_chatbot():
    """Example: Simple RAG chatbot"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    def answer_question(question: str) -> str:
        # 1. Search knowledge base
        results = client.search_knowledge(query=question, limit=3)
        
        # 2. Build context from results
        if results['count'] == 0:
            return "I don't have enough information to answer that question."
        
        context = "\n\n".join([r['text'] for r in results['results']])
        
        # 3. Return context (you'd send this to your LLM)
        print(f"Context found ({results['count']} sources):")
        print(context[:500] + "...\n")
        
        return f"[Send this context + question to your LLM]\nQuestion: {question}\nContext: {context}"
    
    # Test it
    response = answer_question("What is machine learning?")
    return response


def example_semantic_similarity():
    """Example: Calculate semantic similarity"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    # Embed two texts
    text1 = "The cat sat on the mat"
    text2 = "A feline rested on the rug"
    
    emb1 = client.embed(text1)['embedding']
    emb2 = client.embed(text2)['embedding']
    
    # Calculate cosine similarity
    def cosine_similarity(a, b):
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    similarity = cosine_similarity(emb1, emb2)
    print(f"Similarity between texts: {similarity:.3f}")
    print(f"Text 1: {text1}")
    print(f"Text 2: {text2}")


def example_check_health():
    """Example: Check service health"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    health = client.health_check()
    print(f"Service: {health['service']}")
    print(f"Status: {health['status']}")
    print(f"Cache: {'Available' if health['cache_available'] else 'Unavailable'}")
    print(f"Providers:")
    for provider, status in health['providers'].items():
        print(f"  - {provider}: {'✓' if status else '✗'}")


def example_get_stats():
    """Example: Get knowledge base statistics"""
    client = EmbeddingClient(
        base_url="http://localhost:8000",
        api_key="your-api-key-here"
    )
    
    stats = client.get_knowledge_stats()
    print(f"Collection: {stats['collection_name']}")
    print(f"Total vectors: {stats['total_vectors']}")
    print(f"Total points: {stats['total_points']}")
    print(f"Status: {stats['status']}")


if __name__ == "__main__":
    print("=" * 60)
    print("EMBEDDING CLIENT EXAMPLES")
    print("=" * 60)
    
    try:
        print("\n1. Single Embedding:")
        example_single_embedding()
        
        print("\n2. Batch Embeddings:")
        example_batch_embeddings()
        
        print("\n3. Knowledge Search:")
        example_knowledge_search()
        
        print("\n4. Health Check:")
        example_check_health()
        
        print("\n5. Knowledge Stats:")
        example_get_stats()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the service is running at http://localhost:8000")