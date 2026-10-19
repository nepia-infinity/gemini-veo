import os
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path

# 1. .env ファイルを読み込む
load_dotenv()

# パターンA: .env に "GEMINI_API_KEY" と書いている場合（推奨）
# SDKが自動で os.environ["GEMINI_API_KEY"] を読み取るため引数は不要です
client = genai.Client()

# パターンB: .env の変数名が違う場合や、明示的に渡したい場合
# api_key = os.getenv("GEMINI_API_KEY")
# client = genai.Client(api_key=api_key)

prompt = """Medium shot, static eye-level camera. A Japanese modern office with a calm, minimalist background. 
A young male junior employee calmly walks up to a female senior colleague seated at her desk typing on a laptop. 
The junior stands at a respectful distance (1 meter), gives a polite slight bow, and waits patiently until she notices him and stops typing. 
The junior maintains a calm, friendly smile and makes gentle eye contact, raising one hand slightly in a respectful conversational gesture. 
Warm natural office lighting, clean anime aesthetic, soft colors, high emotional clarity."""

# 動画生成ジョブの投入
operation = client.models.generate_videos(
    model="veo-3.1-generate-preview",
    source=prompt,
    config=types.GenerateVideosConfig(
        aspect_ratio="16:9",
        number_of_videos=1,
    ),
)

# 生成完了を待機
print("Waiting for video generation to complete...")
while not operation.done:
    time.sleep(10)
    operation = client.operations.get(operation)

# ユーザーのホームディレクトリ（C:\Users\nepia）から Downloads フォルダのパスを取得
downloads_folder = Path.home() / "Downloads"
output_path = downloads_folder / "sst_office_good.mp4"

# ダウンロード保存
generated_video = operation.response.generated_videos[0]
client.files.download(file=generated_video.video, destination=str(output_path))
print(f"Saved video to: {output_path}")