from module.generator import generate

# 채팅
def chat(request: str, context_list: list):
    
    # 최대 context 초과시 최근 20개만 남김
    max_context = 20
    if len(context_list) > max_context:
        context_list = context_list[-max_context:] 

    # TODO: 키워드 추출해 참고자료 DB조회해서 질문에 추가
    
    text = f"""
    1. input = {request}
    2. context = {context_list}
    """

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

    # 답변 생성
    response = generate(messages)

    # context 업데이트
    new_context = {"request": response["request"], "summary": response["summary"]}
    context_list.append(new_context)
    answer = response["answer"]

    return {"answer": answer, "context": context_list}

