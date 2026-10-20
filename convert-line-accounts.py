"""LINEアカウントCSVをJSONへ変換する補助スクリプト。

CSVの列名をJSONのキーとして保持する。
*_embedding列は数値配列、空の埋め込みは[]、その他の空欄はnullにする。
既存の埋め込みを変換するだけなので、APIキーやpip installは不要。

Usage:
    python convert-line-accounts.py input.csv
    python convert-line-accounts.py input.csv -o line-accounts.json

出力先を省略すると、入力CSVと同じ場所・同じ名前の.jsonを作成する。
既存の出力ファイルは上書きする。入力CSVは変更しない。
"""

import argparse
import csv
import json
import math
from pathlib import Path


REQUIRED_COLUMNS = {"name", "line_id", "summary", "url",
                    "name_embedding", "summary_embedding"}


def parse_embedding(value, column, line_number):
    """CSV内の配列文字列を検証し、JSONの数値配列に戻す。"""
    if not value:
        return []
    try:
        vector = json.loads(value)
    except (ValueError, RecursionError) as exc:
        raise ValueError(
            f"{line_number}行目: {column}が有効なJSON配列ではありません"
        ) from exc
    if not isinstance(vector, list) or any(
        type(number) not in (int, float)
        or (isinstance(number, float) and not math.isfinite(number))
        for number in vector
    ):
        raise ValueError(
            f"{line_number}行目: {column}には有限の数値の配列が必要です"
        )
    return vector


def convert(path):
    accounts = []
    dimensions = {}
    # utf-8-sigはBOM付き・BOMなしのUTF-8をどちらも読み込める。
    with Path(path).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        columns = reader.fieldnames or []
        if len(columns) != len(set(columns)):
            raise ValueError("CSVの列名が重複しています")
        missing = REQUIRED_COLUMNS - set(columns)
        if missing:
            raise ValueError("必要な列がありません: " + ", ".join(sorted(missing)))

        for row in reader:
            line_number = reader.line_num
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{line_number}行目: 列数がヘッダーと一致しません")
            account = {}
            for column, raw_value in row.items():
                value = raw_value.strip()
                if column.endswith("_embedding"):
                    vector = parse_embedding(value, column, line_number)
                    # 非空のベクトルは同じ列内で次元数をそろえる。
                    if vector:
                        expected = dimensions.setdefault(column, len(vector))
                        if len(vector) != expected:
                            raise ValueError(
                                f"{line_number}行目: {column}の次元数が不一致です"
                                f"（期待: {expected}、実際: {len(vector)}）"
                            )
                    account[column] = vector
                else:
                    account[column] = value or None
            accounts.append(account)
    return accounts


def main():
    input_path = Path(
        r"C:\Users\nepia\Desktop\gemini_veo\csv\outputs\AI-SSTの開発順序 - LINE_with_embeddings.csv"
    )
    target = input_path.with_suffix(".json")

    try:
        accounts = convert(input_path)
        content = json.dumps(
            accounts, ensure_ascii=False, indent=2, allow_nan=False
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n", encoding="utf-8")
    except (OSError, ValueError, csv.Error) as exc:
        print(f"変換に失敗しました: {exc}")
        raise SystemExit(1)

    print(f"変換完了: {len(accounts)}件 → {target}")


if __name__ == "__main__":
    main()
