# Week2 Day3：异步 LLM 调用 + 超时控制 + 并发限制

## 目标
- 将 `LLMWrapper.generate` 改造为异步方法，底层调用 `llama-cpp-python` 的同步推理放到线程池中执行，避免阻塞事件循环。
- 在 `agent_node.py` 的任务处理函数中，对模型生成操作设置超时（`asyncio.wait_for`），超时后返回失败结果。
- 为 Node 添加并发限制（`asyncio.Semaphore`），控制同时处理的任务数量，防止显存溢出。

---

## 一、修改 `node/llm_wrapper.py`

### 1.1 添加导入
在文件顶部增加：
```python
import asyncio
from functools import partial
```

### 1.2 修改 `generate` 方法
需要将其变为 `async def`，并在内部使用 `loop.run_in_executor` 来执行同步的 `self.llm(...)`。

**函数签名**（不变）：
```python
async def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.7, stop: List[str] = None) -> dict:
```

**实现步骤**：
- 获取当前事件循环：`loop = asyncio.get_running_loop()`
- 确定要使用的 `max_tokens`：如果参数为 `None`，使用 `self.max_tokens`
- 使用 `loop.run_in_executor` 执行 `self.llm` 调用。因为 `self.llm(...)` 需要多个参数，建议用 `functools.partial` 或 `lambda` 包装。
- 等待执行结果并返回。

**关键点**：
- `run_in_executor` 的第一个参数 `None` 表示使用默认的线程池。
- 确保 `self.llm` 的调用不会因为并发产生线程安全问题（`llama-cpp-python` 的 `Llama` 实例通常是线程安全的，可以多线程调用，但注意显存限制，所以后面我们还要加 Semaphore）。

**示例骨架**：
```python
async def generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.7, stop: List[str] = None) -> dict:
    loop = asyncio.get_running_loop()
    _max_tokens = max_tokens if max_tokens is not None else self.max_tokens
    # 使用 partial 固定参数，避免 lambda 捕获问题
    func = partial(
        self.llm,
        prompt=prompt,
        max_tokens=_max_tokens,
        temperature=temperature,
        stop=stop
    )
    result = await loop.run_in_executor(None, func)
    return result
```

### 1.3 （可选）添加 `close` 方法
如果你之前有 `close` 方法且里面调用了 `self.llm.close()`，注意 `llama-cpp-python` 的 `Llama` 对象并没有 `close` 方法，可以删除或留空。

---

## 二、修改 `node/agent_node.py`

### 2.1 添加并发限制
在 `main()` 函数中，连接建立后，注册完成前，创建一个 `asyncio.Semaphore` 对象，并作为全局变量或在函数间传递。

**建议**：在 `main()` 中定义 `semaphore = asyncio.Semaphore(MAX_CONCURRENT)`，然后在接收循环中使用 `async with semaphore:` 包围任务处理逻辑。

`MAX_CONCURRENT` 的值可以根据你的显存来定，对于 7B Q4_K_M 模型，推荐设为 `1` 或 `2`（保守点先设 1）。

### 2.2 提取任务处理协程
建议将处理单个 `TaskAssignment` 的逻辑提取为一个异步函数，例如 `async def process_task(websocket, task: TaskAssignment, llm: LLMWrapper)`，这样可以清晰地放置超时和并发控制。

### 2.3 在 `process_task` 中实现超时控制
使用 `asyncio.wait_for()` 包裹 `llm.generate(...)`，超时时间从 `task.max_latency_ms` 获得（注意单位换算：秒 = 毫秒 / 1000）。

**伪代码**：
```python
async def process_task(websocket, task: TaskAssignment, llm: LLMWrapper):
    try:
        response = await asyncio.wait_for(
            llm.generate(
                prompt=task.prompt,
                max_tokens=task.max_tokens,
                temperature=task.temperature
            ),
            timeout=task.max_latency_ms / 1000.0
        )
        # 从 response 中提取生成的文本
        generated_text = response['choices'][0]['text'].strip()
        # 构造成功结果
        result = NodeResult(
            task_id=task.task_id,
            node_id=NODE_ID,
            request_id=task.request_id,
            status="success",
            result=generated_text,
            latency_ms=int((time.time() - start_time) * 1000)  # 记录实际耗时
        )
    except asyncio.TimeoutError:
        # 构造超时失败结果
        result = NodeResult(
            task_id=task.task_id,
            node_id=NODE_ID,
            request_id=task.request_id,
            status="failure",
            result="",
            error_msg="LLM generation timeout",
            latency_ms=task.max_latency_ms
        )
    except Exception as e:
        # 其他异常也处理为失败
        result = NodeResult(
            task_id=task.task_id,
            node_id=NODE_ID,
            request_id=task.request_id,
            status="failure",
            result="",
            error_msg=str(e),
            latency_ms=0
        )
    # 发送结果
    await websocket.send(result.model_dump_json())
```

### 2.4 修改接收循环
在原来的 `async for raw_message in websocket:` 循环内部，当接收到 `task_assignment` 后，用 `async with semaphore:` 调用 `process_task`。

**注意**：不要在 `async with semaphore` 内部再等待 `websocket.recv()`，只需将处理任务的部分包裹起来即可。

**伪代码**：
```python
async for raw_message in websocket:
    data = json.loads(raw_message)
    if data["type"] == "task_assignment":
        task = TaskAssignment.model_validate(data)
        async with semaphore:
            await process_task(websocket, task, llm)
```

---

## 三、测试与验证

### 3.1 环境准备
- 确保 Host 和 ClientSimulator 已经支持之前的流程。
- Node 能够正常加载模型。

### 3.2 测试并发限制
- 设置 `MAX_CONCURRENT = 1`。
- 同时从 Client 发送两个请求（例如连续快速发送）。
- 观察 Node 日志：第一个任务开始后，第二个任务应该等到第一个任务完成才进入 `process_task`（因为信号量限制）。

### 3.3 测试超时
- 临时修改 `llm.generate`，在 `run_in_executor` 之前增加 `await asyncio.sleep(100)` 强制超时（仅测试用，记得恢复）。
- 或者将 `max_latency_ms` 设为一个很小的值（如 100 毫秒），模型生成肯定超过。
- 观察 Node 是否捕获 `TimeoutError`，返回 `status="failure"`。
- Host 端应收到失败结果并转发给 Client，Client 显示错误信息。

### 3.4 正常调用
- 移除强制超时代码，恢复正常的 `max_latency_ms`（例如 25000）。
- 发送一个请求，确认能正常返回文本。

---

## 四、验收标准

- [ ] `llm_wrapper.generate` 是异步函数，内部使用 `run_in_executor`。
- [ ] `agent_node.py` 中任务处理使用了 `asyncio.wait_for` 并正确处理超时异常。
- [ ] `agent_node.py` 中使用了 `asyncio.Semaphore` 限制了并发数，且并发数可通过常量配置。
- [ ] 测试场景：
  - 正常生成：得到正确回复。
  - 超时场景：Node 返回 `failure`，Host 转发错误。
  - 并发场景：同时到达两个任务，第二个任务等待第一个完成（日志可见）。
- [ ] 无事件循环阻塞警告（`run_in_executor` 正确使用）。

---

## 五、注意事项

- **超时后线程仍在运行**：`asyncio.wait_for` 超时后只是取消等待，并不真正停止线程池中的任务。该任务会继续运行直到结束，但结果会被丢弃。对于显存限制，这可能会导致短暂的额外占用，但通常可以接受。如需严格中断，需要更复杂的设计（如进程隔离），Day3 不要求。
- **Semaphore 的作用范围**：确保所有任务共享同一个信号量实例，不要在每次循环中新建。
- **错误处理**：除了超时，还要捕获其他异常（如模型加载失败、显存溢出等），避免 Node 崩溃。
- **日志**：在超时和异常发生时打印日志，便于调试。