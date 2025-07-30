#!/usr/bin/env python3
"""
Model Performance Benchmarking Script for RAG Agent System
This script tests various aspects of model performance including:
- Response time and throughput
- Quality of responses for different task types
- Memory usage and resource consumption
- RAG integration effectiveness
"""

import asyncio
import time
import json
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import sys
import os

# Add the rag-agent src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from model_router.local_client import LocalLLMClient, LocalRequest, LocalMessage
from common.vector_client import VectorClient
from common.logging import get_logger

logger = get_logger("benchmark")

@dataclass
class BenchmarkResult:
    """Results from a single benchmark test."""
    test_name: str
    model: str
    prompt: str
    response: str
    response_time: float
    token_count: int
    success: bool
    error: Optional[str] = None

@dataclass
class BenchmarkSuite:
    """Complete benchmark results for a model."""
    model: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    total_tokens: int
    tokens_per_second: float
    test_results: List[BenchmarkResult]

class ModelBenchmark:
    """Benchmark suite for testing model performance."""
    
    def __init__(self):
        self.client = LocalLLMClient()
        self.vector_client = VectorClient()
        
        # Test scenarios for different types of tasks
        self.test_scenarios = {
            "code_generation": [
                "Write a Python function to calculate fibonacci numbers",
                "Create a REST API endpoint for user authentication",
                "Implement a binary search algorithm in Python",
                "Write a function to validate email addresses using regex",
                "Create a class for managing a shopping cart with add, remove, and total methods"
            ],
            "code_review": [
                "Review this code for potential bugs: def divide(a, b): return a / b",
                "Analyze this SQL query for security issues: SELECT * FROM users WHERE id = '" + user_input + "'",
                "Check this JavaScript function for performance issues: function findMax(arr) { let max = 0; for(let i = 0; i < arr.length; i++) { for(let j = 0; j < arr.length; j++) { if(arr[j] > max) max = arr[j]; } } return max; }",
                "Evaluate this Python code for memory leaks: class DataProcessor: def __init__(self): self.cache = {} def process(self, data): self.cache[data] = expensive_operation(data) return self.cache[data]",
                "Review this error handling: try: risky_operation() except: pass"
            ],
            "architectural_analysis": [
                "Design a microservices architecture for an e-commerce platform",
                "Explain the trade-offs between SQL and NoSQL databases for a social media app",
                "Describe how to implement horizontal scaling for a web application",
                "Design a caching strategy for a high-traffic news website",
                "Plan the architecture for a real-time chat application"
            ],
            "debugging": [
                "Debug this error: AttributeError: 'NoneType' object has no attribute 'strip'",
                "Fix this performance issue: Query taking 30 seconds to return 100 records",
                "Resolve this memory issue: Application consuming 8GB RAM for 1000 users",
                "Debug this network error: Connection timeout after 5 seconds",
                "Fix this race condition in concurrent code"
            ],
            "general_purpose": [
                "Explain the concept of machine learning to a beginner",
                "Summarize the key principles of software engineering",
                "What are the best practices for API design?",
                "Compare different programming paradigms",
                "Explain the importance of testing in software development"
            ]
        }
    
    async def setup_rag_data(self):
        """Set up test data in the vector database for RAG testing."""
        logger.info("Setting up RAG test data...")
        
        test_documents = [
            {
                "text": "FastAPI is a modern, fast web framework for building APIs with Python 3.6+ based on standard Python type hints. It provides automatic API documentation, data validation, and serialization.",
                "metadata": {"type": "framework", "language": "python", "category": "web"}
            },
            {
                "text": "The Repository pattern is a design pattern that encapsulates the logic needed to access data sources. It centralizes common data access functionality, providing better maintainability and decoupling.",
                "metadata": {"type": "pattern", "category": "architecture"}
            },
            {
                "text": "SQL injection is a code injection technique that might destroy your database. It occurs when user input is inserted into a SQL query without proper sanitization or parameterization.",
                "metadata": {"type": "security", "category": "vulnerability"}
            },
            {
                "text": "Docker containers share the OS kernel with other containers, making them more efficient than virtual machines. They include the application and all its dependencies in a portable package.",
                "metadata": {"type": "technology", "category": "containerization"}
            },
            {
                "text": "Test-driven development (TDD) is a software development process where tests are written before the actual code. The cycle involves: Red (write failing test), Green (make test pass), Refactor (improve code).",
                "metadata": {"type": "methodology", "category": "testing"}
            }
        ]
        
        for doc in test_documents:
            await self.vector_client.add_document(
                text=doc["text"],
                metadata=doc["metadata"]
            )
        
        logger.info(f"Added {len(test_documents)} documents to vector database")
    
    async def benchmark_model(self, model: str, num_iterations: int = 3) -> BenchmarkSuite:
        """Benchmark a specific model across all test scenarios."""
        logger.info(f"Benchmarking model: {model}")
        
        all_results = []
        
        for category, prompts in self.test_scenarios.items():
            logger.info(f"Testing {category} scenarios...")
            
            for i, prompt in enumerate(prompts):
                # Run multiple iterations for statistical significance
                for iteration in range(num_iterations):
                    test_name = f"{category}_{i}_{iteration}"
                    result = await self.run_single_test(model, test_name, prompt)
                    all_results.append(result)
        
        # Calculate aggregate statistics
        successful_results = [r for r in all_results if r.success]
        failed_results = [r for r in all_results if not r.success]
        
        if successful_results:
            response_times = [r.response_time for r in successful_results]
            token_counts = [r.token_count for r in successful_results]
            
            total_time = sum(response_times)
            total_tokens = sum(token_counts)
            
            suite = BenchmarkSuite(
                model=model,
                total_tests=len(all_results),
                successful_tests=len(successful_results),
                failed_tests=len(failed_results),
                avg_response_time=statistics.mean(response_times),
                min_response_time=min(response_times),
                max_response_time=max(response_times),
                total_tokens=total_tokens,
                tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
                test_results=all_results
            )
        else:
            suite = BenchmarkSuite(
                model=model,
                total_tests=len(all_results),
                successful_tests=0,
                failed_tests=len(failed_results),
                avg_response_time=0,
                min_response_time=0,
                max_response_time=0,
                total_tokens=0,
                tokens_per_second=0,
                test_results=all_results
            )
        
        logger.info(f"Completed benchmarking {model}: {suite.successful_tests}/{suite.total_tests} successful")
        return suite
    
    async def run_single_test(self, model: str, test_name: str, prompt: str) -> BenchmarkResult:
        """Run a single benchmark test."""
        try:
            # Create request
            messages = [LocalMessage(role="user", content=prompt)]
            request = LocalRequest(
                model=model,
                messages=messages,
                max_tokens=2048,
                temperature=0.1
            )
            
            # Measure response time
            start_time = time.time()
            response = await self.client.send_message(request)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            return BenchmarkResult(
                test_name=test_name,
                model=model,
                prompt=prompt,
                response=response.content,
                response_time=response_time,
                token_count=response.usage.get("output_tokens", 0),
                success=True
            )
            
        except Exception as e:
            logger.error(f"Test {test_name} failed: {e}")
            return BenchmarkResult(
                test_name=test_name,
                model=model,
                prompt=prompt,
                response="",
                response_time=0,
                token_count=0,
                success=False,
                error=str(e)
            )
    
    async def benchmark_rag_integration(self, model: str) -> Dict[str, Any]:
        """Test RAG integration performance."""
        logger.info(f"Testing RAG integration for {model}")
        
        rag_queries = [
            "How do I use FastAPI for building APIs?",
            "What is the Repository pattern and when should I use it?",
            "How can I prevent SQL injection attacks?",
            "What are the benefits of using Docker containers?",
            "Explain the TDD development process"
        ]
        
        results = []
        
        for query in rag_queries:
            try:
                # Test with RAG context
                start_time = time.time()
                context = await self.vector_client.get_context(query)
                context_time = time.time() - start_time
                
                # Send query with context
                messages = [LocalMessage(role="user", content=query)]
                request = LocalRequest(
                    model=model,
                    messages=messages,
                    system=f"Use this context to inform your response: {context}",
                    max_tokens=1024
                )
                
                start_time = time.time()
                response = await self.client.send_message(request)
                response_time = time.time() - start_time
                
                results.append({
                    "query": query,
                    "context_retrieval_time": context_time,
                    "response_time": response_time,
                    "total_time": context_time + response_time,
                    "context_length": len(context),
                    "response_length": len(response.content),
                    "success": True
                })
                
            except Exception as e:
                logger.error(f"RAG test failed for query '{query[:50]}...': {e}")
                results.append({
                    "query": query,
                    "context_retrieval_time": 0,
                    "response_time": 0,
                    "total_time": 0,
                    "context_length": 0,
                    "response_length": 0,
                    "success": False,
                    "error": str(e)
                })
        
        # Calculate RAG-specific metrics
        successful_results = [r for r in results if r.get("success", False)]
        
        if successful_results:
            avg_context_time = statistics.mean([r["context_retrieval_time"] for r in successful_results])
            avg_response_time = statistics.mean([r["response_time"] for r in successful_results])
            avg_total_time = statistics.mean([r["total_time"] for r in successful_results])
            avg_context_length = statistics.mean([r["context_length"] for r in successful_results])
            
            rag_metrics = {
                "model": model,
                "total_queries": len(results),
                "successful_queries": len(successful_results),
                "avg_context_retrieval_time": avg_context_time,
                "avg_response_time": avg_response_time,
                "avg_total_time": avg_total_time,
                "avg_context_length": avg_context_length,
                "context_utilization_rate": len([r for r in successful_results if r["context_length"] > 0]) / len(successful_results),
                "detailed_results": results
            }
        else:
            rag_metrics = {
                "model": model,
                "total_queries": len(results),
                "successful_queries": 0,
                "avg_context_retrieval_time": 0,
                "avg_response_time": 0,
                "avg_total_time": 0,
                "avg_context_length": 0,
                "context_utilization_rate": 0,
                "detailed_results": results
            }
        
        return rag_metrics
    
    async def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark across all available models."""
        logger.info("Starting comprehensive model benchmark")
        
        # Set up RAG data
        await self.setup_rag_data()
        
        # Test connection to services
        if not await self.client.test_connection():
            logger.error("Failed to connect to LLM services")
            return {}
        
        if not await self.vector_client.test_connection():
            logger.error("Failed to connect to vector database")
            return {}
        
        # Get available models
        available_models = self.client.list_available_models()
        logger.info(f"Available models: {available_models}")
        
        benchmark_results = {}
        
        for model in available_models:
            try:
                logger.info(f"Benchmarking model: {model}")
                
                # Standard benchmark
                model_benchmark = await self.benchmark_model(model, num_iterations=2)
                
                # RAG integration test
                rag_benchmark = await self.benchmark_rag_integration(model)
                
                benchmark_results[model] = {
                    "standard_benchmark": asdict(model_benchmark),
                    "rag_benchmark": rag_benchmark,
                    "timestamp": time.time()
                }
                
            except Exception as e:
                logger.error(f"Failed to benchmark model {model}: {e}")
                benchmark_results[model] = {
                    "error": str(e),
                    "timestamp": time.time()
                }
        
        return {
            "benchmark_summary": {
                "total_models_tested": len(benchmark_results),
                "successful_models": len([r for r in benchmark_results.values() if "error" not in r]),
                "test_timestamp": time.time(),
                "test_scenarios_count": sum(len(prompts) for prompts in self.test_scenarios.values())
            },
            "model_results": benchmark_results
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = None):
        """Save benchmark results to file."""
        if filename is None:
            timestamp = int(time.time())
            filename = f"benchmark_results_{timestamp}.json"
        
        filepath = os.path.join(os.path.dirname(__file__), "..", "benchmarks", filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Benchmark results saved to {filepath}")
        return filepath
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a summary of benchmark results."""
        print("\\n" + "="*80)
        print("MODEL PERFORMANCE BENCHMARK SUMMARY")
        print("="*80)
        
        summary = results.get("benchmark_summary", {})
        print(f"Total models tested: {summary.get('total_models_tested', 0)}")
        print(f"Successful models: {summary.get('successful_models', 0)}")
        print(f"Test scenarios: {summary.get('test_scenarios_count', 0)}")
        
        print("\\n" + "-"*80)
        print("INDIVIDUAL MODEL RESULTS")
        print("-"*80)
        
        for model, data in results.get("model_results", {}).items():
            if "error" in data:
                print(f"\\n{model}: FAILED - {data['error']}")
                continue
                
            std_bench = data.get("standard_benchmark", {})
            rag_bench = data.get("rag_benchmark", {})
            
            print(f"\\n{model}:")
            print(f"  Standard Tests: {std_bench.get('successful_tests', 0)}/{std_bench.get('total_tests', 0)} passed")
            print(f"  Avg Response Time: {std_bench.get('avg_response_time', 0):.3f}s")
            print(f"  Tokens/Second: {std_bench.get('tokens_per_second', 0):.1f}")
            print(f"  RAG Integration: {rag_bench.get('successful_queries', 0)}/{rag_bench.get('total_queries', 0)} passed")
            print(f"  RAG Avg Time: {rag_bench.get('avg_total_time', 0):.3f}s")

async def main():
    """Main function to run benchmarks."""
    benchmark = ModelBenchmark()
    
    print("Starting comprehensive model benchmark...")
    print("This will test response time, quality, and RAG integration across all available models.")
    
    try:
        results = await benchmark.run_comprehensive_benchmark()
        
        # Save results
        filepath = benchmark.save_results(results)
        
        # Print summary
        benchmark.print_summary(results)
        
        print(f"\\nDetailed results saved to: {filepath}")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}")
        print(f"Benchmark failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())