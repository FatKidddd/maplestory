import numpy as np
import time
import cv2
import mss
import tesserocr
from PIL import Image
import re
from vkeys import press, key_down, key_up, click
from random import random
import tkinter as tk
from threading import Thread
from PIL import Image, ImageTk
from pynput.keyboard import Key, Listener as KeyboardListener

api = tesserocr.PyTessBaseAPI(path='C:/Program Files/Tesseract-OCR/tessdata')

class RadioButtons(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.rb1 = tk.Radiobutton(self, text='Any stat', variable=self.parent.v, value="ANY").pack(anchor=tk.W)
        self.rb2 = tk.Radiobutton(self, text='STR', variable=self.parent.v, value="STR").pack(anchor=tk.W)
        self.rb3 = tk.Radiobutton(self, text='DEX', variable=self.parent.v, value="DEX").pack(anchor=tk.W)
        self.rb4 = tk.Radiobutton(self, text='INT', variable=self.parent.v, value="INT").pack(anchor=tk.W)
        self.rb5 = tk.Radiobutton(self, text='LUK', variable=self.parent.v, value="LUK").pack(anchor=tk.W)
        self.rb6 = tk.Radiobutton(self, text='Max HP', variable=self.parent.v, value="Max HP").pack(anchor=tk.W)
        self.rb7 = tk.Radiobutton(self, text='ATT', variable=self.parent.v, value="ATT").pack(anchor=tk.W)
        self.rb8 = tk.Radiobutton(self, text='Magic ATT', variable=self.parent.v, value="Magic ATT").pack(anchor=tk.W)

class CommandButtons(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.start_button = tk.Button(self, text='Start', fg='green', command=self.handle_start)
        self.stop_button = tk.Button(self, text='Stop', fg='red', command=self.handle_stop)
        self.close_button = tk.Button(self, text='Close', fg='brown', command=self.handle_close)

        self.start_button.pack(side="left")
        self.close_button.pack(side="right")

    def handle_start(self):
        global initialised
        initialised = True
        self.parent.render = True
    
    def handle_stop(self):
        global initialised
        initialised = False
        self.parent.render = True
    
    def handle_close(self):
        global keyboard_listener
        self.parent.parent.destroy()
        keyboard_listener.stop()

class App(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.parent.title('Hello')

        self.v = tk.StringVar()
        self.v.set("ANY")
        self.capture_width = 160
        self.capture_height = 75
        self.scl = 1
        self.top_left_coords = (1920-self.capture_width-20, 1080-self.capture_height-90-10)
        self.delay = 15
        self.render = True

        with mss.mss() as sct:
            self.sct = sct

        self.canvas = tk.Canvas(self, width=self.capture_width*self.scl, height=self.capture_height*self.scl)
        self.radiobuttons = RadioButtons(self)
        self.commandbuttons = CommandButtons(self)

        self.canvas.pack()
        self.radiobuttons.pack()
        self.commandbuttons.pack()

        self.update_widget()

    def get_image_and_text(self):
        mon = self.sct.monitors[-1]
        monitor = {
            'left': mon['left'] + self.top_left_coords[0],
            'top': mon['top'] + self.top_left_coords[1],
            'width': self.capture_width,
            'height': self.capture_height,
        }

        im = self.sct.grab(monitor)
        screenshot = np.array(im, dtype=np.uint8)
        resized = cv2.resize(screenshot, None, fx=self.scl, fy=self.scl, interpolation=cv2.INTER_AREA)
        im_gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        thresh = 127
        im_bw = cv2.threshold(im_gray, thresh, 255, cv2.THRESH_BINARY)[1]

        # image process each stat line
        inverted = 255 - im_bw
        horizontal = inverted
        cols = 10000 
        horizontal_structure = cv2.getStructuringElement(cv2.MORPH_RECT, (cols, 1))
        horizontal = cv2.erode(horizontal, horizontal_structure)

        image_height = im_bw.shape[0]
        image_width = im_bw.shape[1]

        i, j = 0, 1e9
        n = im_bw.shape[0]
        line_y_coords = []
        while i<n:
            if horizontal[i][0] == 255:
                j = min(j, i)
                if i==n-1 or horizontal[i+1][0] == 0:
                    line_y_coords.append((i+j)//2)
                    j = 1e9
            i += 1
        line_y_coords.append(image_height)


        final_text = ''
        prev_y = 0
        global api
        for y in line_y_coords:
            stat_line = im_bw[prev_y:y]
            pil_image = Image.fromarray(stat_line)
            api.SetImage(pil_image)
            text = api.GetUTF8Text()
            # print(repr(text))
            final_text += text
            im_bw[prev_y] = np.ones(image_width) * 255
            prev_y = y
        return im_bw, final_text

    def handle_text(self, text, specific):
        pattern = r"Rare|Epic|Attack Increase:"
        pattern2 = r"(.+):.+?(\d+)%"
        matches = re.findall(pattern, text)
        # to ensure text has fully loaded
        # print(text)

        # to bypass warning
        # press('enter', 3)
        if not (len(matches) > 1): return

        print(text)
        stat_matches = re.findall(pattern2, text)
        print(stat_matches)
        print()

        d = { "STR": 0, "DEX": 0, "INT": 0, "LUK": 0, "All Stats": 0, "ATT": 0, "Magic ATT": 0, "Max HP": -3 }

        for stat_name, stat_val in stat_matches:
            val = int(stat_val)
            res = d.get(stat_name)
            if res != None:
                if stat_name == "All Stats":
                    d["STR"] += val
                    d["DEX"] += val
                    d["INT"] += val
                    d["LUK"] += val
                else:
                    d[stat_name] += val
        
        has_hit_target_roll = False

        if specific != "ANY":
            if d[specific] >= 9:
                has_hit_target_roll = True

            for key in d:
                if d[key] >= 12:
                    has_hit_target_roll = True
        else:
            for key in d:
                if d[key] >= 9:
                    has_hit_target_roll = True

        if has_hit_target_roll:
            global initialised
            initialised = False
            self.parent.destroy()
            return
        else:
            print('clicked')
            click((self.top_left_coords[0]+80, self.top_left_coords[1]+90))
        press('enter', 3)

    def update_widget(self):
        img, text = self.get_image_and_text()
        global initialised
        if initialised:
            self.handle_text(text, self.v.get())

        if self.render:
            # I have no idea why but you need to put self. in front of these, i spent 1 hour debugging this
            height, width = img.shape[:2]
            ppm_header = f'P5 {width} {height} 255 '.encode()
            # self.data = ppm_header + cv2.cvtColor(img, cv2.COLOR_BGR2RGB).tobytes()
            self.data = ppm_header + img.tobytes()
            self.photo = tk.PhotoImage(width=width, height=height, data=self.data, format='PPM')
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
        
        self.parent.after(self.delay, self.update_widget)


def on_press(key):
    global root, initialised
    if key == Key.f4:
        initialised = False
        root.destroy()
        return False
    elif key == Key.f6:
        print('Program stopped')
        initialised = not initialised

if __name__ == "__main__":
    initialised = False

    root = tk.Tk()
    app = App(root)
    app.pack()

    
    keyboard_listener = KeyboardListener(on_press=on_press)
    keyboard_listener.start()

    root.mainloop()

    keyboard_listener.stop()