import serial
import time

PORT = "/dev/cu.usbmodem31301"
BAUD = 9600

ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
print("Connected. Commands: P<0-180>  T<20-160>  LON  LOFF  quit")

def send(cmd):
    ser.write((cmd + '\n').encode())
    print(f"Sent: {cmd}")

while True:
    cmd = input("> ").strip().upper()
    if cmd == "QUIT":
        send("LOFF")
        ser.close()
        break
    elif cmd:
        send(cmd)
