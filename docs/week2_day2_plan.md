# Week2 Day2：llama-cpp-python 环境配置与 LLM 封装（基础版）

## 目标
- 在本地环境中安装 `llama-cpp-python`
- 下载一个可用的 GGUF 量化模型（例如 `tinyllama-1.1b.Q4_K_M.gguf` 或 `Llama-2-7b-chat.Q4_K_M.gguf`，根据显存选择）
- 编写 `node/llm_wrapper.py`，实现一个 `LLMWrapper` 类，能够**同步**调用模型生成文本
- 编写一个独立的测试脚本 `test_llm.py`，验证模型能正常输出

**注意**：Day2 只要求同步调用（不涉及异步、超时、并发），Day3 再改造为异步。

---

## 一、环境准备

### 1. 安装 llama-cpp-python
```bash
pip install llama-cpp-python
```
如果遇到编译问题（缺少 `cmake` 或 `cuda`），请查阅 [llama-cpp-python 官方文档](https://llama-cpp-python.readthedocs.io/) 安装预编译的轮子。

### 2. 下载模型
选择一个适合你硬件的 GGUF 模型。推荐：
- 显存 ≤ 8GB：`TinyLlama-1.1B-Chat-v1.0.Q4_K_M.gguf`（约 0.7GB）
- 显存 8GB+：`Llama-2-7b-chat.Q4_K_M.gguf`（约 4GB）

下载至项目下的 `models/` 目录：
```bash
mkdir -p models
cd models
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf
```

（也可用其他镜像源）

---

## 二、编写 `node/llm_wrapper.py`

你需要实现一个类 `LLMWrapper`，包含以下方法：

### `__init__(self, model_path: str, max_tokens: int = 256, device: str = "cuda", **kwargs)`
- 初始化 `llama-cpp-python` 的 `Llama` 实例。
- 关键参数：
  - `model_path`：模型文件路径
  - `n_ctx`：上下文长度（建议 2048，可根据模型调整）
  - `n_gpu_layers`：如果使用 GPU，设置为 40~50；若 CPU，设为 0
  - `n_threads`：CPU 线程数（可选）
- 将模型实例保存为 `self.llm`。

### `generate(self, prompt: str, max_tokens: int = None, temperature: float = 0.7, stop: List[str] = None) -> dict`
- 同步调用 `self.llm.create_completion()`（或 `self.llm()`）。
- 参数：
  - `prompt`：输入字符串
  - `max_tokens`：最大生成长度（若为 None，使用实例的默认值）
  - `temperature`：温度参数
  - `stop`：停止词列表（例如 `["\n"]` 或 `["User:"]`）
- 返回值：字典，至少包含 `text`（生成的文本）和 `tokens_used`（可选）。
- 建议捕获异常，返回包含 `error` 的字典。

### `close(self)`
- 释放模型资源（可选，`llama-cpp-python` 的 Python 对象通常会自动清理）。

---

## 三、编写测试脚本 `test_llm.py`

在项目根目录创建 `test_llm.py`，内容：

1. 导入 `LLMWrapper`
2. 定义模型路径（例如 `models/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`）
3. 创建 `LLMWrapper` 实例
4. 调用 `generate`，传入简单 prompt，例如 `"Say hello world."`
5. 打印生成的文本
6. 调用 `close`（可选）

运行测试：
```bash
python test_llm.py
```

**预期输出**：模型生成的一段文本（可能不完美，但不应报错）。

---

## 四、验收标准

- [ ] `pip list | grep llama-cpp-python` 显示已安装。
- [ ] 模型文件存在于指定路径，能够加载（无 `FileNotFoundError` 或 `Segmentation fault`）。
- [ ] `test_llm.py` 运行后，终端打印出模型生成的文本（即使只是几个词）。
- [ ] 模型加载和生成过程没有明显异常（如显存溢出导致崩溃）。

---

## 五、注意事项与常见坑

1. **显存不足**：如果加载大模型时程序崩溃，改用更小的模型或设置 `n_gpu_layers=0` 使用 CPU。
2. **模型路径错误**：使用绝对路径或相对路径（相对于运行脚本的工作目录），建议在代码中用 `os.path.abspath()` 转换。
3. **第一次加载较慢**：模型需要加载到内存/显存，耐心等待。
4. **`llama-cpp-python` 版本兼容**：如果安装失败，尝试：
   ```bash
   CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python
   ```
   （CUDA 支持）
5. **输出乱码或重复**：调整 `temperature` 和 `top_p` 参数，或更换模型