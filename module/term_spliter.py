import pandas as pd
import re

def split_terms_into_list(terms_text):
    # 1️⃣ 모든 줄바꿈 기호 정리
    terms_text = terms_text.replace("\\n", " \n").replace("\\f", "").replace("\f", "").strip()
    terms_text = re.sub(r'\n[.\u2024\u2025\u2026]', ' \n ', terms_text)
    terms_text = terms_text.replace('\n', '').strip()

    # 2️⃣ 스페이스바 여러 번 있는 부분을 하나로 축소
    terms_text = re.sub(r'\s+', ' ', terms_text)

    # 3️⃣ "제 1조"가 등장하는 위치 찾기
    first_article_match = re.search(r"제\s*\d+\s*조", terms_text)
    first_article_index = first_article_match.start() if first_article_match else None

    # 4️⃣ "표준약관 제 ~호" 또는 "(YYYY.MM.DD. 제정)" 패턴 확인
    has_standard_clause = re.search(r"표준약관 제\s*\d+\s*호[^\s]*", terms_text)
    has_revision_date = re.search(r"\(\d{4}\.\d{1,2}(\.\d{1,2})?\.?\s*(제정|개정)\)", terms_text)  # '개정'도 포함

    # 5️⃣ "제 1조"가 나오기 전 부분까지만 확인 후 삭제
    if first_article_index is not None:
        before_first_article = terms_text[:first_article_index]
        after_first_article = terms_text[first_article_index:]  
        before_first_article = before_first_article.replace('"', "").strip()
        
        # "표준약관 제~호" 삭제
        before_first_article = re.sub(r"표준약관 제\s*\d+\s*호", "", before_first_article).strip()
        # "(YYYY.MM.DD. 제정|개정)" 삭제
        before_first_article = re.sub(r"\(\d{4}\s*\.\s*\d{1,2}\s*(\.\s*\d{1,2})?\s*\.?\s*(제정|개정)\)", "", before_first_article)

        # 수정된 문자열을 다시 합침
        terms_text = before_first_article + after_first_article
        
    else:
        # "제 1조"가 없으면 전체에서 삭제 가능
        terms_text = re.sub(r"표준약관 제\s*\d+\s*호[^\s]*", "", terms_text)
        terms_text = re.sub(r"\(\d{4}\.\d{1,2}(\.\d{1,2})?\.?\s*(개정|제정)\)", "", terms_text)

    # 6️⃣ "제 n 조" 형식이 처음 나오면 약관을 찾지 않음
    if re.match(r"^제\s*\d+\s*조", terms_text):
        first_clause = ""
        remaining_text = terms_text
    else:
        # 7️⃣ "표준약관 제~호"나 "(YYYY.MM.DD. 제정|개정)" 패턴이 없으면 "약관"을 찾지 않음
        if has_standard_clause or has_revision_date:
            match = re.search(r"(.+?약관)", terms_text)
            if match:
                first_clause = match.group(1).strip()  # "자동차(신차)매매약관"
                remaining_text = terms_text[match.end():].strip()  # 이후 텍스트
            else:
                first_clause = ""
                remaining_text = terms_text.strip()
        else:
            first_clause = ""
            remaining_text = terms_text.strip()

    # 8️⃣ "\n\n제 n 장 ~ \n\n" 형식 삭제
    remaining_text = re.sub(r"\s*제\s*\d+\s*장\s*.*?(?=제\s*\d+\s*조)", "", remaining_text, count=1).strip()

    # 9️⃣ "제 n 조" 나오기 전까지 한 덩어리로 저장
    pattern = r"(제\s*\d+\s*조\s*\(.*?\))"
    
    split_text = re.split(pattern, remaining_text)

    result = [first_clause] if first_clause else []  # 첫 번째 요소: 약관 이름
    pre_section = ""
    
    # "제 1조" 나오기 전까지의 문장 저장
    if split_text[0].strip():
        pre_section = split_text[0].strip()
        result.append(pre_section)

    # 이후 "제 n 조" 조항 저장
    sections = []
    for i in range(1, len(split_text)-1, 2):
        title = split_text[i].strip()
        content = split_text[i+1].strip()
        sections.append(f"{title} {content}")

    result.extend(sections)  # 리스트 순서 유지

    return result

def split_list(text):  # 조항별로 조항번호, 서브번호, 조항명, list로 나누기
    # 특수기호 리스트 (① ~ ㉕)
    special_symbols = ''.join([chr(9311 + i) for i in range(25)])  # ①(9312)부터 ㉕(9336)까지
    special_pattern = rf"(\s*[{special_symbols}])"  # 정규식 패턴 생성
    
    # 1.  2.  A.  b.  가.  나.  1)  2)  (1).  (2).  패턴을 저장
    number_pattern = re.compile(r"(?P<index>\b\d+\.\s*|\b[a-zA-Z]\.\s*|\b[가-힣]\.\s*|\b\d+\)\s*|\(\d+\)\s*|\(\d+\)\.\s*|\b\d+\)\.\s*)")
    # "제n장 (제목)" 패턴 (제n장 ~ 제거)
    chapter_pattern = re.compile(r"제\d+장\s+[^\n]+")

    # "제n조" 또는 "제n조의m" 패턴 (조항 찾기)
    article_pattern = re.compile(r"(제\s*\d+\s*조(?:의\d+)?\s*\((.*?)\))")

    result = []

    for item in text:
        # "제n장 (제목)" 제거
        if chapter_pattern.match(item):
            continue  # "제n장 제목"이면 건너뛰기

        # "제n조" 또는 "제n조의m" 찾기
        match = article_pattern.match(item)
        if match:
            article = match.group(1)  # "제4조의2(가계의부채)" 같은 전체 조항 제목
            content = item[len(match.group(0)):].strip()  # 나머지 본문
        else:
            article = None
            content = item.strip()

        # **특수기호 분리**
        parts = re.split(special_pattern, content)

        parsed = []

        for part in parts:
            part = part.strip()
            
            if not part:  
                continue  # 빈 문자열이면 스킵

            # 특수기호인지 확인
            if part in special_symbols:
                parsed.append(part)
            else:
                # 번호 패턴을 기준으로 텍스트 나누기
                sub_parts = re.split(number_pattern, part)
                
                sub_part_join = []  # sub_parts를 합칠 리스트
                
                for sub_part in sub_parts:
                    sub_part = sub_part.strip()
                    if sub_part:  # 빈 부분은 건너뛰기
                        # 번호 패턴이 아닌 경우 \n 추가
                        if not number_pattern.match(sub_part):
                            sub_part += "\n"
                        sub_part_join.append(sub_part)
                
                # 리스트에 결과를 합치기
                sub_join = ' '.join(sub_part_join)  # 빈 문자열로 join하여 합침
                parsed.append(sub_join)

        result.append([article] + parsed)
    
    return result

def text_classification(text):
    dic={}

    dic['조항번호']=[]
    dic['서브번호']=[]
    dic['조항명']=[]

    article_number=""

    for te in text:
        for te1 in te:
            # 텍스트가 None이 아닌지 확인
            if te1 is not None:
                # "제n조~)" 형태를 확인하는 정규식 패턴
                pattern = r"^제\s*\d+\s*조[^\n]*\)$"

                # 특수문자 또는 숫자 확인
                special_symbols = ''.join([chr(9311 + i) for i in range(25)])  # ① ~ ㉕ 특수문자
                has_special = any(char in special_symbols for char in te1)  # 특수문자 확인
                has_number = any(char.isdigit() for char in te1)  # 숫자 확인

                # 제n조~) 형식인지 확인
                if re.match(pattern, te1):
                    dic['조항번호'].append(te1)  # 숫자는 조항번호에 추가
                    article_number=te1

                elif has_special:
                    dic['서브번호'].append(te1)  # 특수문자는 서브항목에 추가
                else:
                    # "제n조~)" 형식이 아니면, 조항명에 추가
                    dic['조항명'].append(te1)

                    article_number_count=len(dic['조항번호'])
                    subsection=len(dic['서브번호']) 
                    article_title=len(dic['조항명'])
                    if(article_title>article_number_count):
                        for i in range(article_title-article_number_count):
                            dic['조항번호'].append(article_number)
                    if(article_title>subsection):
                        for i in range(article_title-subsection):
                            dic['서브번호'].append("")
    return dic

def Text_Pipline(text, file_name):
    terms_list=split_terms_into_list(text)
    split_text=split_list(terms_list)
    dic_list=text_classification(split_text)
    df = pd.DataFrame(dic_list)
    df['조약명']=file_name
    return df