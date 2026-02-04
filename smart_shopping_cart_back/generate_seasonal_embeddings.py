import os
import sys
import json
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Skipping .env loading.")

# Configuration
GMS_EMBEDDING_URL = "https://gms.ssafy.io/gmsapi/api.openai.com/v1/embeddings"
OUTPUT_FILE = "db/init/10_seasonal_contexts.sql"

# Seasonal context definitions
SEASONAL_CONTEXTS = {
    "winter": "winter warm beverages hot chocolate tea soup comfort food cozy snacks",
    "spring": "spring fresh vegetables strawberries salad light meals produce",
    "summer": "summer cold drinks icecream watermelon refreshing fruits berries",
    "autumn": "autumn pumpkin apple cinnamon warm spices cozy snacks harvest",
    
    # Major Korean Holidays
    "newyear": "new year celebration fresh start party snacks champagne countdown festive decorations resolution",
    "seollal": "korean lunar new year traditional food hanbok rice cake tteokguk gift sets bowing ceremony ancestral rites family gathering",
    "valentines": "valentines day chocolate gifts candy hearts romance couples desserts sweet treats",
    "childrens": "childrens day kids snacks toys gifts candy fun treats family outing celebration",
    "christmas": "christmas holiday season gifts cookies cake turkey chicken party decorations santa festive treats family gathering celebration",
    "chuseok": "korean thanksgiving harvest moon songpyeon rice cake fruit gift sets traditional food family gathering ancestral rites hanbok"
}

def get_gms_key():
    # Try environment variable first
    key = os.getenv("GMS_KEY")
    if key:
        return key
    
    # If not in env, try reading from .env file directly
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    if '=' in line:
                        k, v = line.strip().split('=', 1)
                        if k == 'GMS_KEY':
                            return v
    
    print("Error: GMS_KEY not found in environment or .env file")
    sys.exit(1)

def get_embedding(text, api_key):
    print(f"  Generating embedding for: {text[:60]}...")
    
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

def generate_sql_file():
    """Generate SQL file with CREATE TABLE and INSERT statements"""
    api_key = get_gms_key()
    
    print("=" * 60)
    print("Seasonal Embeddings Generator")
    print("=" * 60)
    
    # Start building SQL content
    sql_lines = []
    sql_lines.append("")
    sql_lines.append("CREATE TABLE IF NOT EXISTS seasonal_contexts (")
    sql_lines.append("    season TEXT PRIMARY KEY,")
    sql_lines.append("    context_text TEXT NOT NULL,")
    sql_lines.append("    embedding vector(1536) NOT NULL,")
    sql_lines.append("    created_at timestamptz NOT NULL DEFAULT now(),")
    sql_lines.append("    updated_at timestamptz NOT NULL DEFAULT now()")
    sql_lines.append(");")
    sql_lines.append("")
    
    # Generate embeddings for each season
    for season, context_text in SEASONAL_CONTEXTS.items():
        print(f"\n[{season.upper()}]")
        embedding = get_embedding(context_text, api_key)
        
        # Format embedding as PostgreSQL array
        embedding_str = json.dumps(embedding)
        
        # Create INSERT statement
        insert_sql = f"INSERT INTO seasonal_contexts (season, context_text, embedding) VALUES (\n"
        insert_sql += f"  '{season}',\n"
        insert_sql += f"  '{context_text}',\n"
        insert_sql += f"  '{embedding_str}'\n"
        insert_sql += ") ON CONFLICT (season) DO UPDATE SET\n"
        insert_sql += f"  context_text = EXCLUDED.context_text,\n"
        insert_sql += f"  embedding = EXCLUDED.embedding,\n"
        insert_sql += f"  updated_at = now();\n"
        
        sql_lines.append(insert_sql)
        print(f"  ✓ Embedding generated ({len(embedding)} dimensions)")
    
    # Write to file
    sql_content = "\n".join(sql_lines)
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    print(f"✓ SQL file generated: {OUTPUT_FILE}")
    print(f"✓ Total seasons: {len(SEASONAL_CONTEXTS)}")

if __name__ == "__main__":
    generate_sql_file()
