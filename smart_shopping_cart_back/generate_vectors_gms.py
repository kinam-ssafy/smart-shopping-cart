import re
import json
import requests
import os
import sys
import time
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Skipping .env loading.")

# 설정
GMS_API_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
INPUT_SQL_FILE = "db/init/03_products.sql"
OUTPUT_SQL_FILE = "db/init/07_vectors.sql"
MODEL_NAME = "text-embedding-3-small"

def get_gms_key():
    """환경 변수에서 GMS_KEY를 가져옵니다."""
    key = os.getenv("GMS_KEY")
    if not key:
        print("Error: GMS_KEY environment variable is not set.")
        print("Please set it in your terminal or add it to .env file (requires python-dotenv).")
        sys.exit(1)
    return key

def parse_products(sql_file):
    """SQL 파일에서 상품명과 설명을 파싱합니다."""
    products = []
    
    try:
        with open(sql_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # INSERT INTO 구문 파싱 (간단한 정규식 사용)
        # 주의: SQL 문법이 복잡하면 이 정규식은 실패할 수 있음. 
        # 현재 03_products.sql의 포맷: ('이름', ..., '설명', ...),
        # 4번째 필드가 설명이라고 가정
        
        # 정규식 설명:
        # VALUES 뒤에 오는 괄호 묶음들을 찾음.
        # 각 괄호 안에는 '값' 들이 콤마로 구분됨.
        # 문자열 값은 '...' 형태로 감싸져 있음.
        
        # 각 insert value 튜플을 찾습니다.
        # \(([^)]+)\) 패턴은 괄호 안에 괄호가 없을 때만 작동하므로 취약함.
        # 하지만 현재 파일 구조상 설명에 괄호가 없거나 적다면 작동함.
        # 더 견고한 파싱을 위해 ' 로 시작하고 ' 로 끝나는 문자열을 추출
        
        matches = re.findall(r"\((.*?)\)", content, re.DOTALL)
        
        product_Index = 1
        for match in matches:
            # 쉼표로 분리하되, 따옴표 안의 쉼표는 무시해야 함... 복잡함.
            # 하지만 현재 데이터는 단순하므로 단순 분할 시도.
            # '청송 꿀사과', 'cat-fresh-fruits', 3.50, '설명...', ...
            
            # 따옴표로 둘러싸인 문자열 추출
            parts = re.findall(r"'([^']*)'", match)
            
            if len(parts) >= 2:
                name = parts[0]
                # 카테고리(1) 다음이 설명 일 수도 있고...
                # SQL 구조: name, category_id, price, description
                # price는 숫자로 따옴표가 없을 수 있음.
                
                # 정석대로 쉼표 기준 분할 (따옴표 고려 안함 - 위험하지만 현재 데이터셋엔 쉼표가 설명 외엔 없어보임)
                # 더 안전하게: '설명' 부분은 보통 가장 긴 텍스트일 것임.
                
                description = ""
                for p in parts:
                    if len(p) > 20: # 설명은 보통 길다
                        description = p
                        break
                
                if description:
                    products.append({
                        "id": product_Index, # BIGSERIAL 순서 가정
                        "name": name,
                        "description": description
                    })
                    product_Index += 1
                    
        return products

    except FileNotFoundError:
        print(f"Error: File {sql_file} not found.")
        sys.exit(1)

def get_embedding(text, api_key):
    """GMS API를 호출하여 임베딩을 생성합니다."""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    data = {
        "model": MODEL_NAME,
        "input": text
    }
    
    try:
        response = requests.post(GMS_API_URL, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        return result['data'][0]['embedding']
    except Exception as e:
        print(f"API Error for text '{text[:20]}...': {e}")
        return None

def generate_sql(products, api_key):
    """임베딩 데이터를 포함한 SQL 파일을 생성합니다."""
    print(f"Generatings embeddings for {len(products)} products...")
    
    with open(OUTPUT_SQL_FILE, 'w', encoding='utf-8') as f:
        f.write("-- Generated Vector Data for RagChunks\n")
        f.write("TRUNCATE TABLE rag_chunks;\n\n")
        f.write("INSERT INTO rag_chunks (product_id, chunk_index, chunk_text, embedding) VALUES\n")
        
        first = True
        for i, product in enumerate(products):
            print(f"[{i+1}/{len(products)}] Embedding: {product['name']}")
            
            embedding = get_embedding(product['description'], api_key)
            if embedding:
                # 벡터 배열을 문자열 '[0.1, 0.2, ...]' 형태로 변환
                vector_str = str(embedding)
                
                # SQL 생성
                if not first:
                    f.write(",\n")
                
                # 쿼리 작성 (ID는 1부터 순차적이라고 가정)
                # chunk_index는 0 (설명 전체를 하나로 봄)
                # metadata는 생략 (default {})
                sql_value = f"({product['id']}, 0, '{product['description']}', '{vector_str}')"
                f.write(sql_value)
                first = False
                
                # API 부하 조절
                time.sleep(0.1)
            else:
                print(f"Skipping {product['name']} due to error.")
        
        f.write(";\n")
    
    print(f"Done! Saved to {OUTPUT_SQL_FILE}")

if __name__ == "__main__":
    if not os.path.exists("db/init"):
        os.makedirs("db/init", exist_ok=True)
        
    api_key = get_gms_key()
    products = parse_products(INPUT_SQL_FILE)
    
    if products:
        generate_sql(products, api_key)
    else:
        print("No products found to process.")
