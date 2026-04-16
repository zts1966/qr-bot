import os
import io
from PIL import Image
from pyzbar.pyzbar import decode
from flask import Flask
import threading
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# ===== 保持 Railway 在线 =====
flask_app = Flask(__name__)

@flask_app.route('/')
def health():
    return 'Bot is running!'

def run_flask():
    flask_app.run(host='0.0.0.0', port=8080)

threading.Thread(target=run_flask, daemon=True).start()
# ============================

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')
KNOWN_DIR = 'known_qrs'

# 存储链接和群名的对应关系
link_map = {}

def load_qr_links():
    """读取 known_qrs 文件夹里的二维码图片，提取链接"""
    print("正在加载已知二维码链接...")
    print(f"当前工作目录: {os.getcwd()}")
    print(f"known_qrs 是否存在: {os.path.exists('known_qrs')}")
    
    if not os.path.exists(KNOWN_DIR):
        print(f"错误：找不到 {KNOWN_DIR} 文件夹！")
        return
    
    print(f"known_qrs 内容: {os.listdir(KNOWN_DIR)}")
    
    count = 0
    for sub in os.listdir(KNOWN_DIR):
        sub_path = os.path.join(KNOWN_DIR, sub)
        if not os.path.isdir(sub_path):
            continue
        print(f"处理文件夹: {sub}")
        for fname in os.listdir(sub_path):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(sub_path, fname)
                print(f"  读取图片: {fname}")
                try:
                    img = Image.open(img_path)
                    decoded = decode(img)
                    if decoded:
                        url = decoded[0].data.decode('utf-8')
                        link_map[url] = sub
                        print(f"  ✅ 已加载：{sub} -> {url[:50]}...")
                        count += 1
                    else:
                        print(f"  ❌ 无法解码：{fname}")
                except Exception as e:
                    print(f"  ❌ 读取失败：{fname} - {e}")
                break  # 每个文件夹只取第一张图片
    print(f"共加载 {count} 个供方")

def decode_qr_from_bytes(img_bytes):
    """从图片字节数据解码二维码，返回链接"""
    try:
        img = Image.open(io.BytesIO(img_bytes))
        decoded = decode(img)
        if decoded:
            return decoded[0].data.decode('utf-8')
    except Exception as e:
        print(f"解码错误: {e}")
    return None

async def start(update: Update, context):
    await update.message.reply_text('二维码识别机器人已启动！\n请发送二维码图片给我。')

async def handle_photo(update: Update, context):
    print("收到图片")
    photo = update.message.photo[-1]
    file = await photo.get_file()
    img_bytes = await file.download_as_bytearray()
    
    url = decode_qr_from_bytes(img_bytes)
    
    if url:
        print(f"解码链接: {url[:80]}...")
        if url in link_map:
            await update.message.reply_text(f'✅ 这个二维码来自：【{link_map[url]}】')
        else:
            await update.message.reply_text('❓ 未在已知库中找到匹配的二维码')
    else:
        await update.message.reply_text('❌ 无法识别二维码，请确保图片清晰')

def main():
    load_qr_links()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot 启动成功！")
    app.run_polling()

if __name__ == '__main__':
    main()