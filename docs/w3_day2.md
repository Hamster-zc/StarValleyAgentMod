# Week3 Day2：FAISS 向量索引构建与检索

## 目标
- 安装 FAISS 库（CPU 版本，适配 Linux 开发环境）
- 基于 Day1 生成的向量和元数据，构建 FAISS 索引
- 实现检索函数：给定查询文本，返回 Top-K 最相关的历史对话记录（ID + 文本 + 相似度分数）
- 编写测试脚本验证检索功能

---

## 一、安装 FAISS

### CPU 版本（推荐，兼容性好）
```bash
pip install faiss-cpu
```

### GPU 版本（可选，如果你有 NVIDIA GPU 且已安装 CUDA）
```bash
pip install faiss-gpu
```

> **注意**：在 Linux 开发机上，CPU 版本足够，且不需要额外驱动配置。

---

## 二、创建 `rag/faiss_index.py`

### 功能设计
- `build_index()`: 从 `storage/embeddings.npy` 和 `storage/metadata.json` 加载向量和元数据，构建 FAISS 索引。
- `load_index()`: 如果索引已存在，直接加载（避免重复构建）。
- `search(query_text, top_k=5)`: 接收查询文本，将其转为向量，在 FAISS 中检索，返回 Top-K 结果（包含 ID、文本、相似度分数）。

### 关键接口（自行实现）
```python
class FAISSIndex:
    def __init__(self, index_path: str = "storage/faiss.index", 
                 metadata_path: str = "storage/metadata.json"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.index = None
        self.metadata = None

    def build(self):
        """从 embeddings.npy 构建索引"""
        # 1. 加载向量 (np.load)
        # 2. 加载 metadata (json.load)
        # 3. 创建 FAISS 索引 (IndexFlatIP 或 IndexFlatL2)
        # 4. 添加向量到索引
        # 5. 保存索引到 index_path
        pass

    def load(self):
        """加载已保存的索引和元数据"""
        pass

    def search(self, query_text: str, top_k: int = 5):
        """检索最相似的 top_k 条记忆"""
        # 1. 调用 embedding_model.encode([query_text])
        # 2. 使用 index.search() 检索
        # 3. 根据返回的 ID 从 metadata 中查找对应文本
        # 4. 返回 List[Dict] 包含 id, text, score
        pass
```

---

## 三、FAISS 索引类型选择

- **`IndexFlatIP`**（内积相似度）：适用于余弦相似度（需要向量归一化）。
- **`IndexFlatL2`**（欧氏距离）：适用于 L2 距离。

推荐使用 `IndexFlatIP`，因为 Sentence-Transformers 的输出默认已经是单位向量（归一化），可以直接用内积作为相似度。

示例：
```python
import faiss
dimension = embeddings.shape[1]
index = faiss.IndexFlatIP(dimension)   # 内积相似度
index.add(embeddings)
```

---

## 四、测试脚本 `test_faiss.py`

在 `test/` 目录下创建 `test_faiss.py`，验证检索功能：

1. 构建索引（如果不存在）。
2. 输入一个测试查询（如“矿洞探险”）。
3. 调用 `search` 方法，打印 Top-3 结果及相似度分数。
4. 检查返回结果是否包含 `id`、`text`、`score` 字段。

---

## 五、集成到 Host（Day3 准备）

虽然今天是 Day2，但你可以提前思考如何将检索集成到 Host：

- 在 `host/server.py` 的 `client_handler` 中，在调用 `build_prompt_with_memory` 后，添加长期记忆检索：
  ```python
  long_term_memories = faiss_index.search(client_msg.context[-1]["content"], top_k=3)
  ```
- 将检索到的长期记忆也拼接到 prompt 中（与短期记忆区分或合并）。
- 在 `citations` 中加入长期记忆的 ID（可以用前缀区分，如 `"long_" + id`）。

Day2 先专注于索引构建和检索函数，Day3 再集成。

---

## 六、验收标准（Day2 结束时应满足）

- [ ] `faiss-cpu` 已安装，导入无报错。
- [ ] `rag/faiss_index.py` 实现 `build` 和 `search` 方法。
- [ ] 运行 `python test/test_faiss.py` 后，控制台输出 Top-3 检索结果，且相似度分数合理（0.5~1.0 之间）。
- [ ] 索引文件 `storage/faiss.index` 成功保存，且可重复加载。
- [ ] 检索速度 < 100ms（对于几千条数据，FAISS CPU 应远快于此）。

---

## 七、常见问题

- **向量维度不匹配**：确保 Embedding 模型输出维度与索引创建时一致（均为 384）。
- **索引未归一化**：如果使用 `IndexFlatIP`，需确保向量已归一化。`sentence-transformers` 默认输出已归一化，无需额外处理。
- **检索结果为空**：检查 metadata 中的 ID 是否与索引顺序对应（FAISS 返回的是索引位置，需映射回 ID）。

---

现在请按照此文档开始实现。如果遇到具体错误（如 FAISS 导入失败、维度错误等），请将错误信息贴出来，我会给出调试建议。