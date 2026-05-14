import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time
from collections import deque

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

PORT = "COM3"
BAUD = 115200
MAX_POINTS = 150

class STM32SpeedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STM32 ADC PI/PID Speed Control Monitor")
        self.root.geometry("1200x760")

        self.ser = None
        self.running = False
        self.reader_thread = None

        self.time_data = deque(maxlen=MAX_POINTS)
        self.sp_data = deque(maxlen=MAX_POINTS)
        self.rpm_data = deque(maxlen=MAX_POINTS)
        self.pwm_data = deque(maxlen=MAX_POINTS)
        self.adc_data = deque(maxlen=MAX_POINTS)
        self.start_time = time.time()

        self.var_status = tk.StringVar(value="Disconnected")
        self.var_mode = tk.StringVar(value="--")
        self.var_enabled = tk.StringVar(value="--")
        self.var_setpoint = tk.StringVar(value="--")
        self.var_rpm = tk.StringVar(value="--")
        self.var_error = tk.StringVar(value="--")
        self.var_pwm = tk.StringVar(value="--")
        self.var_kp = tk.StringVar(value="--")
        self.var_ki = tk.StringVar(value="--")
        self.var_kd = tk.StringVar(value="--")
        self.var_adc = tk.StringVar(value="--")

        self.build_ui()
        self.update_plot()

    def build_ui(self):
        title = ttk.Label(self.root, text="STM32 ADC PI/PID Speed Control Monitor",
                          font=("Segoe UI", 18, "bold"))
        title.pack(pady=10)

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=5)

        conn = ttk.LabelFrame(top, text="Connection")
        conn.pack(side="left", padx=5, pady=5)

        ttk.Label(conn, text="Port").grid(row=0, column=0, padx=5, pady=5)
        self.port_entry = ttk.Entry(conn, width=12)
        self.port_entry.insert(0, PORT)
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(conn, text="Baud").grid(row=1, column=0, padx=5, pady=5)
        self.baud_entry = ttk.Entry(conn, width=12)
        self.baud_entry.insert(0, str(BAUD))
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(conn, text="Connect", command=self.connect_serial).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(conn, text="Disconnect", command=self.disconnect_serial).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(conn, text="Status").grid(row=3, column=0, padx=5, pady=5)
        ttk.Label(conn, textvariable=self.var_status).grid(row=3, column=1, padx=5, pady=5)

        ctrl = ttk.LabelFrame(top, text="Control")
        ctrl.pack(side="left", padx=5, pady=5)

        ttk.Button(ctrl, text="Start", command=lambda: self.send_cmd("START")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(ctrl, text="Stop", command=lambda: self.send_cmd("STOP")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(ctrl, text="Open Loop", command=lambda: self.send_cmd("OPEN")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(ctrl, text="Closed Loop", command=lambda: self.send_cmd("CLOSED")).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(ctrl, text="PI", command=lambda: self.send_cmd("MODE PI")).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(ctrl, text="PID", command=lambda: self.send_cmd("MODE PID")).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(ctrl, text="Setpoint RPM").grid(row=3, column=0, padx=5, pady=5)
        self.sp_entry = ttk.Entry(ctrl, width=10)
        self.sp_entry.insert(0, "1000")
        self.sp_entry.grid(row=3, column=1, padx=5, pady=5)
        ttk.Button(ctrl, text="Send SP", command=self.send_sp).grid(row=3, column=2, padx=5, pady=5)

        ttk.Label(ctrl, text="Manual PWM").grid(row=4, column=0, padx=5, pady=5)
        self.pwm_entry = ttk.Entry(ctrl, width=10)
        self.pwm_entry.insert(0, "1500")
        self.pwm_entry.grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(ctrl, text="Send PWM", command=self.send_pwm).grid(row=4, column=2, padx=5, pady=5)

        tune = ttk.LabelFrame(top, text="Gains")
        tune.pack(side="left", padx=5, pady=5)

        ttk.Label(tune, text="Kp").grid(row=0, column=0, padx=5, pady=5)
        self.kp_entry = ttk.Entry(tune, width=10)
        self.kp_entry.insert(0, "0.30")
        self.kp_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(tune, text="Ki").grid(row=1, column=0, padx=5, pady=5)
        self.ki_entry = ttk.Entry(tune, width=10)
        self.ki_entry.insert(0, "0.05")
        self.ki_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(tune, text="Kd").grid(row=2, column=0, padx=5, pady=5)
        self.kd_entry = ttk.Entry(tune, width=10)
        self.kd_entry.insert(0, "0.00")
        self.kd_entry.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(tune, text="Send Gains", command=self.send_gains).grid(row=3, column=0, columnspan=2, padx=5, pady=8)

        thresh = ttk.LabelFrame(top, text="ADC Thresholds")
        thresh.pack(side="left", padx=5, pady=5)

        ttk.Label(thresh, text="TH High").grid(row=0, column=0, padx=5, pady=5)
        self.thh_entry = ttk.Entry(thresh, width=10)
        self.thh_entry.insert(0, "2600")
        self.thh_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(thresh, text="TH Low").grid(row=1, column=0, padx=5, pady=5)
        self.thl_entry = ttk.Entry(thresh, width=10)
        self.thl_entry.insert(0, "1800")
        self.thl_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(thresh, text="Send TH", command=self.send_thresholds).grid(row=2, column=0, columnspan=2, padx=5, pady=8)

        stats = ttk.LabelFrame(self.root, text="Live Stats")
        stats.pack(fill="x", padx=10, pady=5)

        items = [
            ("Mode", self.var_mode),
            ("Enabled", self.var_enabled),
            ("Setpoint", self.var_setpoint),
            ("RPM", self.var_rpm),
            ("Error", self.var_error),
            ("PWM", self.var_pwm),
            ("ADC Raw", self.var_adc),
            ("Kp(x1000)", self.var_kp),
            ("Ki(x1000)", self.var_ki),
            ("Kd(x1000)", self.var_kd),
        ]

        for i, (name, var) in enumerate(items):
            frame = ttk.Frame(stats)
            frame.grid(row=0, column=i, padx=8, pady=8)
            ttk.Label(frame, text=name, font=("Segoe UI", 10, "bold")).pack()
            ttk.Label(frame, textvariable=var, font=("Segoe UI", 11)).pack()

        graph_frame = ttk.LabelFrame(self.root, text="Live Graph")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(10, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Setpoint, RPM, PWM")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)

        self.line_sp, = self.ax.plot([], [], label="Setpoint")
        self.line_rpm, = self.ax.plot([], [], label="RPM")
        self.line_pwm, = self.ax.plot([], [], label="PWM")
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def connect_serial(self):
        if self.ser and self.ser.is_open:
            return
        try:
            port = self.port_entry.get().strip()
            baud = int(self.baud_entry.get().strip())
            self.ser = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
            self.running = True
            self.reader_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.reader_thread.start()
            self.var_status.set(f"Connected ({port})")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_serial(self):
        self.running = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.var_status.set("Disconnected")

    def send_cmd(self, cmd):
        if self.ser and self.ser.is_open:
            self.ser.write((cmd + "\r\n").encode())

    def send_sp(self):
        self.send_cmd(f"SP {self.sp_entry.get().strip()}")

    def send_pwm(self):
        self.send_cmd(f"PWM {self.pwm_entry.get().strip()}")

    def send_gains(self):
        self.send_cmd(f"KP {self.kp_entry.get().strip()}")
        time.sleep(0.05)
        self.send_cmd(f"KI {self.ki_entry.get().strip()}")
        time.sleep(0.05)
        self.send_cmd(f"KD {self.kd_entry.get().strip()}")

    def send_thresholds(self):
        self.send_cmd(f"THH {self.thh_entry.get().strip()}")
        time.sleep(0.05)
        self.send_cmd(f"THL {self.thl_entry.get().strip()}")

    def read_serial(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if line.startswith("DATA,"):
                    self.handle_data(line)
            except Exception:
                break

    def handle_data(self, line):
        try:
            parts = line.split(",")
            if len(parts) != 11:
                return

            _, sp, rpm, err, pwm, kp, ki, kd, mode, enabled, adc_raw = parts

            self.var_setpoint.set(sp)
            self.var_rpm.set(rpm)
            self.var_error.set(err)
            self.var_pwm.set(pwm)
            self.var_kp.set(kp)
            self.var_ki.set(ki)
            self.var_kd.set(kd)
            self.var_mode.set(mode)
            self.var_enabled.set(enabled)
            self.var_adc.set(adc_raw)

            t = time.time() - self.start_time
            self.time_data.append(t)
            self.sp_data.append(float(sp))
            self.rpm_data.append(float(rpm))
            self.pwm_data.append(float(pwm))
            self.adc_data.append(float(adc_raw))
        except Exception:
            pass

    def update_plot(self):
        self.line_sp.set_data(self.time_data, self.sp_data)
        self.line_rpm.set_data(self.time_data, self.rpm_data)
        self.line_pwm.set_data(self.time_data, self.pwm_data)

        if len(self.time_data) > 1:
            self.ax.set_xlim(min(self.time_data), max(self.time_data))
        else:
            self.ax.set_xlim(0, 10)

        vals = list(self.sp_data) + list(self.rpm_data) + list(self.pwm_data)
        if vals:
            ymin = min(vals) - 50
            ymax = max(vals) + 50
            if ymin == ymax:
                ymax = ymin + 1
            self.ax.set_ylim(ymin, ymax)
        else:
            self.ax.set_ylim(0, 3000)

        self.canvas.draw()
        self.root.after(200, self.update_plot)

if __name__ == "__main__":
    root = tk.Tk()
    app = STM32SpeedApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect_serial(), root.destroy()))
    root.mainloop()
