import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from node.llm_wrapper import LLMWrapper

def test_llm_wrapper(model_path):
    llm = LLMWrapper(model_path=model_path, max_tokens=128, device='cuda')
    prompt = "What is the capital of France?"
    response = llm.generate(prompt)
    print("Response:", response)
    assert 'choices' in response
    assert len(response['choices']) > 0
    assert 'text' in response['choices'][0]
    llm.close()

if __name__ == "__main__":
    test_llm_wrapper(r"model\Qwen2.5-7B-Instruct-Q4_K_M.gguf")
