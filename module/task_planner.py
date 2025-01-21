from module.generator import generate

# 태스크 플래너
# 사용자의 입력을 받으면, 사용자가 요청하는 Task가 무엇인지, 어떤 분야에 대한것인지 키워드 List를 출력하는 기능
def tasker(request: str):

    text = f"""
    input에 대해 Task와 Keywords를 추출해주세요.
    input = {request}
    """

    messages = [
        {
            "role": "system",
            "content": "You are a terms and conditions writing assistant. You must respond in Korean language. You must respond in the following JSON format:\n{\n  task : generate,review,answer,other 중 1개 , summary : 사용자 요청 요약, keywords : [질문의 핵심 키워드 목록] \n}",
            },
        {
            "role": "user", 
            "content": f"{text}"
            },
    ]

    # 답변 생성
    response = generate(messages, max_tokens=128)
    
    return response