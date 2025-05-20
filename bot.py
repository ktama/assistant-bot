import configparser
import google.generativeai as genai
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio
from pydub import AudioSegment
import os


VOICEVOX_URL = "http://127.0.0.1:50021"  # VoicevoxエンジンのURL
SPEAKER_ID = 1  # 話者ID（1 = 四国めたん など）

vc_client = None

# 設定ファイル読み込み
config = configparser.ConfigParser()
config.read('config.ini')

# Geminiの設定
ai_api_key = config['gemini']['api_key']
ai_model = config['gemini']['model']
genai.configure(api_key=ai_api_key)
model = genai.GenerativeModel(ai_model)

# Discordの設定
token = config['discord']['token']
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

prompt = ""
chat_sessions = {}

@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    await tree.sync()

@tree.command(name="q", description="質問する")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)
    user_id = interaction.user.id

    if user_id not in chat_sessions:
        # 初回はプロンプトを履歴として渡す
        chat_sessions[user_id] = model.start_chat(history=[
            {"role": "user", "parts": [prompt]},
        ])

    chat = chat_sessions[user_id]

    try:
        response = chat.send_message(question)
        reply = response.text

        # 履歴制限：最大5件（含む初期プロンプト）
        if len(chat.history) > 5:
            # 最新5件だけ抽出（直近5ターンの会話）
            new_history = chat.history[-5:]
            chat_sessions[user_id] = model.start_chat(history=new_history)
    except Exception as e:
        reply = f"エラーが発生しました: {e}"

    await interaction.followup.send(reply)

# ボイスチャンネル参加コマンド
@tree.command(name="voice", description="ボイスチャンネルに参加")
async def join_vc(interaction: discord.Interaction):
    global vc_client

    if not interaction.user.voice:
        await interaction.response.send_message("ボイスチャンネルに参加してからコマンドを実行してください。", ephemeral=True)
        return

    channel = interaction.user.voice.channel
    vc_client = await channel.connect()
    await interaction.response.send_message(f"{channel.name} に参加しました。")

@tree.command(name="leave", description="ボイスチャンネルから退出")
async def leave_vc(interaction: discord.Interaction):
    global vc_client

    if vc_client and vc_client.is_connected():
        await vc_client.disconnect()
        vc_client = None
        await interaction.response.send_message("ボイスチャンネルから退出しました。")
    else:
        await interaction.response.send_message("現在ボイスチャンネルに接続していません。", ephemeral=True)

def load_prompt_template():
    with open('prompt.md', 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    return prompt_template


@client.event
async def on_message(message: discord.Message):
    global vc_client

    # Bot自身のメッセージかつVCに接続済みなら読み上げ
    if message.author == client.user and vc_client and vc_client.is_connected():
        await read_aloud(message.content)

async def read_aloud(text):
    # VOICEVOXにテキストを送信して音声取得
    async with aiohttp.ClientSession() as session:
        params = {"text": text, "speaker": SPEAKER_ID}
        async with session.post(f"{VOICEVOX_URL}/audio_query", params=params) as resp:
            if resp.status != 200:
                print("audio_queryエラー")
                return
            audio_query = await resp.json()

        async with session.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": SPEAKER_ID}, json=audio_query) as resp:
            if resp.status != 200:
                print("synthesisエラー")
                return
            with open("output.wav", "wb") as f:
                f.write(await resp.read())

    # 再生（mp3は使わず、wavを直接再生）
    source = discord.FFmpegPCMAudio("output.wav")
    vc_client.play(source)

    # 再生中は待機
    while vc_client.is_playing():
        await asyncio.sleep(0.5)

    # 後片付け
    os.remove("output.wav")

if __name__ == "__main__":
    prompt = load_prompt_template()
    client.run(token)
