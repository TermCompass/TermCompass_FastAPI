# LLM모델의 generate를 분리한 모듈
# generate 파라미터 등을 일원화 관리하기 위해 모듈화
import json
from module.global_var import model, tokenizer
from module.brace_checker import check_braces

def generate(messages : str, max_tokens : int = 512): # 최대 토큰 수 512에서 조절 가능
    input_ids = tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", padding=True
    ).to(model.device)

    outputs = model.generate(
        input_ids,
        max_new_tokens=max_tokens,
        eos_token_id=tokenizer.eos_token_id,
        do_sample=False,
        temperature=None,
        top_p=None,
        attention_mask=(input_ids != tokenizer.pad_token_id).long(),
    )

    response = tokenizer.decode(
        outputs[0][input_ids.shape[-1] :], skip_special_tokens=True
    )

    print("response 시작 ====================================================")
    print(response)
    print("response 끝 ====================================================")

    parsed = json.loads(check_braces(response))
    
    return parsed