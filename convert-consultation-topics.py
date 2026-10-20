"""相談項目CSVをJSONへ変換する補助スクリプト。

標準ライブラリのみを使用するため、pip installやAPIキーは不要。
下の入力・出力パスを変更して実行する。
Usage: python convert-consultation-topics.py
既存の出力JSONは上書きする。入力CSVは変更しない。
"""
import csv
import json
import math
from pathlib import Path


INPUT_CSV_PATH = Path(
    r"C:\Users\nepia\Desktop\gemini_veo\csv\outputs\consultation_topics_with_embeddings.csv"
)
OUTPUT_JSON_PATH = Path(
    r"C:\Users\nepia\line-ai-sst-cognitive-log\src\data\lineAccounts\consultationTopics.json"
)


def convert(path):
    topics = []
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)):
            raise ValueError("CSVの列名が重複しています。")
        if not {"name", "name_embedding"}.issubset(columns):
            raise ValueError("CSVにname列とname_embedding列が必要です。")
        for row in reader:
            line = reader.line_num
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{line}行目: 列数が一致しません。")
            name = row["name"].strip()
            if not name:
                raise ValueError(f"{line}行目: nameが空です。")
            try:
                vector = json.loads(row["name_embedding"])
            except ValueError as exc:
                raise ValueError(f"{line}行目: 埋め込みが有効なJSONではありません。") from exc
            if not isinstance(vector, list) or len(vector) != 3072:
                raise ValueError(f"{line}行目: 埋め込みには3072次元の配列が必要です。")
            if any(
                type(v) not in (int, float)
                or (isinstance(v, float) and not math.isfinite(v))
                for v in vector
            ):
                raise ValueError(f"{line}行目: 埋め込みに不正な数値があります。")
            topics.append({"name": name, "name_embedding": vector})
    return topics


def main():
    if INPUT_CSV_PATH.resolve() == OUTPUT_JSON_PATH.resolve() or (
        INPUT_CSV_PATH.exists() and OUTPUT_JSON_PATH.exists()
        and INPUT_CSV_PATH.samefile(OUTPUT_JSON_PATH)
    ):
        raise ValueError("入力と出力には別のファイルを指定してください。")
    topics = convert(INPUT_CSV_PATH)
    # 全件を検証してから保存する。
    content = json.dumps(topics, ensure_ascii=False, indent=2, allow_nan=False)
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_JSON_PATH.write_text(content + "\n", encoding="utf-8")
    print(f"変換完了: {len(topics)}件 → {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
