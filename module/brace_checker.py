# LLM의 출력 문자열이 중괄호(JSON)로 묶여있는지 확인하는 함수
# 사용범위가 넓어 모듈로 분리함
# 추후 상황에 따라 generator.py와 병합

def check_braces(string):
    # 시작 글자가 "{"이 아니면 추가
    if not string.startswith("{"):
        string = "{" + string

    # 끝 글자가 "}"이 아니면 추가
    if not string.endswith("}"):
        string = string + "}"

    return string