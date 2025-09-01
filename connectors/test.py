import requests
import json
from datetime import datetime, timedelta, timezone

# Configuration
QDRANT_URL = "http://localhost:6333"
OLLAMA_URL = "http://localhost:11434"
COLLECTION = "text_docs"

def get_embeddings(text, model="nomic-embed-text"):
    """Get embeddings from Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": model, "prompt": text},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def generate_response(system_prompt, user_prompt, model="llama3.1:8b-instruct-q4_K_M"):
    """Generate response from Ollama"""
    try:
        payload = {
            "model": model,
            "prompt": f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n",
            "stream": False
        }
        response = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()["response"].strip()
    except Exception as e:
        print(f"Generation error: {e}")
        return None

def search_news(query_vector, ticker="AAPL", days=30, limit=20):
    """Search for news using Qdrant REST API"""
    try:
        # Calculate cutoff timestamp
        cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        
        # Build search payload
        search_payload = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "ticker", "match": {"any": [ticker]}},
                    {"key": "published_at", "range": {"gte": cutoff}}
                ]
            }
        }
        
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
            json=search_payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["result"]
    except Exception as e:
        print(f"Search error: {e}")
        return []

def search_all_tickers(query_vector, days=30, limit=50):
    """Search for news across all tickers"""
    try:
        # Calculate cutoff timestamp
        cutoff = int((datetime.now(timezone.utc) - timedelta(days=days)).timestamp())
        
        # Build search payload without ticker filter
        search_payload = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
            "filter": {
                "must": [
                    {"key": "published_at", "range": {"gte": cutoff}}
                ]
            }
        }
        
        response = requests.post(
            f"{QDRANT_URL}/collections/{COLLECTION}/points/search",
            json=search_payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()["result"]
    except Exception as e:
        print(f"Search error: {e}")
        return []

def format_context(results, max_chars=3000):
    """Format search results into context"""
    if not results:
        return "No relevant news found."
    
    context_parts = []
    total_chars = 0
    
    for result in results:
        payload = result.get("payload", {})
        title = payload.get("title", "No title")
        summary = payload.get("summary", "No summary")
        url = payload.get("url", "No URL")
        ticker = payload.get("ticker", "Unknown")
        pub_timestamp = payload.get("published_at", 0)
        
        # Convert timestamp to readable date
        try:
            pub_date = datetime.fromtimestamp(pub_timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        except:
            pub_date = str(pub_timestamp)
        
        # Create context block with ticker info
        block = f"[{ticker}] {title} ({pub_date})\n{summary[:200]}...\nURL: {url}"
        
        if total_chars + len(block) > max_chars:
            break
            
        context_parts.append(block)
        total_chars += len(block)
    
    return "\n\n---\n\n".join(context_parts)

def analyze_news_custom(ticker, custom_query, days=30):
    """Analyze news with a custom query for specific ticker"""
    print(f"Analyzing news for {ticker} with custom query: '{custom_query}' (last {days} days)...")
    
    # Get embeddings for custom query
    print("Getting embeddings...")
    query_vector = get_embeddings(custom_query)
    if not query_vector:
        return {"error": "Failed to get embeddings"}
    
    # Search for news
    print("Searching for news...")
    results = search_news(query_vector, ticker, days)
    if not results:
        return {"answer": f"No recent news found for {ticker} in the last {days} days.", "citations": []}
    
    # Build context
    print("Building context...")
    context = format_context(results)
    
    # Generate analysis
    print("Generating analysis...")
    system_prompt = (
        "You are a cautious markets analyst. Use ONLY the provided context. "
        "Answer the user's specific question about the company based on the news. "
        "Prefer concrete, recent facts; avoid speculation. Keep it brief."
    )
    
    user_prompt = f"Question: {custom_query}\n\nContext:\n{context}"
    
    answer = generate_response(system_prompt, user_prompt)
    if not answer:
        return {"error": "Failed to generate response"}
    
    # Prepare citations
    citations = []
    for result in results[:6]:  # Top 6 results
        payload = result.get("payload", {})
        citations.append({
            "title": payload.get("title", ""),
            "url": payload.get("url", ""),
            "published_at": payload.get("published_at", ""),
            "ticker": payload.get("ticker", ""),
            "score": result.get("score", 0)
        })
    
    return {
        "answer": answer,
        "citations": citations,
        "total_results": len(results)
    }

def ask_cross_ticker_question(question, days=30):
    """Ask a question that searches across all tickers"""
    print(f"Searching across all tickers for: '{question}' (last {days} days)...")
    
    # Get embeddings for the question
    print("Getting embeddings...")
    query_vector = get_embeddings(question)
    if not query_vector:
        return {"error": "Failed to get embeddings"}
    
    # Search across all tickers
    print("Searching across all tickers...")
    results = search_all_tickers(query_vector, days, limit=100)
    if not results:
        return {"answer": f"No relevant news found across any tickers in the last {days} days.", "citations": []}
    
    # Build context
    print("Building context...")
    context = format_context(results)
    
    # Generate analysis
    print("Generating analysis...")
    system_prompt = (
        "You are a cautious markets analyst. Use ONLY the provided context. "
        "Answer the user's question based on the news from various companies. "
        "Prefer concrete, recent facts; avoid speculation. Keep it brief."
    )
    
    user_prompt = f"Question: {question}\n\nContext:\n{context}"
    
    answer = generate_response(system_prompt, user_prompt)
    if not answer:
        return {"error": "Failed to generate response"}
    
    # Prepare citations
    citations = []
    for result in results[:8]:  # Top 8 results since we're across multiple tickers
        payload = result.get("payload", {})
        citations.append({
            "title": payload.get("title", ""),
            "url": payload.get("url", ""),
            "published_at": payload.get("published_at", ""),
            "ticker": payload.get("ticker", ""),
            "score": result.get("score", 0)
        })
    
    return {
        "answer": answer,
        "citations": citations,
        "total_results": len(results)
    }

def analyze_news(ticker="AAPL", days=30):
    """Main function to analyze news for a ticker"""
    print(f"Analyzing news for {ticker} (last {days} days)...")
    
    # Create query
    query = f"What are the latest news for {ticker} and what do they imply?"
    
    # Get embeddings
    print("Getting embeddings...")
    query_vector = get_embeddings(query)
    if not query_vector:
        return {"error": "Failed to get embeddings"}
    
    # Search for news
    print("Searching for news...")
    results = search_news(query_vector, ticker, days)
    if not results:
        return {"answer": f"No recent news found for {ticker} in the last {days} days.", "citations": []}
    
    # Build context
    print("Building context...")
    context = format_context(results)
    
    # Generate analysis
    print("Generating analysis...")
    system_prompt = (
        "You are a cautious markets analyst. Use ONLY the provided context. "
        "Summarize the latest news for the company, infer what's going on, and cite URLs. "
        "Prefer concrete, recent facts; avoid speculation. Keep it brief."
    )
    
    user_prompt = f"Question: {query}\n\nContext:\n{context}"
    
    answer = generate_response(system_prompt, user_prompt)
    if not answer:
        return {"error": "Failed to generate response"}
    
    # Prepare citations
    citations = []
    for result in results[:6]:  # Top 6 results
        payload = result.get("payload", {})
        citations.append({
            "title": payload.get("title", ""),
            "url": payload.get("url", ""),
            "published_at": payload.get("published_at", ""),
            "ticker": payload.get("ticker", ""),
            "score": result.get("score", 0)
        })
    
    return {
        "answer": answer,
        "citations": citations,
        "total_results": len(results)
    }

def print_nice_results(result):
    """Print results in a nice, readable format"""
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    print("\n" + "="*60)
    print(f"📊 NEWS ANALYSIS RESULTS")
    print("="*60)
    
    # Print the main answer
    print(f"\n💡 ANALYSIS:")
    print("-" * 40)
    print(result.get("answer", "No analysis generated"))
    
    # Print citations
    citations = result.get("citations", [])
    if citations:
        print(f"\n📚 SOURCES ({len(citations)} articles):")
        print("-" * 40)
        for i, citation in enumerate(citations, 1):
            title = citation.get("title", "No title")
            url = citation.get("url", "No URL")
            ticker = citation.get("ticker", "Unknown")
            pub_date = citation.get("published_at", "Unknown date")
            score = citation.get("score", 0)
            
            # Convert timestamp to readable date
            try:
                if pub_date and pub_date != "Unknown date":
                    date_obj = datetime.fromtimestamp(int(pub_date), tz=timezone.utc)
                    pub_date = date_obj.strftime("%Y-%m-%d %H:%M")
            except:
                pass
            
            print(f"{i}. [{ticker}] {title}")
            print(f"   📅 {pub_date} | 🔗 {url}")
            if score > 0:
                print(f"   📊 Relevance: {score:.3f}")
            print()
    
    # Print summary stats
    total_results = result.get("total_results", 0)
    print(f"📈 Total articles found: {total_results}")
    print("="*60)

if __name__ == "__main__":
    import sys
    
    # Get ticker from command line argument or user input
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    else:
        ticker = input("Enter ticker symbol (e.g., AAPL) or 'all' for cross-ticker question: ").upper().strip()
    
    # Handle cross-ticker question
    if ticker.lower() in ['all', 'cross', 'market']:
        question = input("What would you like to know about the market? ")
        if not question:
            print("No question provided. Exiting.")
            exit()
        
        result = ask_cross_ticker_question(question, days=45)
    else:
        if not ticker:
            print("No ticker provided. Using AAPL as default.")
            ticker = "AAPL"
        
        # Get custom query if provided
        custom_query = None
        if len(sys.argv) > 2:
            custom_query = sys.argv[2]
        
        print(f"Analyzing news for {ticker}...")
        
        if custom_query:
            print(f"Custom query: {custom_query}")
            result = analyze_news_custom(ticker, custom_query, days=45)
        else:
            result = analyze_news(ticker, days=45)
    
    # Print results nicely
    print_nice_results(result)
    
    # Also print raw JSON for debugging if needed
    if "--debug" in sys.argv:
        print("\n🔍 DEBUG - Raw JSON:")
        print(json.dumps(result, indent=2))
