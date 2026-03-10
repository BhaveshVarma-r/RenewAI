"""Test script for ChromaDB semantic search."""

import asyncio
import os
from dotenv import load_dotenv
from mock_services.vector_search import MockVectorSearch

def test_semantic_search_sync():
    print("Initializing Vector Search...")
    # Initialize outside of an active loop to avoid RuntimeError
    vs = MockVectorSearch()
    
    async def run_queries():
        queries = [
            "I don't have enough money for this",
            "How do I pay in parts?",
            "I'm worried about the company's reputation",
            "What happens if I miss the deadline?"
        ]
        
        for query in queries:
            print(f"\nQUERY: {query}")
            results = await vs.async_similarity_search(query, k=2)
            for i, res in enumerate(results):
                print(f"  Result {i+1}: {res['objection']} (Score: {res['score']})")
                print(f"  Response: {res['response'][:100]}...")

    asyncio.run(run_queries())

if __name__ == "__main__":
    load_dotenv()
    test_semantic_search_sync()
