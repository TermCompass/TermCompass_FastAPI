import json
from module import global_var as gv

# 채팅
def chat(request: str, context_list: list):

    max_context = 20
    if len(context_list) > max_context:
        context_list = context_list[
            -max_context:
        ]  # 최대 context 초과시 최근 20개만 남김

    # TODO: 키워드 추출해 참고자료 DB조회해서 질문에 추가

    text = f"""
    1. input = {request}
    2. context = {context_list}
    """

    # 입력
    # text = f"""{{ "input" : {request} , "context" : {context_list} }}"""
    gv.tokenizer.pad_token = gv.tokenizer.eos_token

    messages = [
        {
            "role": "system",
            "content": "You are a terms and conditions writing assistant. You must respond in Korean language. You must respond in the following JSON format:\n{\n  request : 질문 요약 100자 미만 , answer : 답변 , summary : 답변 요약 100자 미만 \n}",
            },
        {
            "role": "user", 
            "content": f"{text}"
            },
    ]
    input_ids = gv.tokenizer.apply_chat_template(
        messages, add_generation_prompt=True, return_tensors="pt", padding=True
    ).to(gv.model.device)

    outputs = gv.model.generate(
        input_ids,
        max_new_tokens=512,
        eos_token_id=gv.tokenizer.eos_token_id,
        do_sample=False,
        temperature=None,
        top_p=None,
        attention_mask=(input_ids != gv.tokenizer.pad_token_id).long(),
    )

    response = gv.tokenizer.decode(
        outputs[0][input_ids.shape[-1] :], skip_special_tokens=True
    )
    print("response 시작 ====================================================")
    print(response)
    print("response 끝 ====================================================")
    parsed = json.loads(check_braces(response))

    # context 업데이트
    new_context = {"request": parsed["request"], "summary": parsed["summary"]}
    context_list.append(new_context)
    answer = parsed["answer"]

    return {"answer": answer, "context": context_list}


def check_braces(string):
    # 시작 글자가 "{"이 아니면 추가
    if not string.startswith("{"):
        string = "{" + string

    # 끝 글자가 "}"이 아니면 추가
    if not string.endswith("}"):
        string = string + "}"

    return string
