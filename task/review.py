from module.generator import generate


def review (input : str, data_list : list):
    # 조회한 자료들을 참고로 해당 부분 검토
    text = f"""
    1. input = {input}
    2. context = {data_list}
    """

    messages = [
        {
            "role": "system",
            "content": "You are a terms and conditions legal reviewer. You must respond in Korean language. You must respond in the following JSON format:\n{\n  review : context를 참고한 해당 input의 검토 결과 최대 100글자 , grade : 해당 input에 대한 등급 A,B,C 중 1개 \n}, If there are no special circumstances, assign the grade as B.",
            },
        {
            "role": "user", 
            "content": f"{text}"
            },
    ]

    # 답변 생성
    response = generate(messages)

    return response