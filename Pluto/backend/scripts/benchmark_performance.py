"""
Performance benchmark script
"""
import asyncio
import aiohttp
import time
from statistics import mean, stdev

BASE_URL = "http://localhost:8000/api/v1"

async def test_query_latency(session, query, session_id, iterations=10):
    """Measure query latency"""
    latencies = []
    
    for i in range(iterations):
        start = time.time()
        
        async with session.post(
            f"{BASE_URL}/query/",
            headers={"X-Session-ID": session_id},
            json={"query": query}
        ) as response:
            await response.json()
        
        latencies.append(time.time() - start)
    
    return {
        "mean": mean(latencies),
        "stdev": stdev(latencies) if len(latencies) > 1 else 0,
        "min": min(latencies),
        "max": max(latencies)
    }

async def test_concurrent_users(num_users=10):
    """Simulate concurrent users"""
    async with aiohttp.ClientSession() as session:
        tasks = [
            test_query_latency(session, f"Query from user {i}", f"session-{i}")
            for i in range(num_users)
        ]
        
        results = await asyncio.gather(*tasks)
        
        print(f"\n{'='*60}")
        print(f"CONCURRENT USERS TEST ({num_users} users)")
        print(f"{'='*60}")
        
        all_means = [r['mean'] for r in results]
        print(f"Average latency: {mean(all_means):.2f}s")
        print(f"Worst latency: {max(r['max'] for r in results):.2f}s")
        print(f"Best latency: {min(r['min'] for r in results):.2f}s")

if __name__ == "__main__":
    asyncio.run(test_concurrent_users(num_users=10))