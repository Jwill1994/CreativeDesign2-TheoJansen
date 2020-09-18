see__author__ = 'zhengwang'

import threading
import SocketServer
#import serial
import cv2
import numpy as np
import math
import socket
# distance data measured by ultrasonic sensor
mode = "No object"
def select_white(image, white):
    lower = np.uint8([white, white, white])
    upper = np.uint8([255, 255, 255])
    white_mask = cv2.inRange(image, lower, upper)
    return white_mask

def line_direction(image, upper_limit):
    height, width = image.shape
    height = height - 1
    width = width - 1
    center = int(width / 2)
    right = width
    left = 0
    left1 = 0
    right1 = width
    white_distance = np.zeros(width)
    scale = 5
    for i in range(center):
        if image[height - 30, center - i] > 200:
            left1 = center - i
            break
    for i in range(center):
        if image[height - 30, center + i] > 200:
            right1 = center + i
            break
    for i in range(center):
        if image[height, center - i] > 200:
            left = center - i
            break
    for i in range(center):
        if image[height, center + i] > 200:
            right = center + i
            break
    center = int((left + right) / 2.)
    center1 = int((left1 + right1) / 2.)
    for i in range(0, int(318 / scale)):
        for j in range(height - 1):
            white_distance[scale * i] = j
            if image[height - j, scale * i] > 200:
                white_distance[scale * i] = j
                break

    a = white_distance[center]
    b = white_distance[center1]
    left_sum = np.sum(white_distance[0:center])
    right_sum = np.sum(white_distance[center:319])
    print(left, right, left1, right1, center, center1, a, b)
    print(left_sum, right_sum)
    if left == right == 159:
        result = 'backward'
    elif left1 == right1 == 159:
        if left_sum > right_sum:
            result = 'left'
        else:
            result = 'right'
    elif a < 140 and float(white_distance[center+20]-white_distance[center-20])/40.0 < 0.2 :
        if right_sum > left_sum+500:
            result = 'right'
        elif right_sum+500 < left_sum:
            result = 'left'
        else:
            result = 'forward'
    elif abs(center-center1) < 25 :
        result = 'forward'
    elif left1 - left + (right1 - right) > 25.:
        result = 'right'

    elif left1 - left + (right1 - right) < -25.:
        result = 'left'
    else:
        result = 'forward'

    return result

class ObjectDetection(object):
    def detectTUMB(self, cascade_classifier, gray_image, image):
        # y camera coordinate of the target point 'P'
        # detection
        mode="No object"
        cascade_obj = cascade_classifier.detectMultiScale(
            gray_image,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30,30)
            #flags=cv2.cv.CV_HAAR_SCALE_IMAGE
        )
        for (x_pos, y_pos, width, height) in cascade_obj:
            # draw a rectangle around the objects
            #print(width,height)
            if(width>=50):
                cv2.rectangle(image, (x_pos, y_pos), (x_pos+width, y_pos+height), (255, 255, 255), 2)
                cv2.putText(image, 'Tumbler', (x_pos, y_pos-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                mode="Tumbler"

        return mode

class VideoStreamHandler(SocketServer.StreamRequestHandler):
    obj_detection = ObjectDetection()

    # cascade classifiers
    cup_cascade=cv2.CascadeClassifier('cascade_xml/cascade.xml')

    def handle(self):
        stream_bytes = ' '
        # stream video frames one by one
        try:
            valid=0
            while True:
                global mode
                stream_bytes += self.rfile.read(1024)
                first = stream_bytes.find('\xff\xd8')
                last = stream_bytes.find('\xff\xd9')
                if first != -1 and last != -1:
                    jpg = stream_bytes[first:last+2]
                    stream_bytes = stream_bytes[last+2:]
                    gray = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8),  cv2.IMREAD_GRAYSCALE)
                    image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                    masked_image = select_white(image, 150)
                    image_h, image_w,channels = image.shape
                    a=line_direction(masked_image,200)
                    mode=self.obj_detection.detectTUMB(self.cup_cascade, gray, image)
                    local=mode+","+a
                    # object detection

                    #cv2.imshow("white", mask_image)

                    cv2.imshow('image1', image)
                    cv2.imshow('image2', masked_image)
                    #cv2.imshow('grayimage', gray)
                    key = cv2.waitKey(1) & 0xFF
                    valid=1
                if valid==1:
                    self.request.send(local)
                    print(local)
                    valid=0
            cv2.destroyAllWindows()

        finally:
            print ("Connection closed on thread 1")


class ThreadServer(object):
    def server_thread(host, port):
        server = SocketServer.TCPServer((host, port), VideoStreamHandler)
        server.serve_forever()

    #def server_thread2(host, port):
    #    server = SocketServer.TCPServer((host, port), SensorDataHandler)
    #    server.serve_forever()

    ip=socket.gethostbyname(socket.getfqdn())
    print(ip)
    #distance_thread = threading.Thread(target=server_thread2, args=(ip, 9998))
    #distance_thread.start()
    video_thread = threading.Thread(target=server_thread(ip, 8889))
    video_thread.start()


