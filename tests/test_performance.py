import pytest
import time
import asyncio
import aiohttp
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict
import json

# 性能测试配置
TEST_CONFIG = {
    "base_url": "http://localhost:8000",
    "num_requests": 100,
    "concurrent_users": 10,
    "test_duration": 60,  # 秒
    "max_avg_response_time": 10.0,  # 最大平均响应时间（秒）
    "max_error_rate": 5.0,  # 最大错误率（%）
    "min_requests_per_second": 0.5  # 最小每秒请求数
}

class PerformanceMetrics:
    def __init__(self):
        self.response_times: List[float] = []
        self.error_count: int = 0
        self.success_count: int = 0
        self.start_time: float = 0
        self.end_time: float = 0

    def add_response_time(self, time: float):
        self.response_times.append(time)

    def add_error(self):
        self.error_count += 1

    def add_success(self):
        self.success_count += 1

    def start(self):
        self.start_time = time.time()

    def stop(self):
        self.end_time = time.time()

    def get_statistics(self) -> Dict:
        if not self.response_times:
            return {
                "total_requests": 0,
                "error_rate": 0,
                "avg_response_time": 0,
                "median_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "requests_per_second": 0,
                "total_duration": 0
            }

        total_duration = self.end_time - self.start_time
        total_requests = len(self.response_times)
        
        return {
            "total_requests": total_requests,
            "error_rate": (self.error_count / total_requests) * 100 if total_requests > 0 else 0,
            "avg_response_time": statistics.mean(self.response_times),
            "median_response_time": statistics.median(self.response_times),
            "min_response_time": min(self.response_times),
            "max_response_time": max(self.response_times),
            "requests_per_second": total_requests / total_duration if total_duration > 0 else 0,
            "total_duration": total_duration
        }

async def execute_workflow(session, url: str, workflow: Dict) -> float:
    """执行单个工作流并返回响应时间"""
    start_time = time.time()
    try:
        async with session.post(f"{url}/api/workflow/execute", json=workflow) as response:
            await response.json()
            return time.time() - start_time
    except Exception as e:
        print(f"Error executing workflow: {str(e)}")
        return -1

async def load_test(url: str, num_requests: int, concurrent_users: int) -> PerformanceMetrics:
    """执行负载测试"""
    metrics = PerformanceMetrics()
    metrics.start()

    # 测试工作流数据
    test_workflow = {
        "workflow": {
            "test_node": {
                "inputs": {"text": "performance test"},
                "class_type": "test_node_type"
            }
        },
        "client_id": "perf_test_client"
    }

    async with aiohttp.ClientSession() as session:
        tasks = []
        for _ in range(num_requests):
            task = execute_workflow(session, url, test_workflow)
            tasks.append(task)

        # 分批执行请求
        batch_size = concurrent_users
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            response_times = await asyncio.gather(*batch)
            
            for rt in response_times:
                if rt < 0:
                    metrics.add_error()
                else:
                    metrics.add_success()
                    metrics.add_response_time(rt)

    metrics.stop()
    return metrics

@pytest.mark.performance
def test_api_performance():
    """API性能测试"""
    metrics = asyncio.run(load_test(
        TEST_CONFIG["base_url"],
        TEST_CONFIG["num_requests"],
        TEST_CONFIG["concurrent_users"]
    ))
    
    stats = metrics.get_statistics()
    
    # 性能指标断言
    assert stats["error_rate"] < TEST_CONFIG["max_error_rate"], f"Error rate too high: {stats['error_rate']}%"
    assert stats["avg_response_time"] < TEST_CONFIG["max_avg_response_time"], f"Average response time too high: {stats['avg_response_time']}s"
    assert stats["requests_per_second"] > TEST_CONFIG["min_requests_per_second"], f"Throughput too low: {stats['requests_per_second']} req/s"
    
    # 打印详细统计信息
    print("\nPerformance Test Results:")
    print(json.dumps(stats, indent=2))

@pytest.mark.performance
def test_long_running_performance():
    """长时间运行的性能测试"""
    async def run_test():
        start_time = time.time()
        metrics = PerformanceMetrics()
        metrics.start()
        
        async with aiohttp.ClientSession() as session:
            while time.time() - start_time < TEST_CONFIG["test_duration"]:
                response_time = await execute_workflow(
                    session,
                    TEST_CONFIG["base_url"],
                    {
                        "workflow": {"test": "long_running"},
                        "client_id": "long_test"
                    }
                )
                
                if response_time < 0:
                    metrics.add_error()
                else:
                    metrics.add_success()
                    metrics.add_response_time(response_time)
                
                await asyncio.sleep(1)  # 避免过度请求
        
        metrics.stop()
        return metrics
    
    metrics = asyncio.run(run_test())
    stats = metrics.get_statistics()
    
    # 打印长时间运行测试结果
    print("\nLong Running Test Results:")
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 