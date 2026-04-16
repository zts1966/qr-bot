import os
import cv2
import numpy as np
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

KNOWN_DIR = 'known_qrs'
ref_features = {}

def load_reference_qrs():
    print("正在加载已知二维码...")
    if not os.path.exists(KNOWN_DIR):
        print(f"错误：找不到 {KNOWN_DIR} 文件夹！")
        return
    count = 0
    for sub in os.listdir(KNOWN_DIR):
        sub_path = os.path.join(KNOWN_DIR, sub)
        if not os.path.isdir(sub_path):
            continue
        for fname in os.listdir(sub_path):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(sub_path, fname)
                img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                if img is None:
                    continue
                orb = cv2.ORB_create()
                kp, des = orb.detectAndCompute(img, None)
                if des is not None:
                    ref_features[sub] = des
                    print(f"已加载 {sub}")
                    count += 1
                break
    print(f"共加载 {count} 个二维码")

def match_qr(img_path):
    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None
    orb = cv2.ORB_create()
    kp_q, des_q = orb.detectAndCompute(img, None)
    if des_q is None:
        return None
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    best_match = None
    best_score = 0
    for name, ref_des in ref_features.items():
        matches = bf.match(des_q, ref_des)
        score = len(matches)
        if score > best_score:
            best_score = score
            best_match = name
    return best_match if best_score > 10 else None

async def start(update: Update, context):
    await update.message.reply_text('二维码识别机器人已启动！\n请发送二维码图片给我。')

async def handle_photo(update: Update, context):
    print("收到图片")
    photo = update.message.photo[-1]
    file = await photo.get_file()
    file_path = f"temp_{update.message.message_id}.jpg"
    await file.download_to_drive(file_path)
    
    result = match_qr(file_path)
    os.remove(file_path)
    
    if result:
        await update.message.reply_text(f'✅ 这个二维码来自：【{result}】')
    else:
        await update.message.reply_text('❓ 未找到匹配的二维码')

def main():
    load_reference_qrs()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    print("Bot 启动成功！")
    app.run_polling()

if __name__ == '__main__':
    main()