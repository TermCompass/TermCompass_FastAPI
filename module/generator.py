# LLM모델의 generate를 분리한 모듈
# generate 파라미터 등을 일원화 관리하기 위해 모듈화
import json
import re

from openai import OpenAI

from module.global_var import model, tokenizer
from module.brace_checker import check_braces

#파일의 apikey불러오기
openai_api_key_path = "./admin/api_key/openai_api_key.txt"
with open(openai_api_key_path, "r") as f:
    openai_api_key = f.read()

client = OpenAI(
        api_key=openai_api_key,
    )

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
    if not response.endswith("}"):
        response += "}"

    try:
        parsed = json.loads(response)
        return parsed
    except:
        # 1단계: 모든 큰따옴표를 작은따옴표로 변경
        data = response.replace('"', "'")

        # 2단계: {' 를 {" 로, ':' 를 ": " 로, ',' 를 ", " 로, '} 를 } 으로 변경
        data = re.sub(r"{\s*'", '{"', data)
        data = re.sub(r"'\s*:\s*'", '": "', data)
        data = re.sub(r"'\s*:", '":', data)
        data = re.sub(r"'\s*,\s*'", '","', data)
        data = re.sub(r"'\s*}", '"}', data)  
        data = re.sub(r"[\s*'", '["', data)
        data = re.sub(r"'\s*]", '"]', data)  

        # print("escaped_data 시작 ====================================================")
        # print(data)
        # print("escaped_data 끝 ====================================================")
        parsed = json.loads(data)

        # print("parsed 시작 ====================================================")
        # print(parsed)
        # print("parsed 끝 ====================================================")

        return parsed

def generate2(input: str, model: str = "gpt-4o") -> dict:
    """
    OpenAI API 호출 후 JSON 응답 파싱 함수

    Args:
    - input (str): OpenAI API에 전달할 프롬프트
    - model (str, optional): 사용할 OpenAI 모델 이름 (기본값: "gpt-3.5-turbo")

    Returns:
    - dict: JSON 응답 데이터를 파싱한 딕셔너리
    """
    try:
        response = client.chat.completions.create(
        model=model,
        temperature=0,
        messages=input
        )

        # print("response 시작 ====================================================")
        # print(response)
        # print("response 끝 ====================================================")        

        content = response.choices[0].message.content

        print("content 시작 ====================================================")
        print(content)
        print("content 끝 ====================================================")        

        # 코드 블록 제거
        clean_content = content.strip('```json').strip('```').strip()
        # OpenAI 응답을 JSON 문자열로 변환 후 로드
        response_json = json.loads(clean_content)
        return response_json
    except Exception as e:
        return {"error": str(e)}