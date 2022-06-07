from paddleocr import PaddleOCR, draw_ocr
import cv2
import numpy as np
import xlrd
from time import sleep
from threading import Thread
import queue
import Levenshtein
from PIL import Image, ImageDraw, ImageFont

iq = queue.Queue(1)
ans = queue.Queue(1)
data = xlrd.open_workbook("data.xls")
table = data.sheets()[0]
def add_text(img, text, left, top, textColor=(255, 255, 0), textSize=30):
    img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    # 创建一个可以在给定图像上绘图的对象
    draw = ImageDraw.Draw(img)
    # 字体的格式
    fontStyle = ImageFont.truetype(
    "font/simsun.ttc", textSize, encoding="utf-8")
    # 绘制文本
    draw.text((left, top), text, textColor, font=fontStyle)
    # 转换回OpenCV格式
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
def find_question(txt):
    mm = 0
    maxid = -1
    for r in range(table.nrows):
        v = Levenshtein.ratio(txt, table.row_values(r)[1])
        if v > mm:
            print(v,table.row_values(r)[1])
            mm = v
            maxid = r
    if maxid >= 0:
        ans.put(maxid)
def get_text(img):
    result = ocr.ocr(img, cls=True)
    res = ""
    for li in result:
        rr = li[1]
        if len(rr[0])>10 and rr[1] > 0.8:
            res += rr[0]
    find_question(res)
def work():
    while True:
        if not iq.empty():
            get_text(iq.get())
        sleep(0.1)
if __name__ == "__main__":
    t = Thread(target=work)
    t.setDaemon(True)
    t.start()
    ocr = PaddleOCR(lang="ch")  # need to run only once to download and load model into memory
    cam=cv2.VideoCapture(0)
    SCREEN_WIDTH=800
    SCREEN_HEIGHT=600
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,SCREEN_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT,SCREEN_HEIGHT)
    idx = 0
    cv2.namedWindow("ans")
    cv2.moveWindow("ans", 800, 300)
    ansm = np.zeros((300,SCREEN_WIDTH, 3), np.uint8)
    last_ans = 0
    while True:
        preview = np.zeros((SCREEN_HEIGHT,SCREEN_WIDTH, 3), np.uint8)
        ret,img = cam.read()      #读取摄像头图片
        if not ret:
            continue
        idx +=1
        if idx % 10 == 0:
            iq.put(img)
        if not ans.empty():
            r = ans.get()
            if r != last_ans:
                ansm = np.zeros((300,SCREEN_WIDTH, 3), np.uint8)
                last_ans = r
            a = table.row_values(r)[2]
            ansm = add_text(ansm,table.row_values(r)[2],10,0)
            if a.find("A")>=0:
                ansm = add_text(ansm,table.row_values(r)[3],10,100)
            if a.find("B")>=0:
                ansm = add_text(ansm,table.row_values(r)[4],10,150)
            if a.find("C")>=0:
                ansm = add_text(ansm,table.row_values(r)[5],10,200)
            if a.find("D")>=0:
                ansm = add_text(ansm,table.row_values(r)[6],10,250)
            cv2.imshow("ans",ansm)
        temp = np.asarray(img)
        temp = temp.reshape((SCREEN_HEIGHT, SCREEN_WIDTH, 3))
        cv2.imshow("cam",img)
        if cv2.waitKey(100) == 27:
            break

