from paddleocr import PaddleOCR, draw_ocr
import cv2
import numpy as np
import xlrd
from time import sleep
from threading import Thread
import queue
import Levenshtein
import datetime
from PIL import Image, ImageDraw, ImageFont
import os
import pyttsx3
import logging
logger = logging.getLogger("simple")
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("log.txt")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(asctime)s][%(levelname)s]%(message)s", '%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)
logger.addHandler(fh)

voice =  pyttsx3.init()
voice.setProperty("rate", 150)
def say_word(n,s):
    voice.say("题目 %s, 答案是 %s"%(n,s))
    voice.runAndWait()
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True' # for fix libiomp5md.dll error

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
def find_question(num, txt):
    mm = 0
    maxid = -1
    for r in range(table.nrows):
        v = Levenshtein.ratio(txt, table.row_values(r)[1])
        if v > mm:
            mm = v
            maxid = r
    if maxid >= 0:
        ans.put((num, maxid,mm))
    if mm < 0.5:
        logger.info("new question:%f,%s",v, res)
    return mm
def get_text(img):
    result = ocr.ocr(img, cls=True)
    res = ""
    for li in result:
        rr = li[1]
        if len(rr[0])>6 and rr[1] > 0.8:
            res += rr[0]
    l = res.find(".") #problem
    if len(res)<5 or l<1 or l>2:
        return
    num = res[:l]
    txt = res[l+1:]
    find_question(num, txt)
def work():
    while True:
        if not iq.empty():
            get_text(iq.get())
        sleep(0.5)
if __name__ == "__main__":
    logger.info("question system start.")
    cam=cv2.VideoCapture(0)
    if cam is None or not cam.isOpened():
        logger.error("camera open failed, exit.")
        exit(0)
    ocr = PaddleOCR(lang="ch")  # need to run only once to download and load model into memory
    t = Thread(target=work)
    t.setDaemon(True)
    t.start()
    SCREEN_WIDTH=800
    SCREEN_HEIGHT=600
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,SCREEN_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT,SCREEN_HEIGHT)
    idx = 0
    say_ct = 0
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
            n,r,v = ans.get()
            logger.debug("%s,%f,%s", n, v, table.row_values(r)[1])
            if r == last_ans:
                say_ct +=1
            if r != last_ans:
                ansm = np.zeros((300,SCREEN_WIDTH, 3), np.uint8)
                last_ans = r
                say_ct = 0
                if v <0.5: # not in data
                    ansm = add_text(ansm,"注意，题库可能未找到！",50,50,textColor=(255, 0, 0))
            ansm = add_text(ansm,"匹配度：        ",200,0)
            ansm = add_text(ansm,"匹配度：%.2f"%v,200,0)
            a = str(table.row_values(r)[2])
            if say_ct > 2:
                say_word(n, a)
            ansm = add_text(ansm,a,10,0)
            if a.find("A")>=0:
                ansm = add_text(ansm,str(table.row_values(r)[3]),10,100)
            if a.find("B")>=0:
                ansm = add_text(ansm,str(table.row_values(r)[4]),10,150)
            if a.find("C")>=0:
                ansm = add_text(ansm,str(table.row_values(r)[5]),10,200)
            if a.find("D")>=0:
                ansm = add_text(ansm,str(table.row_values(r)[6]),10,250)
            cv2.imshow("ans",ansm)
        temp = np.asarray(img)
        temp = temp.reshape((SCREEN_HEIGHT, SCREEN_WIDTH, 3))
        cv2.imshow("cam",img)
        if cv2.waitKey(200) == 27:
            break

