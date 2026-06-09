from node.llm_wrapper import LLMWrapper

def test_llm_wrapper(model_path):
    llm = LLMWrapper(model_path=model_path, max_tokens=128, device='cpu')
    prompt = "What is the capital of France?"
    response = llm.generate(prompt)
    print("Response:", response)
    assert 'choices' in response
    assert len(response['choices']) > 0
    assert 'text' in response['choices'][0]
    llm.close()
