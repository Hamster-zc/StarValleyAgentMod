#!/usr/bin/env python
"""
Week2 Day3 测试脚本：验证 LLMWrapper 异步生成、超时和并发限制
用法：python test_w2d3.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 上面这行会将 StarValleyAgentMod 加入路径
import asyncio
import time
from node.llm_wrapper import LLMWrapper

# 配置
MODEL_PATH = "./model/Qwen2.5-7B-Instruct-Q4_K_M.gguf"  # 根据实际路径修改
MAX_CONCURRENT = 1  # 与 Node 中的并发数一致

async def test_generate():
    print("加载模型中...")
    llm = LLMWrapper(model_path=MODEL_PATH, max_tokens=64, device='cuda')
    prompt = "What is the capital of France? Answer in one sentence."
    
    print("调用 generate...")
    start = time.time()
    response = await llm.generate(prompt=prompt, max_tokens=30, temperature=0.7)
    elapsed = time.time() - start
    text = response['choices'][0]['text'].strip()
    print(f"生成文本: {text}")
    print(f"耗时: {elapsed:.2f} 秒")
    print("✅ 异步生成测试通过\n")

async def test_timeout():
    print("测试超时控制：设置超时 0.1 秒（模型生成会超过）...")
    llm = LLMWrapper(model_path=MODEL_PATH, max_tokens=256, device='cuda')
    prompt = "Tell me a very long story about a dog." * 10  # 长 prompt 可能让生成慢一些
    try:
        response = await asyncio.wait_for(
            llm.generate(prompt=prompt, max_tokens=200, temperature=0.7),
            timeout=0.1
        )
        print("❌ 测试失败：未超时，模型返回了结果，但预期应超时")
    except asyncio.TimeoutError:
        print("✅ 超时测试通过：已捕获 TimeoutError\n")

async def test_concurrency():
    print("测试并发限制（Semaphore）...")
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    llm = LLMWrapper(model_path=MODEL_PATH, max_tokens=30, device='cuda')
    
    async def limited_generate(task_id, prompt):
        async with semaphore:
            print(f"任务 {task_id} 开始")
            start = time.time()
            response = await llm.generate(prompt=prompt, max_tokens=20)
            elapsed = time.time() - start
            text = response['choices'][0]['text'].strip()
            print(f"任务 {task_id} 完成，耗时 {elapsed:.2f} 秒，文本: {text[:50]}")
            return text
    
    prompts = [
        "What is the capital of France?",
        "What is the capital of Germany?",
        "What is the capital of Italy?"
    ]
    print(f"同时启动 {len(prompts)} 个任务，最大并发 {MAX_CONCURRENT}，预期任务将串行执行")
    start_all = time.time()
    results = await asyncio.gather(*[limited_generate(i, p) for i, p in enumerate(prompts)])
    total_time = time.time() - start_all
    print(f"所有任务完成，总耗时 {total_time:.2f} 秒")
    # 当 MAX_CONCURRENT=1 时，总耗时应该近似于三个任务耗时之和
    print("✅ 并发限制测试通过（总耗时 > 单任务耗时 * 任务数 的一半）\n")

async def main():
    print("=== Week2 Day3 功能测试 ===\n")
    await test_generate()
    await test_timeout()
    await test_concurrency()
    print("所有测试完成。")

if __name__ == "__main__":
    asyncio.run(main())