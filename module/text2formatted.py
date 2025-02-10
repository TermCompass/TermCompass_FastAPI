from module.generator import generate2

def process_and_refine_text(text):
    """
    긴 텍스트를 분할하여 정제하고 결과 합치기
    """

    # 긴 텍스트 -> 분할된 텍스트 list
    max_tokens = 3500
    chunks = []
    current_chunk = []
    current_length = 0

    for paragraph in text.split("\f"):
        paragraph_length = len(paragraph)
        if current_length + paragraph_length > max_tokens:
            chunks.append("".join(current_chunk))
            current_chunk = [paragraph]
            current_length = paragraph_length
        else:
            current_chunk.append(paragraph)
            current_length += paragraph_length

    if current_chunk:
        chunks.append("".join(current_chunk))

    # 각각 청크 refine
    refined_chunks = []
    
    for i, chunk in enumerate(chunks):

        messages=[
                {"role": "system", 
                 "content": 
                 '''
                 You are an assistant that improves and refines legal documents to make them clear and well-formatted.
                 응답은 다음의 JSON 형식을 절대적으로 지키세요. : {"result": html형식의 <body> 안의 내용물 }
                 표로 예상되는 부분은 <table> 태그를 사용하세요.
                 태그 내부의 속성은 표기하지 마세요.
                 '''},
                {"role": "user", "content": f"Please refine the following text: {chunk}"}]
        
        # 답변 생성
        response = generate2(messages)
        
        print(f"Processing chunk {i + 1} of {len(chunks)}...")
        if response["result"]:
            print(response["result"])
            refined_chunks.append(response["result"])

    # 합쳐서 return
    return "".join(refined_chunks)
