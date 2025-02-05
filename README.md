# FastAPI
TermCompass AI모델 처리

## 0. 디렉토리 구조
```
─TermCompass_FastAPI
   ├─admin
   │  └─api_key
   ├─Data
   │  ├─Database
   ├─module
   └─task
```

## 1. 검토
입력
```
{"content":"text 혹은 파일"}
```
출력
```
{"result":["검토 결과1","검토 결과2","검토 결과3"...]}
or
{"result":"파일을 읽을 수 없습니다."} # 파일 읽기 실패시
```

## 2. 생성
입력
```
{"content":"사용자 요청 내용"}
```
출력
```
{"result":10001} # 표준 약관 문서 ID
```

## 3. 수정
입력
```
{
    "request":"사용자 요청 내용",
    "current":"현재 작성된 약관",
    "context","현재 컨텍스트"
}
```
출력
```
{
    "result": {
        "answer": "[변경 List]", 
        "context": "업데이트된 context"
    }
}
```

## 4. 채팅
입력
```
{
    "request":"사용자 요청 내용",
    "context","현재 컨텍스트"
}
```
출력
```
{
    "result": {
        "answer": "답변", 
        "context": "업데이트된 context"
    }
}
```
---