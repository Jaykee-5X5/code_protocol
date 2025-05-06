from machine import Pin, SoftI2C
import ssd1306
import gfx
from time import sleep

i2c = SoftI2C(scl=Pin(18), sda=Pin(19))

oled_width = 128
oled_height = 64
oled = ssd1306.SSD1306_I2C(oled_width, oled_height, i2c)
graphics = gfx.GFX(oled_width, oled_height, oled.pixel)


def print_text(msg,x=0,y=0):
    print('I am printing text')

    # clear the screen
    oled.fill(0)
    #place text on the screen
    oled.text(msg, x,y)
    # show the screen
    oled.show()  


def plot_line(*args,**kwargs):
    print('I am plotting a line')
