import pandas as pd
import re

def split_articles(text):  # 조항별로 편집집
    # '제X조' 뒤에 공백이나 줄바꿈이 올 수 있음을 고려한 정규식 패턴
    pattern = r'(^제\d+조(?:\s|\n)?)'  # 조항이 문장의 시작(줄의 시작)에 있는 경우만 매칭
    parts = re.split(pattern, text, flags=re.MULTILINE)  # MULTILINE 모드 사용

    terms_list = []
    
    if parts[0].strip():  # 첫 번째 항목이 비어 있지 않으면
        terms_list.append(parts[0].strip())

    current_article_number = 1  # 조항 번호 시작

    for i in range(1, len(parts), 2):  # 짝수 번째 인덱스에 조항 제목이 있음
        title = parts[i].strip()
        content = parts[i + 1].strip() if i + 1 < len(parts) else ""

        match = re.match(r'제(\d+)조', title)
        if match:
            article_number = int(match.group(1))

            if article_number != current_article_number:
                article_number = current_article_number

            title = title.replace(f"제{article_number}조", f"제{current_article_number}조")
            current_article_number += 1

        terms_list.append(f"{title} {content}")
    return terms_list

def split_list(text): #조항별로 조항번호, 서브번호,조항명,list로 나누기
    # 특수기호 리스트 (① ~ ㉕)
    special_symbols = ''.join([chr(9311 + i) for i in range(25)])  # ①(9312)부터 ㉕(9336)까지
    special_pattern = rf"(\s*[{special_symbols}])"  # 정규식 패턴 생성

    # "제n장 (제목)" 패턴 (제n장 ~ 제거)
    chapter_pattern = re.compile(r"제\d+장\s+[^\n]+")

    # "제n조" 또는 "제n조의m" 패턴 (조항 찾기)
    article_pattern = re.compile(r"(제\d+조(?:의\d+)?\s*\((.*?)\))")

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

        # **줄바꿈을 공백으로 변환 후 특수기호 분리**
        content = content.replace("\n", " ")  # **\n을 공백으로 변환**
        parts = re.split(special_pattern, content)

        parsed = []
        
        for part in parts:
            clean_part = part.replace("\n", " ").strip()  # **줄바꿈 제거 + 앞뒤 공백 제거**
            if clean_part:
                parsed.append(clean_part)  # 공백이 아닌 경우 리스트에 추가

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
                pattern = r"^제\d+조[^\n]*\)$"

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

# ============================= !!!!!!!파이프라인!!!! ======================================================
def Text_Pipline(text, file_name):
    terms_list=split_articles(text)
    split_text=split_list(terms_list)
    dic_list=text_classification(split_text)
    df = pd.DataFrame(dic_list)
    df['조약명']=file_name
    return df

text = "예식장이용 표준약관 \n\n표준약관 제 10030 호\n(2014. 9. 19. 개정)\n\n제 1 조(목적)  이   약관은   예식장을   운영하는   사업자(이하   ‘사업자’라   합니다)와 \n\n예식장을 이용하는 예식당사자등(이하 ‘이용자’라 합니다)  간의 예식장의 이용에 \n\n관한 제반 계약사항을 규정함을 목적으로 합니다.\n\n제 2 조(약관의 명시 설명 및 계약서의 교부\n\n․\n\n)\n\n    ①   사업자는   계약을   체결하는   장소인   사무실내의   보기   쉬운   곳에   이   약관과 \n\n이용요금(내역별 금액)을 게시하고,  계약을 체결하기 전에 이 약관의 내용을 \n\n설명합니다.\n\n    ②   사업자는   계약을   체결하는   때에   다음   각   호의   사항을   기재한   계약서  2 통을 \n\n마련하여   사업자와   이용자의   기명날인   또는   서명을   받은   후에  1 통을 \n\n이용자에게 교부합니다.\n\n    1. 사업자의 상호, 주소 및 전화번호, 담당자의 이름\n\n    2. 이용일시 및 이용시간\n\n    3. 이용호실\n\n \n\f       4.  예식비용(예식장,  부대시설,  부대서비스,  부대물품 등 내역별로 이용요금을 \n\n기재함)\n\n    5. 계약금\n\n    6. 기타 예식에 관하여 필요한 사항\n\n  ③   사업자는   계약을   체결하는   때에   이용자의   요구가   있으면   이   약관을 \n\n교부합니다.  다만,  이용자에게   교부하는   계약서에   이   약관이   기재되어   있는 \n\n경우에는 그러하지 아니합니다.\n\n제 3 조(계약금과 예식비용의 지급)\n\n   ① 계약금은 예식비용의 10% 이하로 하며, 이용자는 계약을 체결하는 때에 이를 \n\n지급하여야 합니다.\n\n   ② 이용자는 예식이 모두 종료되는 즉시 예식비용의 잔금을 지급하여야 합니다 . \n\n다만, 사업자가 제 7 조의 규정에 의한 손해배상액을 지급하여야 할 경우에는 \n\n이용자는 그 금액을 공제하여 지급할 수 있습니다.\n\n제 4 조(사업자의 의무)\n\n  ① 사업자는 이용자가 예식을 진행하는 데 불편함이 없도록 예식장 및 부대시설을 \n\n쾌적하게   유지하고,\n\n 계약에서   정한   부대서비스   및   부대물품을   사전에 \n\n성실하게 준비합니다.\n\n  ② 사업자 및 종업원은 이용자에게 계약에서 정한 예식비용 이외의 일체의 금품을 \n\n요구하지 않습니다.\n\n  ③   사업자는   이용자에게   예식장을   이용하게   함에   있어서   식당 ,  신랑정장, \n\n신부드레스,  신부화장,  사진 비디오촬영 등 부대시설 서비스 물품의 이용을\n\n․\n\n․\n\n․\n\n \n \n \n\f조건으로 할 수 없습니다.\n\n제 5 조  (이용자의   의무)  이용자는   사업자의   시설관리   및   질서유지에   관한 \n\n운영규정을 준수하고, 예식의 원활한 진행을 위하여 협력하여야 합니다.\n\n제 6 조 (계약의 해제)\n\n    ①   사업자   또는   이용자는   계약에서   정한   예식일   전까지   상대방에게   통지하여 \n\n계약을 해제할 수 있습니다.\n\n ②   사업자가   자신의   책임있는   사유로   계약을   해제한   경우,  그   손해배상은 \n\n소비자분쟁해결기준(공정거래위원회   고시)에   따릅니다.\n\n 다만,\n\n 사업자가 \n\n계약에서 정한 동일한 내용 및 조건으로 다른 호실에서 예식이 진행될 수 있게 \n\n한 경우에는 손해배상액을 지급하지 않을 수 있습니다.\n\n     ③  이용자가   자신의   책임있는   사유로   계약을   해제한   경우,  그   손해배상은 \n\n소비자분쟁해결기준(공정거래위원회 고시)에 따릅니다.\n\n제 7 조(부대서비스 물품에   대한   손해배상\n\n․\n\n)  사업자는   이용자가   계약에서   정한 \n\n부대서비스   또는   부대물품을   사업자의   고의 과실로   이용하지   못한   경우에는\n\n․\n\n, \n\n당해   부대서비스   또는   부대물품의   이용요금의   배액을   손해배상액으로 \n\n이용자에게 지급합니다.\n\n제 8 조(기념사진에 대한 손해배상)\n\n    ①   사업자에게   촬영을   의뢰한   기념사진이   사업자의   고의 과실로   멸실 훼손된\n\n․\n\n․\n\n경우에는   사업자는   이용자에게   제 2 항   내지   제 4 항의   규정에   따라 \n\n손해배상을 합니다.\n\n \n \n\f    ②   이용자가   주요   사진(이하   주례   사진,  신랑 신부   양인   사진\n\n․\n\n,  신부   독사진, \n\n양가부모   사진,  가족   사진,  친구   사진을   말합니다)의   전부   또는   일부의 \n\n재촬영을   원하는   경우에는   사업자는   자신의   비용   부담으로   재촬영을   하되 \n\n전부를   촬영한   경우에는   이에   추가하여   촬영요금(이하   계약에서   정한 \n\n촬영요금을 말합니다)을 이용자에게 지급하고,  주요 사진의 일부만을 촬영한 \n\n경우에는 촬영요금의 배액을 지급합니다.\n\n   ③ 이용자가 주요사진의 재촬영을 원하지 않는 경우에는 사업자는 촬영요금의  3\n\n배액을 이용자에게 지급합니다.\n\n   ④ 사업자가 제 2 항의 규정에 의하여 부담하는 재촬영요금 및 지급액 또는 제 3\n\n항의 규정에 의하여 부담하는 지급액은 예식비용을 한도로 합니다.\n\n제 9 조  (부대시설   사업자의   고의 과실에   대한   사업자의   책임\n\n․\n\n)  사업자와   부대시설 \n\n사업자가 다른 경우에도,  이용자는 부대시설 사업자의 고의 과실로 인한 손해의\n\n․\n\n배상을 이 약관에 따라 사업자에게 청구할 수 있습니다. 다만, 사업자가 부대시설 \n\n사업자를 소개 추천하면서 그 부대시설 사업자의 고의 과실에 대해서는 자신이\n\n․\n\n․\n\n책임을 지지 않는다는 뜻을 미리 분명히 하거나,  이용자가 독자적으로 부대시설 \n\n이용계약을 체결한 경우에는 그러하지 아니합니다. \n\n제 10 조(사고로 인한 책임)  사업자는 예식장 및 부대시설의 하자,  종업원의 고의․\n\n과실   등   사업자의   책임있는   사유로   예식장   및   부대시설   내에서   사고가   발생한 \n\n경우에는, 그 사고로 이용자 및 하객이 입은 손해를 배상할 책임을 집니다.\n\n제 11 조(휴대물에 대한 책임)\n\n  ① 사업자는 이용자 또는 하객이 휴대한 물건(이하 ‘물건’이라 합니다)을 사업자나 \n\n종업원에게   보관을   맡긴   경우에는,  그   물건의   멸실 훼손 도난   등에   대하여\n\n․\n\n․\n\n \n \n \n\f불가항력으로   인한   것임을   증명하지   아니하면   그   손해를   배상할   책임을 \n\n면하지 못합니다.\n\n    ②   사업자는   이용자   또는   하객이   보관을   맡기지   아니한   물건이라도   사업자나 \n\n종업원의   고의 과실로   인하여   멸실 훼손 도난   등이   된   때에는   그   손해를\n\n․\n\n․\n\n․\n\n배상할 책임을 집니다.\n\n  ③ 사업자는 이용자 또는 하객의 물건에 대하여 책임이 없음을 게시한 때에도 제 1\n\n항과 제 2 항에 의한 책임을 면하지 못합니다.\n\n  ④ 화폐, 유가증권 등의 고가물에 대하여는 이용자 또는 하객이 그 종류와 가액을 \n\n명시하여 사업자나 종업원에게 보관을 맡기지 아니한 경우에는,  사업자는 그 \n\n멸실 훼손 도단 등에 대하여 손해를 배상할 책임을 지지 아니합니다\n\n․\n\n․\n\n.\n\n제 12 조 (면책)\n\n   ① 사업자는 천재지변등 불가항력적인 사유로 계약을 이행할 수 없는 경우에는 \n\n이용자에게 책임을 지지 아니하며, 계약금을 반환합니다.\n\n   ② 이용자는 천재지변등 불가항력적인 사유로 계약에서 정한 예식일시에 예식을 \n\n할   수   없는   경우에는   사업자에게   책임을   지지   아니하며,  계약금의   반환을 \n\n청구할 수 있습니다.\n\n제 13 조(재판관할)  이   계약과   관련된   사업자와   이용자간의   소는   민사소송법상의 \n\n관할법원에 제기하여야 합니다.\n\n제 14 조(기타사항)  이   약관에서   규정되지   아니한   사항   또는   이   계약의   해석에 \n\n관하여   다툼이   있는   경우에는   사업자와   이용자가   합의하여   결정하되,  합의가 \n\n \n\f이루어지지 아니한 경우에는 약관의 규제에 관한 법률,  민법,  상법 등 관계법령 \n\n및 공정 타당한 일반관례에 따릅니다. \n\n\f"
df = Text_Pipline(text,"예식장 표준약관")
df.to_csv('result.csv')