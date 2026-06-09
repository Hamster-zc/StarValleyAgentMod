import llama_cpp
from typing import List

class LLMWrapper:
    def __init__(self, model_path: str, max_tokens: int = 256, device: str = 'cuda', **kwargs):
        self.max_tokens = max_tokens
        if device == 'cuda':
            n_gpu_layers = 40   # 或 -1 表示全部层
        else:
            n_gpu_layers = 0
        self.llm = llama_cpp.Llama(
            model_path=model_path,
            n_ctx=2048,
            n_gpu_layers=n_gpu_layers,
            n_threads=4,
            **kwargs
        )
        
    def generate(self, prompt: str,max_tokens: int = None, temperature: float = 0.7,stop: List[str] = None) -> dict:
        if max_tokens is None:
            max_tokens = self.max_tokens
        response = self.llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop
        )
        return response
    
    def close(self):
        self.llm.close()

