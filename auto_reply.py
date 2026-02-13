import pyperclip
import pyautogui
import time
import pytesseract
from PIL import Image
import easyocr
import numpy as np  # 需要导入numpy库
import os
from datetime import datetime
import hashlib
import subprocess

# position info(x, y, w, h) of conversation list
CHAT_LIST_REGION = (11, 145, 350, 717)

AUTO_REPLY_TEXT = "你好"

# center position of input box
INPUT_BOX_X=411
INPUT_BOX_Y=797


RIGHT_CHAT_PANEL = (283, 125, 572, 662) # x, y w h

# initiate easyocr to get chat record which is chinese or english
reader = easyocr.Reader(['ch_sim','en']) 

pyautogui.FAILSAFE = False #

UNREAD_ICON_PATH = "red_icon.png"  # d

# 激活微信窗口
def activate_wechat():
    subprocess.call(["wmctrl", "-a", "微信"])

# 找到红点并点击
def click_unread_chat():
    location = pyautogui.locateOnScreen(
        'red_icon.png',
        region=CHAT_LIST_REGION,
        confidence=0.8,
        grayscale=True
    )

    if location:
        print("发现新消息")

        # 获取红点中心
        center = pyautogui.center(location)

        click_x = center.x  # 向左偏移
        click_y = center.y

        print(click_x)
        print(click_y)

        # 点击红点（实际上会点到对应联系人）
        pyautogui.moveTo(click_x, click_y, duration=0.2)
        pyautogui.click()

        time.sleep(0.3)    # 等待会话加载
        print("已点击会话")
        return True

    return False

# 输入内容并发送
def send_message(text):
    # 激活输入框
    pyautogui.moveTo(INPUT_BOX_X, INPUT_BOX_Y, duration=0.2)
    pyautogui.click()
    time.sleep(0.2)

    # 复制文字到剪贴板
    pyperclip.copy(text)

    # 粘贴文字
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.1)

    # 回车发送
    pyautogui.press('enter')
    print("已发送消息:", text)


# def get_new_message():
#     print("start ")
#     screenshot = pyautogui.screenshot(region=RIGHT_CHAT_PANEL)


#     filename = f"chat_content.png"
#     try:
#         if image_hash(screenshot) == image_hash(Image.open(filename)):
#             print("no change")
#             return []
#     except FileNotFoundError:
#         pass  # 第一次运行没有文件，直接保存
                                            

#     # 保存截图到当前目录
#     screenshot.save(filename)
#     print("截图已保存:", os.path.abspath(filename))

#     screenshot_np = np.array(screenshot)

#     img_width = screenshot_np.shape[1]
    

#     # 识别图片
#     result = reader.readtext(screenshot_np)
#     result.sort(key=lambda x: x[0][0][1])  # bbox 左上角的 y

#     messages = []
#     current_msg = None

#     # 打印结果
#     for detection in result:
#         bbox = detection[0]
#         text = detection[1]
#         conf = detection[2]

#         # 左右边距计算
#         x_left = bbox[0][0]
#         x_right = bbox[1][0]

#         left_margin = x_left
#         right_margin = img_width - x_right

#         if left_margin < right_margin:
#             sender = "对方"     # 靠左
#         else:
#             sender = "自己"     # 靠右

#         # if detection[2] < 0.01:
#         #     continue
#         print(f"[{sender}] 识别文本:", text)
#         print("置信度:", detection[2])
#         print("-" * 20)
#         messages.append({
#             "sender": sender,
#             "text": text.strip(),
#             "conf": conf
#         })
#     return messages


def get_new_message():
    print("start ")
    screenshot = pyautogui.screenshot(region=RIGHT_CHAT_PANEL)

    filename = "chat_content.png"

    # try:
    #     if image_hash(screenshot) == image_hash(Image.open(filename)):
    #         print("no change")
    #         return []
    # except FileNotFoundError:
    #     pass  # 第一次运行没有文件，直接保存

    screenshot.save(filename)
    print("截图已保存:", os.path.abspath(filename))

    screenshot_np = np.array(screenshot)
    img_width = screenshot_np.shape[1]

    # OCR
    result = reader.readtext(screenshot_np)

    # 按纵坐标排序
    result.sort(key=lambda x: x[0][0][1])  # bbox 左上角的 y

    messages = []
    current_msg = None

    for detection in result:
        bbox, text, conf = detection
        if conf < 0.5 or not text.strip():
            continue

        x_left = bbox[0][0]
        x_right = bbox[1][0]

        left_margin = x_left
        right_margin = img_width - x_right

        sender = "对方" if left_margin < right_margin else "自己"
        y_top = bbox[0][1]

        # 判断是否属于上一条消息（同侧且行间距小于阈值）
        if current_msg and current_msg["sender"] == sender and y_top - current_msg["last_y"] < 30:
            current_msg["text"] += "\n" + text.strip()
            current_msg["last_y"] = y_top
        else:
            if current_msg:
                # 保存上一条消息
                messages.append({
                    "sender": current_msg["sender"],
                    "text": current_msg["text"],
                    "conf": current_msg["conf"]
                })
            current_msg = {
                "sender": sender,
                "text": text.strip(),
                "conf": conf,
                "last_y": y_top
            }

    # 保存最后一条消息
    if current_msg:
        messages.append({
            "sender": current_msg["sender"],
            "text": current_msg["text"],
            "conf": current_msg["conf"]
        })

    # 打印结果
    for msg in messages:
        print(f"[{msg['sender']}] 识别文本:", msg["text"])
        print("置信度:", msg["conf"])
        print("-" * 20)

    return messages



def image_hash(img):
    arr = np.array(img)
    return hashlib.md5(arr.tobytes()).hexdigest()

def detect_sender(bbox, img_width):
    x1, y1 = bbox[0]
    x3, y3 = bbox[2]

    center_x = (x1 + x3) / 2

    if center_x < img_width * 0.5:
        return "对方"
    else:
        return "自己"

# 主循环
activate_wechat()
while True:
    if click_unread_chat():
        print("已打开会话，发送消息")
        messages = get_new_message()
        if messages:
            text = messages[-1]
            if text['sender'] == "自己":
                print("最后是自己发送的不做处理")
                time.sleep(2)
                continue
            send_message(text['sender'] + ": " + text['text'])
        
        time.sleep(2)  # 避免重复发送

    time.sleep(1)
