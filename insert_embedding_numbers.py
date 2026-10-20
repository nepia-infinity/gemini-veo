import os
import time
import json
import pandas as pd
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError(".env ファイルに GEMINI_API_KEY が見つかりません。")

# api_key 引数に直接渡して初期化
client = genai.Client(api_key=api_key)

INPUT_CSV_PATH = r"C:\Users\nepia\Desktop\gemini_veo\csv\raw\AI-SSTの開発順序 - LINEアカウント一覧.csv"
OUTPUT_CSV_PATH = r"C:\Users\nepia\Desktop\gemini_veo\csv\outputs\AI-SSTの開発順序 - LINE_with_embeddings.csv"

# 修正後: 'models/' を付与
def get_embedding(text: str, model: str = "gemini-embedding-2") -> list:
    if pd.isna(text) or not str(text).strip():
        return []
    
    try:
        response = client.models.embed_content(
            model=model,
            contents=str(text),
        )
        return response.embeddings[0].values
    except Exception as e:
        print(f"Error embedding text: '{text[:20]}...': {e}")
        return []

def main():
    print(f"CSV読み込み中: {INPUT_CSV_PATH}")
    df = pd.read_csv(INPUT_CSV_PATH)

    print("name 列のエンベディングを生成中...")
    name_embeddings = []
    for text in df["name"]:
        emb = get_embedding(text)
        # CSV保存時に崩れないよう JSON 文字列として保持
        name_embeddings.append(json.dumps(emb))
        time.sleep(0.1)  # レートリミット回避のための微小ウェイト

    print("summary 列のエンベディングを生成中...")
    summary_embeddings = []
    for text in df["summary"]:
        emb = get_embedding(text)
        summary_embeddings.append(json.dumps(emb))
        time.sleep(0.1)

    # 新しい列として追加
    df["name_embedding"] = name_embeddings
    df["summary_embedding"] = summary_embeddings

    # CSV出力
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    df.to_csv(OUTPUT_CSV_PATH, index=False, encoding="utf-8-sig")   
    print(f"完了しました！出力先: {OUTPUT_CSV_PATH}")

if __name__ == "__main__":
    main()