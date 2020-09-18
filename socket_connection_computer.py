see__author__ = 'zhengwang'

import threading
import SocketServer
import cv2
import numpy as np
import socket

image=""
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
    scale = 10
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
    print(measure())
    if measure() < 25:
        result = 'stop'
    elif left == right == 159:
        result = 'backward'
    elif left1 == right1 == 159:
        if left_sum > right_sum:
            result = 'left'
        else:
            result = 'right'
    elif a < 120 and abs(a - b) < 3:
        if right_sum > left_sum:
            result = 'right'
        elif right_sum < left_sum:
            result = 'left'
        else:
            result = 'forward'

    elif left1 - left + (right1 - right) > 25:
        result = 'right'

    elif left1 - left + (right1 - right) < -25:
        result = 'left'
    else:
        result = 'forward'

    return result

class VideoStreamHandler(SocketServer.StreamRequestHandler):

    def handle(self):
        global image
        stream_bytes = ' '

        try:
            while True:
                stream_bytes += self.rfile.read(1024)
                first = stream_bytes.find('\xff\xd8')
                last = stream_bytes.find('\xff\xd9')
                if first != -1 and last != -1:
                    jpg = stream_bytes[first:last+2]
                    stream_bytes = stream_bytes[last+2:]
                    image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
                    #masked_image=select_white(image,150)
                    print(len(image))
                    print(image[len(image)-1])#
                    print(image[int(len(image)/2)])
                    print(image[0])
                    cv2.imshow('image', image)
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('i'):
                        tm = time.time()
                        cv2.imwrite("./{0}.jpg".format(tm),image)
            cv2.destroyAllWindows()

        finally:
            print "Connection closed on thread 1"


class KeyboardControl(SocketServer.BaseRequestHandler):
    data=" "
    global image
    def handle(self):
        try:
            while self.data:
                key = cv2.waitKey(1) & 0xFF
                if key==255:
                    key="No Keyboard Input"
                    print(image)
                elif key==ord('q'):
                    key="TURNR"
                elif key==ord('e'):
                    key="TURNL"
                elif key == ord('w'):
                    key = "SLOW"
                elif key == ord('s'):
                    key = "BACK"
                elif key == ord('d'):
                    key = "LEFT"
                elif key == ord('a'):
                    key = "RIGHT"
                elif key == ord('z'):
                    key = "FAST"
                else:
                    key=chr(key)
                self.data = self.request.recv(1024)
                self.request.sendall(key)
                keyboard_data = self.data.decode()
                print(keyboard_data)
            cv2.destroyAllWindows()
        finally:
            print "Connection closed on thread 1"

class ThreadServer(object):
    def server_thread(host, port):
        server = SocketServer.TCPServer((host, port), KeyboardControl)
        server.serve_forever()
    
    ip=socket.gethostbyname(socket.getfqdn())
    keyboard_thread = threading.Thread(target=server_thread(ip, 8889))
    keyboard_thread.start()

if __name__ == '__main__':
    ThreadServer()
