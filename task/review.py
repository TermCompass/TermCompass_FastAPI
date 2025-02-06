from module.generator import generate, generate2


def review (input : str, data_list : list):
    # 조회한 자료들을 참고로 해당 부분 검토
    input = input.replace('"', "'")
    input = input.replace('“', "'")
    input = input.replace('”', "'")
    print(input)
    text = f"""
    1. input = {input}
    2. context = {data_list}
    """

    messages = [
        {
            "role": "system",
            "content": 
            """
            You are a terms and conditions legal reviewer. 
            You must respond in Korean language. 
            You must respond in the following JSON format:\n{ \"grade\" : \"해당 input에 대한 등급 A,B,C 중 1개\" , \"review\" : \"해당 input의 검토 결과 최대 200글자\" \n}. 
            If the clause is favorable to the customer, grade A. 
            If there are no special circumstances, grade B. 
            If the customer is at a disadvantage, grade C.
            """,
            },
        {
            "role": "user", 
            "content": f"{text}"
            },
    ]

    # 답변 생성
    response = generate2(messages)

    # grade = response["review"][:1]
    # review = response["review"][1:]

    # newResponse = {"grade":grade,"review":review}

    return response