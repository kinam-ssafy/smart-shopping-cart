import os
import sys
import re
import json
import random
import time
import math
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Skipping .env loading.")

# 설정
GMS_EMBEDDING_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
GMS_CHAT_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/chat/completions"
# 아직 DB에 넣기 전이므로, 로컬 SQL 파일에서 데이터를 읽어서 'In-Memory DB'처럼 씁니다.
PRODUCTS_SQL_FILE = "db/init/03_products.sql"
SQL_FILE = "db/init/07_vectors.sql"

def get_gms_key():
    key = os.getenv("GMS_KEY")
    if not key:
        print("Error: GMS_KEY not found in .env")
        sys.exit(1)
    return key

def parse_product_names(sql_file):
    """
    03_products.sql에서 상품 ID와 이름을 매핑합니다.
    (ID는 INSERT 순서대로 1부터 시작한다고 가정)
    """
    print(f"Loading product names from {sql_file}...")
    name_map = {}
    
    if not os.path.exists(sql_file):
        print(f"Warning: {sql_file} not found. Using fallback names.")
        return name_map

    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # INSERT INTO products ... VALUES ('이름', ...
    # 간단한 정규식으로 '따옴표로 시작하는 첫 번째 값' 추출
    # VALUES 이후의 괄호 묶음 찾기
    matches = re.findall(r"\((.*?)\)", content, re.DOTALL)
    
    pid = 1
    for match in matches:
        # 첫 번째 '문자열' 찾기
        parts = re.findall(r"'([^']*)'", match)
        if parts:
            name = parts[0] # 첫 번째가 name
            name_map[str(pid)] = name
            pid += 1
            
    print(f"Loaded {len(name_map)} product names.")
    return name_map

def parse_vectors_from_sql(sql_file, name_map):
    """
    07_vectors.sql 파일을 파싱하여 메모리에 로드합니다.
    name_map을 사용하여 정확한 상품명을 연결합니다.
    """
    print(f"Loading vectors from {sql_file}...")
    items = []
    
    if not os.path.exists(sql_file):
        print(f"Error: {sql_file} not found. Please run generate_vectors_gms.py first.")
        sys.exit(1)
        
    with open(sql_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pattern = re.compile(r"\s*\((\d+),\s*\d+,\s*'([^']*)',\s*'(\[.*?\])'\)")
    matches = pattern.findall(content)
    
    for m in matches:
        pid = m[0]
        desc = m[1]
        vector_str = m[2]
        
        # 이름 매핑 확인
        real_name = name_map.get(pid, desc.split(' ', 1)[0]) # 없으면 첫 단어
        
        vector = json.loads(vector_str)
        items.append({
            "id": pid,
            "name": real_name,
            "text": desc, # 설명 원본
            "vector": vector
        })
        
    print(f"Loaded {len(items)} items from SQL file.")
    return items

def get_embedding(text, api_key):
    """GMS Embedding API 호출"""
    print(f"\n[1] Generating Embedding for context...")
    print(f"    Context: {text[:60]}...")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "text-embedding-3-small",
        "input": text
    }
    
    response = requests.post(GMS_EMBEDDING_URL, headers=headers, json=data)
    if response.status_code != 200:
        print(f"Embedding API Error: {response.text}")
        sys.exit(1)
        
    return response.json()['data'][0]['embedding']

def cosine_similarity(v1, v2):
    """코사인 유사도 계산"""
    dot_product = sum(a*b for a,b in zip(v1, v2))
    norm_a = math.sqrt(sum(a*a for a in v1))
    norm_b = math.sqrt(sum(b*b for b in v2))
    return dot_product / (norm_a * norm_b)

def get_recommendation_explanation(cart_items, recommended_items, api_key):
    """GMS Chat API (GPT-5-nano) 호출"""
    print(f"\n[3] Asking AI for explanation (Model: gpt-5-nano)...")
    
    # 이제 정확한 이름을 사용합니다.
    cart_names = ", ".join([item['name'] for item in cart_items])
    rec_names = ", ".join([item['name'] for item in recommended_items])
    
    prompt = f"""
    사용자가 장바구니에 다음 물품을 담았습니다: [{cart_names}]
    그래서 시스템이 다음 물품들을 추천했습니다: [{rec_names}]
    
    이 추천이 왜 좋은지 사용자에게 친절하게 설명해주는 멘트를 한국어로 작성해주세요.
    마치 마트 직원이 추천해주듯 자연스럽게, 한두 문장으로 써주세요.
    """
    
    print(f"    Prompt: 사용자가 [{cart_names}] 등을 담아서 [{rec_names}] 등을 추천함...")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": "gpt-5.2",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful shopping assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    start_time = time.time()
    response = requests.post(GMS_CHAT_URL, headers=headers, json=data)
    end_time = time.time()
    
    if response.status_code != 200:
        print(f"Chat API Error: {response.text}")
        return
        
    result = response.json()
    print(f"⏱️ AI Response Time: {end_time - start_time:.2f}s")
    print("-" * 50)
    print("🤖 AI Explanation:")
    print(result['choices'][0]['message']['content'])
    print("-" * 50)

def main():
    api_key = get_gms_key()
    
    # 0. 상품명 로드
    name_map = parse_product_names(PRODUCTS_SQL_FILE)

    # 1. 가짜 DB 로드 (이름 포함)
    db_items = parse_vectors_from_sql(SQL_FILE, name_map)
    if len(db_items) < 2:
        print("Not enough items in vector file.")
        sys.exit(1)
        
    # 2. 임의의 장바구니 상황 연출
    cart_picks = random.sample(db_items, 2)
    print(f"\n🛒 Current Cart: {[c['name'] for c in cart_picks]}")
    
    # 3. 임베딩 생성 (맥락 만들기)
    # 이름과 설명을 적절히 섞어서 문맥 생성
    context_text = ", ".join([f"{c['name']} {c['text']}" for c in cart_picks])
    context_vector = get_embedding(context_text, api_key)
    
    # 4. 유사도 검색
    print("\n[2] Calculating Similarities (In-Memory)...")
    results = []
    
    for item in db_items:
        if any(c['id'] == item['id'] for c in cart_picks):
            continue
        score = cosine_similarity(context_vector, item['vector'])
        results.append((score, item))
        
    results.sort(key=lambda x: x[0], reverse=True)
    top_5 = results[:5]
    
    print("\n📦 Top 5 Recommendations:")
    for score, item in top_5:
        print(f" - [{score:.4f}] {item['name']}")
        
    # 5. AI 설명 생성
    get_recommendation_explanation(cart_picks, [r[1] for r in top_5], api_key)

if __name__ == "__main__":
    main()
