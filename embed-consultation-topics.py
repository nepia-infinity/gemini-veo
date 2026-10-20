"""name列のあるCSVにname_embedding列を追加する。

事前準備: pip install google-genai python-dotenv
.envに GEMINI_API_KEY=... を設定し、下の入力・出力パスを変更する。
実行: python embed-consultation-topics.py
"""
import csv
import json
import math
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# この2か所を実際のCSVの場所に変更する。
INPUT_CSV_PATH = Path(
    r"C:\Users\nepia\Desktop\gemini_veo\csv\raw\クイックリプライ一覧.csv"
)
OUTPUT_CSV_PATH = Path(
    r"C:\Users\nepia\Desktop\gemini_veo\csv\outputs\consultation_topics_with_embeddings.csv"
)

# 窓口データを生成したモデル・次元数と必ず揃える。
MODEL = "gemini-embedding-2"
DIMENSIONS = 3072


def main():
    load_dotenv(Path(__file__).resolve().parent / ".env")
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(".envにGEMINI_API_KEYを設定してください。")
    if INPUT_CSV_PATH.resolve() == OUTPUT_CSV_PATH.resolve() or (
        INPUT_CSV_PATH.exists() and OUTPUT_CSV_PATH.exists()
        and INPUT_CSV_PATH.samefile(OUTPUT_CSV_PATH)
    ):
        raise ValueError("入力CSVと出力CSVは別のファイルにしてください。")

    with INPUT_CSV_PATH.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if "name" not in columns:
            raise ValueError("入力CSVにname列がありません。")
        if len(columns) != len(set(columns)):
            raise ValueError("入力CSVの列名が重複しています。")
        rows = list(reader)

    # APIを呼ぶ前に入力を全件検証する。
    for index, row in enumerate(rows, start=1):
        if None in row or any(value is None for value in row.values()):
            raise ValueError(f"データ{index}件目の列数が一致しません。")
        row["name"] = row["name"].strip()
        if not row["name"]:
            raise ValueError(f"データ{index}件目のnameが空です。")

    with genai.Client(api_key=api_key) as client:
        for index, row in enumerate(rows, start=1):
            response = client.models.embed_content(
                model=MODEL,
                contents=row["name"],
                config=types.EmbedContentConfig(output_dimensionality=DIMENSIONS),
            )
            if not response.embeddings or not response.embeddings[0].values:
                raise ValueError(f"{row['name']}: 埋め込みが取得できませんでした。")
            vector = response.embeddings[0].values
            if len(vector) != DIMENSIONS or any(not math.isfinite(v) for v in vector):
                raise ValueError(f"{row['name']}: 埋め込みの次元数または数値が不正です。")
            row["name_embedding"] = json.dumps(vector, allow_nan=False)
            print(f"{index}/{len(rows)}件完了: {row['name']}")

    # 全件成功した場合だけ保存する。既存の出力CSVは上書きする。
    if "name_embedding" not in columns:
        columns.append("name_embedding")
    OUTPUT_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV_PATH.open("w", encoding="utf-8-sig", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    print(f"保存完了: {OUTPUT_CSV_PATH}")


if __name__ == "__main__":
    main()
