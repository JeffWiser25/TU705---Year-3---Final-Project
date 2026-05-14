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
        self.root.title("STM32 Speed Control Monitor")
        self.root.geometry("1200x760")

        self.ser = None
        self.running = False
        self.reader_thread = None

        self.time_data = deque(maxlen=MAX_POINTS)
        self.setpoint_data = deque(maxlen=MAX_POINTS)
        self.rpm_data = deque(maxlen=MAX_POINTS)
        self.pwm_raw_data = deque(maxlen=MAX_POINTS)

        self.start_time = time.time()

        self.var_connection = tk.StringVar(value="Disconnected")
        self.var_mode = tk.StringVar(value="--")
        self.var_enabled = tk.StringVar(value="--")
        self.var_setpoint = tk.StringVar(value="--")
        self.var_rpm = tk.StringVar(value="--")
        self.var_error = tk.StringVar(value="--")
        self.var_pwm_raw = tk.StringVar(value="--")
        self.var_kp = tk.StringVar(value="--")
        self.var_ki = tk.StringVar(value="--")
        self.var_kd = tk.StringVar(value="--")
        self.var_pulses = tk.StringVar(value="--")

        self.build_ui()
        self.update_plot()

    def build_ui(self):
        title = ttk.Label(
            self.root,
            text="STM32 PI/PID Speed Control Monitor",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=10)

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=5)

        conn = ttk.LabelFrame(top, text="Connection")
        conn.pack(side="left", padx=5, pady=5, fill="y")

        ttk.Label(conn, text="Port").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.port_entry = ttk.Entry(conn, width=12)
        self.port_entry.insert(0, PORT)
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(conn, text="Baud").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.baud_entry = ttk.Entry(conn, width=12)
        self.baud_entry.insert(0, str(BAUD))
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(conn, text="Connect", command=self.connect_serial).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(conn, text="Disconnect", command=self.disconnect_serial).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(conn, text="Status").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(conn, textvariable=self.var_connection, foreground="blue").grid(row=3, column=1, padx=5, pady=5, sticky="w")

        ctrl = ttk.LabelFrame(top, text="Controls")
        ctrl.pack(side="left", padx=5, pady=5, fill="y")

        ttk.Button(ctrl, text="Start", command=lambda: self.send_cmd("START")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(ctrl, text="Stop", command=lambda: self.send_cmd("STOP")).grid(row=0, column=1, padx=5, pady=5)

        ttk.Button(ctrl, text="Open Loop", command=lambda: self.send_cmd("MODE OPEN")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(ctrl, text="PI", command=lambda: self.send_cmd("MODE PI")).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(ctrl, text="PID", command=lambda: self.send_cmd("MODE PID")).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(ctrl, text="Setpoint RPM").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sp_entry = ttk.Entry(ctrl, width=10)
        self.sp_entry.insert(0, "1000")
        self.sp_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(ctrl, text="Send SP", command=self.send_sp).grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(ctrl, text="Kp").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.kp_entry = ttk.Entry(ctrl, width=10)
        self.kp_entry.insert(0, "1.0")
        self.kp_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(ctrl, text="Ki").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.ki_entry = ttk.Entry(ctrl, width=10)
        self.ki_entry.insert(0, "0.0")
        self.ki_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(ctrl, text="Kd").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.kd_entry = ttk.Entry(ctrl, width=10)
        self.kd_entry.insert(0, "0.0")
        self.kd_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(ctrl, text="Send Gains", command=self.send_gains).grid(row=6, column=0, columnspan=3, padx=5, pady=8)

        stats_frame = ttk.LabelFrame(self.root, text="Live Stats")
        stats_frame.pack(fill="x", padx=10, pady=5)

        stats = [
            ("Mode", self.var_mode),
            ("Enabled", self.var_enabled),
            ("Setpoint RPM", self.var_setpoint),
            ("RPM", self.var_rpm),
            ("Error", self.var_error),
            ("PWM Raw", self.var_pwm_raw),
            ("Kp x1000", self.var_kp),
            ("Ki x1000", self.var_ki),
            ("Kd x1000", self.var_kd),
            ("Pulse Count", self.var_pulses),
        ]

        for i, (label, var) in enumerate(stats):
            box = ttk.Frame(stats_frame)
            box.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")
            ttk.Label(box, text=label, font=("Segoe UI", 10, "bold")).pack()
            ttk.Label(box, textvariable=var, font=("Segoe UI", 11)).pack()

        graph = ttk.LabelFrame(self.root, text="Live Graph")
        graph.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(11, 5), dpi=100)
        self.ax1 = self.fig.add_subplot(111)
        self.ax2 = self.ax1.twinx()

        self.ax1.set_title("Setpoint / RPM / PWM Raw")
        self.ax1.set_xlabel("Time (s)")
        self.ax1.set_ylabel("RPM")
        self.ax2.set_ylabel("PWM Raw")
        self.ax1.grid(True)

        self.line_setpoint, = self.ax1.plot([], [], label="Setpoint RPM", color="tab:blue")
        self.line_rpm, = self.ax1.plot([], [], label="Measured RPM", color="tab:green")
        self.line_pwm, = self.ax2.plot([], [], label="PWM Raw", color="tab:red")

        lines = [self.line_setpoint, self.line_rpm, self.line_pwm]
        labels = [l.get_label() for l in lines]
        self.ax1.legend(lines, labels, loc="upper left")

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        bottom = ttk.Label(
            self.root,
            text="Expected serial format: DATA,setpoint_rpm,rpm,error,pwm_raw,pwm_pct,kp,ki,kd,mode,enabled,pulse_count"
        )
        bottom.pack(pady=5)

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
            self.var_connection.set(f"Connected ({port})")
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))

    def disconnect_serial(self):
        self.running = False
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
        except Exception:
            pass
        self.var_connection.set("Disconnected")

    def send_cmd(self, cmd):
        if self.ser and self.ser.is_open:
            self.ser.write((cmd + "\r\n").encode())

    def send_sp(self):
        self.send_cmd(f"SP {self.sp_entry.get().strip()}")

    def send_gains(self):
        self.send_cmd(f"KP {self.kp_entry.get().strip()}")
        time.sleep(0.05)
        self.send_cmd(f"KI {self.ki_entry.get().strip()}")
        time.sleep(0.05)
        self.send_cmd(f"KD {self.kd_entry.get().strip()}")

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
            if len(parts) != 12:
                return

            _, sp, rpm, err, pwm_raw, _pwm_pct, kp, ki, kd, mode, enabled, pulses = parts

            self.var_setpoint.set(sp)
            self.var_rpm.set(rpm)
            self.var_error.set(err)
            self.var_pwm_raw.set(pwm_raw)
            self.var_kp.set(kp)
            self.var_ki.set(ki)
            self.var_kd.set(kd)
            self.var_mode.set(mode)
            self.var_enabled.set(enabled)
            self.var_pulses.set(pulses)

            t = time.time() - self.start_time
            self.time_data.append(t)
            self.setpoint_data.append(float(sp))
            self.rpm_data.append(float(rpm))
            self.pwm_raw_data.append(float(pwm_raw))
        except Exception:
            pass

    def update_plot(self):
        self.line_setpoint.set_data(self.time_data, self.setpoint_data)
        self.line_rpm.set_data(self.time_data, self.rpm_data)
        self.line_pwm.set_data(self.time_data, self.pwm_raw_data)

        if len(self.time_data) > 1:
            self.ax1.set_xlim(min(self.time_data), max(self.time_data))
        else:
            self.ax1.set_xlim(0, 10)

        rpm_vals = list(self.setpoint_data) + list(self.rpm_data)
        if rpm_vals:
            self.ax1.set_ylim(0, max(100, max(rpm_vals) + 100))
        else:
            self.ax1.set_ylim(0, 3000)

        pwm_vals = list(self.pwm_raw_data)
        if pwm_vals:
            self.ax2.set_ylim(0, max(100, max(pwm_vals) + 100))
        else:
            self.ax2.set_ylim(0, 7000)

        self.canvas.draw()
        self.root.after(200, self.update_plot)


if __name__ == "__main__":
    root = tk.Tk()
    app = STM32SpeedApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect_serial(), root.destroy()))
    root.mainloop()
