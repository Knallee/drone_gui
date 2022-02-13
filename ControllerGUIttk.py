# Copy Rights:
# This program was built mainly by following python tutorila provided by pythonprogramming.net
# Many essential functions/ classes are copied with little change.

import tkinter as tk
from tkinter import ttk             # Better looking GUI
import time
import serial
import struct                       # used to pack/unpack data packets
import threading

# The program includes a receiving feature with live data plot! However, matplotlib.pyplot turned out to be not very
# suitable for live plotting. The program becomes very slow when we include this and I'm not able to solve the problem
# with threading unfortunately. Thus, I have commented all the code parts that deal with this feature. If you are
# interested in testing the functionality, feel free to set en_RX_mode.

en_RX_mode = False

if en_RX_mode:
    from collections import deque     # used to store received data to plot!
    import matplotlib
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib import style
    from matplotlib.figure import Figure
    import matplotlib.animation as animation

    matplotlib.use("TkAgg")

    # Better looking Graphs
    style.use('ggplot')
    darkColor = '#183A54'
    lightColor = '#00A3E0'

    # Initiating plots
    f = Figure(figsize=(5,5), dpi=100)
    a = f.add_subplot(411)
    b = f.add_subplot(412)
    c = f.add_subplot(413)
    d = f.add_subplot(414)

    # Arrays to store received data
    Roll = deque(maxlen=50)
    Pitch = deque(maxlen=50)
    Yaw = deque(maxlen=50)
    Thrust = deque(maxlen=50)

    # Used to break out of the port listening loop
    listenFlag = False


LARGE_FONT = ("Verdana", 12)
NORM_FONT = ("Helvetica", 10)
SMALL_FONT = ("Helvetica", 8)

# Open and set serial port
ser = serial.Serial()
ser.baudrate = 9600
ser.port = 'COM1'
ser.open()

# Lists to store navigation commands
navigationList = []
periodsList = []


if en_RX_mode:
    # Start the port listening thread
    def start_listening():
        t = threading.Thread(target=listening)
        t.daemon = True
        t.start()

    # Stops the port listening thread
    def stop_listening():
        global listenFlag
        listenFlag = True


    def listening():
        global listenFlag
        global Roll
        global Pitch
        global Yaw
        global Thrust

        # Start listening until listenFlag = False
        while True:
            # if data is sensed on the port, read and process the data
            if ser.inWaiting() > 0:
                # Data packet size is 8 bytes. The data structure is determined on the transmitter side.
                msg = ser.read(8)
                dataList = list(msg)                                                        # little endian
                pData1 = struct.pack("2B", dataList[0], dataList[1])  # pack the data into chunks of 2
                Thrust.append(struct.unpack(">H", pData1))
                pData1 = struct.pack("2B", dataList[2], dataList[3])  # pack the data into chunks of 2
                Yaw.append(struct.unpack(">H", pData1))
                pData1 = struct.pack("2B", dataList[4], dataList[5])  # pack the data into chunks of 2
                Pitch.append(struct.unpack(">H", pData1))
                pData1 = struct.pack("2B", dataList[6], dataList[7])  # pack the data into chunks of 2
                Roll.append(struct.unpack(">H", pData1))

            if listenFlag:
                listenFlag = False
                break

    # The function used to animate all the plots
    def animate(i):
        global Roll
        global Pitch
        global Yaw
        global Thrust

        # Figures need to be cleared on every plot.
        a.clear()
        b.clear()
        c.clear()
        d.clear()

        # Must be set every time after clearing
        a.set_ylim([0, 1050])
        b.set_ylim([0, 1050])
        c.set_ylim([0, 1050])
        d.set_ylim([0, 1050])

        a.set_ylabel("Thrust")
        b.set_ylabel("Yaw")
        c.set_ylabel("Pitch")
        d.set_ylabel("Roll")

        # Plot The received data from Quad
        a.plot(Roll, darkColor)
        b.plot(Pitch, lightColor)
        c.plot(Yaw)
        d.plot(Thrust)


# This function pops up a a mini window to ask for the number of seconds the user wants to move
# The direction is stored in navigationList and the number of seconds is stored in the periodList


def storeMove(direction):
    global navigationList
    global periodsList

    # Create a window with title and label
    timeQ = tk.Tk()
    timeQ.wm_title("Seconds?")
    label = ttk.Label(timeQ, text = "Choose how many seconds you want the move:")
    label.pack(side="top", fill="x", pady=10)

    # Create and initialize the entry box widget
    e = ttk.Entry(timeQ)
    e.insert(0,0)
    e.pack()
    e.focus_set()

    # Store values in variable upon a button press
    def callback():
        global navigationList
        global periodsList

        moveSecs = (e.get())
        navigationList.append(direction)
        periodsList.append(moveSecs)

        timeQ.destroy()

    b = ttk.Button(timeQ, text="Submit", width=10, command=callback)
    b.pack()

    # Keep the window open until it's closed
    tk.mainloop()

# This function pops up a small window to indicate the direction the quad is flying in for the periodList number of
# seconds. The pop up is destroyed whenever the direction is changed


def popupmsg(index):
    global navigationList
    global periodsList

    # Create a window with title and label
    popup = tk.Tk()
    popup.wm_title("!")
    label = ttk.Label(popup, text=str("Moving " + navigationList[index]), font=NORM_FONT)
    label.pack(side="top")

    # Close the window after a certain number of seconds
    def leavemini():
        global periodsList
        if len(periodsList):
            for i in range(1, int(periodsList[index])):
                time.sleep(1)
        popup.destroy()

    # Starts the closing routine after one second (because we need to run mainloop first!)
    popup.after(1000, leavemini)

    # Keep the window open until it's closed
    popup.mainloop()


# This is the main Window for the app. It inherits from tk.Tk. The general structure is taken from pythonprogramming.net
class ControllerGUI(tk.Tk):
    # Create and Initialize the main window
    def __init__(self, *args, **kwargs):

        tk.Tk.__init__(self, *args, **kwargs)
        tk.Tk.wm_title(self, "Quad Controller")
        tk.Tk.tk_setPalette(self, background='white', foreground='black',
                            activeBackground='black', activeForeground='white')
        container = tk.Frame(self)

        container.pack(side="top", fill="both", expand=True)

        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        # The code to switch between frames. It's based on a thread in StackOverflow
        self.frames = {}

        for F in (StartPage, TXMode, RXMode, Navigation):

            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # start by showing the start page
        self.show_frame(StartPage)

        # Use HJ.ico as the frame's icon
        tk.Tk.iconbitmap(self, default='HJ.ico')

    def show_frame(self, cont):

        frame = self.frames[cont]
        frame.tkraise()


# Start page has buttons to bransh to three different modes: Transmitter, Receiver, and Navigation.
class StartPage(tk.Frame):
    # Create and Initialize the window/frame
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Start Page", font=LARGE_FONT, background="white")
        label.pack(pady=10,padx=10)

        button = ttk.Button(self, text="TXMode",
                            command=lambda: controller.show_frame(TXMode))
        button.pack(side="right")

        button2 = ttk.Button(self, text="RXMode",
                             command=lambda: controller.show_frame(RXMode))
        button2.pack(side="left")

        button3 = ttk.Button(self, text="Navigation Mode",
                             command=lambda: controller.show_frame(Navigation))
        button3.pack()

        button4 = ttk.Button(self, text="Disconnect",
                             command=self.disconnect)
        button4.pack()

    def disconnect(self):
        ser.write(b'\x01\xf4')  # Reset Thrust, Yaw, ....
        ser.write(b'\x01\xf4')
        ser.write(b'\x01\xf4')
        ser.write(b'\x01\xf4')
        ser.write(b'\x02')  # Key to switch off PC mode


# Transmit mode page
class TXMode(tk.Frame):

    # Create and Initialize the frame
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="TXMode", font=LARGE_FONT, background="white")
        label.pack(pady=10, padx=10)
        self._job = None

        # Create, Initialize, and place the slider widgets
        self.slider1 = ttk.Scale(self, from_=500, to=-500, orient="vertical", value=True, command=self.updateValue)
        self.slider2 = ttk.Scale(self, from_=500, to=-500, orient="vertical", value=True, command=self.updateValue)
        self.slider3 = ttk.Scale(self, from_=500, to=-500, orient="vertical", value=True, command=self.updateValue)
        self.slider4 = ttk.Scale(self, from_=500, to=-500, orient="vertical", value=True, command=self.updateValue)

        self.slider3.place(x=210, y=130, anchor="center")
        self.slider4.place(x=280, y=130, anchor="center")
        self.slider1.place(x=40 , y=130, anchor="center")
        self.slider2.place(x=110, y=130, anchor="center")

        # Create, Initialize, and place the slider widgets
        label = ttk.Label(self, text="Thrust", font=NORM_FONT, background="white")
        label.place(x=40, y=200, anchor="center")
        label = ttk.Label(self, text="Yaw", font=NORM_FONT, background="white")
        label.place(x=110, y=200, anchor="center")
        label = ttk.Label(self, text="Roll", font=NORM_FONT, background="white")
        label.place(x=210, y=200, anchor="center")
        label = ttk.Label(self, text="Pitch", font=NORM_FONT, background="white")
        label.place(x=280, y=200, anchor="center")

        # A button to return to the Home Window
        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_frame(StartPage))
        button1.pack()

        # A button to return to the Home Window
        button2 = ttk.Button(self, text="Reset",
                             command=self.resetSliders)
        button2.pack()

    def resetSliders(self):
        self.slider1.set(0)
        self.slider2.set(0)
        self.slider3.set(0)
        self.slider4.set(0)

    # A two level function to update
    def updateValue(self, event):
        if self._job:
            self.after_cancel(self._job)
        self._job = self.after(50, self._do_something)

    def _do_something(self):
        self._job = None
        inBytes = struct.pack(">H", (500+int(self.slider1.get())))
        ser.write(inBytes)

        inBytes = struct.pack(">H", (500+int(self.slider2.get())))
        ser.write(inBytes)

        inBytes = struct.pack(">H", (500+int(self.slider3.get())))
        ser.write(inBytes)

        inBytes = struct.pack(">H", (500+int(self.slider4.get())))
        ser.write(inBytes)

        ser.write(b'\x00')  # Key for slider controll mode


# Receiver mode page
class RXMode(tk.Frame):
    # Create and Initialize the frame
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="RXMode", font=LARGE_FONT, background="white")
        label.pack(pady=10, padx=10)

        # A button to return to the Home Window
        button1 = ttk.Button(self, text="Back to Home",
                             command=lambda: controller.show_frame(StartPage))
        button1.pack(side="top")

        if en_RX_mode:
            # Buttons to start or stop listening to the serial port
            button2 = ttk.Button(self, text="Start",
                                 command=start_listening)
            button2.pack(side="right")

            button3 = ttk.Button(self, text="Stop",
                                 command=stop_listening)
            button3.pack(side="left")

            # Create and initialize the canavas on witch the plots are placed
            canvas = FigureCanvasTkAgg(f, self)
            canvas.show()
            canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)


# Navigation mode page
class Navigation(tk.Frame):
    # Create and Initialize the frame
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Navigation Mode", font=LARGE_FONT, background="white")
        label.pack(pady=10, padx=10)

        # A button to return to the Home Window
        button1 = ttk.Button(self, text="Back to Home", command=lambda: controller.show_frame(StartPage))
        button1.pack(side="bottom")

        # Buttons to choose the navigation directions
        button2 = ttk.Button(self, text="Forward", command=lambda: storeMove("Forward"))
        button2.pack(side="top")

        button3 = ttk.Button(self, text="Backward", command=lambda: storeMove("Backward"))
        button3.pack(side="bottom")

        button4 = ttk.Button(self, text="Left", command=lambda: storeMove("Left"))
        button4.pack(side="left")

        button5 = ttk.Button(self, text="Right", command=lambda: storeMove("Right"))
        button5.pack(side="right")

        # A button to start the autopilot
        button6 = ttk.Button(self, text="Start Autopilot", command=self.startAutoPilot)
        button6.place(x=160, y=115, anchor="center")

    # A function to start the autopilot
    def startAutoPilot(self):
        global navigationList
        global periodsList

        # Loop in the navigation list
        for i in range(len(navigationList)):
            # Start the popup message thread
            t = threading.Thread(target=popupmsg, args=(i, ))
            t.daemon = True
            t.start()

            # Depending on the direction, send the appropriate signal to the controller (and the nto the Quad)
            if navigationList[i] == "Forward":
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\xf4')
                ser.write(b'\x02\x58')  # Roll = 600
                ser.write(b'\x01\xf4')

            elif navigationList[i] == "Backward":
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\x90')  # Roll = 400
                ser.write(b'\x01\xf4')

            elif navigationList[i] == "Right":
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\xf4')
                ser.write(b'\x02\x58')  # Pitch = 600

            else:
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\xf4')
                ser.write(b'\x01\x90')  # Pitch = 400

            ser.write(b'\x01')  # Key for autopilot mode
            time.sleep(float(periodsList[i]))

        ser.write(b'\x01\xf4')  # Reset Thrust, Yaw, ....
        ser.write(b'\x01\xf4')
        ser.write(b'\x01\xf4')
        ser.write(b'\x01\xf4')
        ser.write(b'\x00')      # Key to return to sliders mode

        navigationList.clear()  # Clear Navigation List and Time list
        periodsList.clear()

# This variable needs to persist: Main application
app = ControllerGUI()
# Specify the size of the program window
app.geometry("320x220")
# Choose the style for all the ttk widgets
ttk.Style().theme_use('clam')

if en_RX_mode:
    # This variable needs to persist: Animate the plots
    ani = animation.FuncAnimation(f, animate, interval=100)

# Keep the window open until it's closed
app.mainloop()
# Close the port when the application window is closed
ser.close()
