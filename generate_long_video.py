import os
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

# 各カット約6〜7秒想定のシナリオ
scenes = [
    # Cut 1: 上司の来訪と状況説明 (Describe & Explain)
    (
        "Medium shot, dimly lit modern Japanese office at night. "
        "A middle-aged boss hands documents to a seated junior employee. "
        "Employee speaks politely in Japanese: 'お声がけありがとうございます。退勤準備中でした。'"
    ),
    # Cut 2: 予定の伝達と代替案の提示 (Explain & Specify)
    (
        "Medium close-up. The employee speaks calmly with gentle eye contact in Japanese: "
        "'本日は予定があり難しいため、明日の朝一番に着手してもよろしいでしょうか？'"
    ),
    # Cut 3: 上司の受諾 (Choose)
    (
        "Over-the-shoulder shot. The boss pauses, checks the document, then nods and speaks in Japanese: "
        "'分かった、明日の午前中までなら大丈夫だ。今日はもう上がりなさい。'"
    ),
    # Cut 4: 感謝と退勤
    (
        "Medium shot. The employee smiles, bows politely, and packs their bag, speaking in Japanese: "
        "'ありがとうございます、明日の午前中に完了させます。お先に失礼します。' "
        "Employee walks toward the exit."
    ),
]

current_video = None

for i, prompt in enumerate(scenes):
    print(f"\n--- Generating Cut {i + 1}/{len(scenes)} ---")

    if current_video is None:
        source_input = types.GenerateVideosSource(
            prompt=prompt,
        )
    else:
        source_input = types.GenerateVideosSource(
            prompt=prompt,
            video=current_video.video,
        )

    operation = client.models.generate_videos(
        model="veo-3.1-generate-preview",
        source=source_input,
    )

    # 完了待機
    while not operation.done:
        print(f"Waiting for cut {i + 1}...")
        time.sleep(10)
        operation = client.operations.get(operation)

    # エラー・レスポンス検証
    if operation.error:
        print(f"Error in Cut {i + 1}: {operation.error}")
        break

    if not operation.response or not operation.response.generated_videos:
        print(f"No video returned in Cut {i + 1}. Raw response: {operation.response}")
        break

    current_video = operation.response.generated_videos[0]
    print(f"Cut {i + 1} completed successfully.")

# 正常終了時に保存
if current_video:
    output_path = Path.home() / "Downloads" / "sst_desc_refusal_30s.mp4"
    client.files.download(file=current_video.video, destination=str(output_path))
    print(f"\nCompleted: Saved to {output_path}")
else:
    print("\nVideo generation stopped due to an error.")