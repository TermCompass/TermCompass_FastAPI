# LLM의 출력 문자열이 중괄호(JSON)로 묶여있는지 확인하는 함수
# 사용범위가 넓어 모듈로 분리함
# 추후 상황에 따라 generator.py와 병합
import json

def check_braces(string : str):
    """
    문자열이 JSON 형식으로 제대로 감싸져 있는지 확인하고 수정합니다.
    """
    # 문자열이 이미 JSON 형식인지 확인
    try:
        json.loads(string)
        return string  # 유효한 JSON이면 바로 반환
    except json.JSONDecodeError:
        pass

    # JSON 문자열 양 끝 중괄호 보정
    string = string.strip()
    if not string.startswith("{"):
        string = "{" + string
    if not string.endswith("}"):
        string += "}"

    # 리스트 닫기 보정
    if string.count('[') > string.count(']'):
        string += ']' * (string.count('[') - string.count(']'))
    elif string.count('{') > string.count('}'):
        string += '}' * (string.count('{') - string.count('}'))

    # 문자열 따옴표 개수 보정
    if string.count('"') % 2 != 0:
        string += '"'

    # 중괄호 사이 콤마 삽입 예외 처리
    string = string.replace('}{', '},{')

    # JSON 파싱 재시도
    try:
        json.loads(string)
        return string
    except json.JSONDecodeError as e:
        print(f"최종 JSON 오류 발생: {e}")
        return None
