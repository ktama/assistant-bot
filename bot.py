import configparser
import os
import aiohttp
import asyncio
from pydub import AudioSegment  # 未使用なら削除可
import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai

VOICEVOX_URL = "http://127.0.0.1:50021"
SPEAKER_ID = 2  # 例: 四国めたん

vc_client = None
chat_sessions = {}
prompt = ""

# 設定読み込み
def load_config():
    config = configparser.ConfigParser()
    config.read("config.ini")
    return config

# プロンプトテンプレート読み込み
def load_prompt_template():
    with open("prompt.md", "r", encoding="utf-8") as f:
        return f.read()

# Gemini初期化
def init_gemini(api_key, model_name):
    genai.configure(api_key=api_key)
    return genai.GenerativeModel(model_name)

# VOICEVOXで読み上げ
async def read_aloud(text):
    global vc_client
    async with aiohttp.ClientSession() as session:
        audio_query_resp = await session.post(f"{VOICEVOX_URL}/audio_query", params={"text": text, "speaker": SPEAKER_ID})
        if audio_query_resp.status != 200:
            print("audio_queryエラー")
            return
        audio_query = await audio_query_resp.json()

        synthesis_resp = await session.post(f"{VOICEVOX_URL}/synthesis", params={"speaker": SPEAKER_ID}, json=audio_query)
        if synthesis_resp.status != 200:
            print("synthesisエラー")
            return
        with open("output.wav", "wb") as f:
            f.write(await synthesis_resp.read())

    source = discord.FFmpegPCMAudio("output.wav")
    vc_client.play(source)

    while vc_client.is_playing():
        await asyncio.sleep(0.5)

    os.remove("output.wav")

# main
def main():
    global prompt
    config = load_config()
    prompt = load_prompt_template()

    token = config["discord"]["token"]
    ai_model = init_gemini(config["gemini"]["api_key"], config["gemini"]["model"])

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}!")
        await tree.sync()

    @tree.command(name="q", description="質問する")
    async def ask(interaction: discord.Interaction, question: str):
        await interaction.response.defer(thinking=True)
        user_id = interaction.user.id

        if user_id not in chat_sessions:
            chat_sessions[user_id] = ai_model.start_chat(history=[{"role": "user", "parts": [prompt]}])

        chat = chat_sessions[user_id]
        try:
            response = chat.send_message(question)
            reply = response.text

            if len(chat.history) > 5:
                chat_sessions[user_id] = ai_model.start_chat(history=chat.history[-5:])
        except Exception as e:
            reply = f"エラーが発生しました: {e}"

        await interaction.followup.send(reply)
        await read_aloud(reply)

    @tree.command(name="jv", description="ボイスチャンネルに参加")
    async def join_vc(interaction: discord.Interaction):
        global vc_client

        if not interaction.user.voice:
            await interaction.response.send_message("ボイスチャンネルに参加してからコマンドを実行してください。", ephemeral=True)
            return

        channel = interaction.user.voice.channel
        vc_client = await channel.connect()
        await interaction.response.send_message(f"{channel.name} に参加しました。")

    @tree.command(name="lv", description="ボイスチャンネルから退出")
    async def leave_vc(interaction: discord.Interaction):
        global vc_client

        if vc_client and vc_client.is_connected():
            await vc_client.disconnect()
            vc_client = None
            await interaction.response.send_message("ボイスチャンネルから退出しました。")
        else:
            await interaction.response.send_message("現在ボイスチャンネルに接続していません。", ephemeral=True)

    @client.event
    async def on_message(message: discord.Message):
        global vc_client

        if message.author == client.user and vc_client and vc_client.is_connected():
            await read_aloud(message.content)

    client.run(token)

if __name__ == "__main__":
    main()
