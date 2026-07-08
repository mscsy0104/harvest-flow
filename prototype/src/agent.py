from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate

# 로컬 Ollama에 올라온 모델 지정 (gemma:2b, llama3, eeve 등 본인 모델명 입력)
llm = Ollama(model="gemma4:latest", temperature=0.2)

def generate_ai_metadata(body_text):
    """로컬 LLM을 호출하여 본문 요약 및 키워드 태그 추출"""
    print("🧠 [로컬 LLM] AI가 문서를 분석 중입니다... 잠시만 기다려주세요.")
    
    template = """
    당신은 테크 블로그 전문 편집자입니다. 다음 본문을 읽고 두 가지를 수행해주세요.
    1. 본문을 딱 2줄로 명확하게 요약해주세요. (앞에 '- '를 붙이세요)
    2. 본문과 관련된 핵심 키워드 태그 3개를 뽑아주세요. (예: #데이터, #생산성)

    [본문]
    {body}

    [출력 포맷]
    요약:
    (요약 내용)
    태그:
    (태그 내용)
    """
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm
    
    try:
        response = chain.invoke({"body": body_text})
        return response
    except Exception as e:
        return f"AI 정제 실패 (Ollama 미구동 또는 에러): {e}"