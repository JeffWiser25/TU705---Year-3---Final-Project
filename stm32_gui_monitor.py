import tkinter as tk
from tkinter import ttk, messagebox
import serial
import threading
import time
from collections import deque

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ---------------- CONFIG ----------------
PORT = "COM4"          # change to your STM32 COM port
BAUD = 115200
MAX_POINTS = 100
# ----------------------------------------


class STM32MonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STM32 PI/PID Speed Control Monitor")
        self.root.geometry("1100x700")

        self.ser = None
        self.running = False
        self.reader_thread = None

        self.setpoint_data = deque(maxlen=MAX_POINTS)
        self.feedback_data = deque(maxlen=MAX_POINTS)
        self.pwm_data = deque(maxlen=MAX_POINTS)
        self.time_data = deque(maxlen=MAX_POINTS)

        self.start_time = time.time()

        self.var_connection = tk.StringVar(value="Disconnected")
        self.var_mode = tk.StringVar(value="--")
        self.var_enabled = tk.StringVar(value="--")
        self.var_setpoint = tk.StringVar(value="--")
        self.var_feedback = tk.StringVar(value="--")
        self.var_error = tk.StringVar(value="--")
        self.var_pwm = tk.StringVar(value="--")
        self.var_kp = tk.StringVar(value="--")
        self.var_ki = tk.StringVar(value="--")
        self.var_kd = tk.StringVar(value="--")

        self.build_ui()
        self.update_plot()

    def build_ui(self):
        title = ttk.Label(
            self.root,
            text="STM32 PI/PID Speed Control Monitor",
            font=("Segoe UI", 18, "bold")
        )
        title.pack(pady=10)

        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)

        conn_frame = ttk.LabelFrame(top_frame, text="Connection")
        conn_frame.pack(side="left", padx=5, pady=5, fill="y")

        ttk.Label(conn_frame, text="Port").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.port_entry = ttk.Entry(conn_frame, width=12)
        self.port_entry.insert(0, PORT)
        self.port_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(conn_frame, text="Baud").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.baud_entry = ttk.Entry(conn_frame, width=12)
        self.baud_entry.insert(0, str(BAUD))
        self.baud_entry.grid(row=1, column=1, padx=5, pady=5)

        ttk.Button(conn_frame, text="Connect", command=self.connect_serial).grid(row=2, column=0, padx=5, pady=5)
        ttk.Button(conn_frame, text="Disconnect", command=self.disconnect_serial).grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(conn_frame, text="Status").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ttk.Label(conn_frame, textvariable=self.var_connection, foreground="blue").grid(row=3, column=1, padx=5, pady=5, sticky="w")

        control_frame = ttk.LabelFrame(top_frame, text="Controls")
        control_frame.pack(side="left", padx=5, pady=5, fill="y")

        ttk.Button(control_frame, text="Start", command=lambda: self.send_cmd("START")).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Stop", command=lambda: self.send_cmd("STOP")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="PI Mode", command=lambda: self.send_cmd("MODE PI")).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="PID Mode", command=lambda: self.send_cmd("MODE PID")).grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(control_frame, text="Setpoint").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.sp_entry = ttk.Entry(control_frame, width=12)
        self.sp_entry.insert(0, "2000")
        self.sp_entry.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="Send SP", command=self.send_setpoint).grid(row=2, column=2, padx=5, pady=5)

        ttk.Label(control_frame, text="Kp").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.kp_entry = ttk.Entry(control_frame, width=10)
        self.kp_entry.insert(0, "0.8")
        self.kp_entry.grid(row=3, column=1, padx=5, pady=5)

        ttk.Label(control_frame, text="Ki").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.ki_entry = ttk.Entry(control_frame, width=10)
        self.ki_entry.insert(0, "0.2")
        self.ki_entry.grid(row=4, column=1, padx=5, pady=5)

        ttk.Label(control_frame, text="Kd").grid(row=5, column=0, padx=5, pady=5, sticky="w")
        self.kd_entry = ttk.Entry(control_frame, width=10)
        self.kd_entry.insert(0, "0.05")
        self.kd_entry.grid(row=5, column=1, padx=5, pady=5)

        ttk.Button(control_frame, text="Send Gains", command=self.send_gains).grid(row=6, column=0, columnspan=3, padx=5, pady=8)

        stats_frame = ttk.LabelFrame(self.root, text="Live Stats")
        stats_frame.pack(fill="x", padx=10, pady=5)

        stats = [
            ("Mode", self.var_mode),
            ("Enabled", self.var_enabled),
            ("Setpoint", self.var_setpoint),
            ("Feedback", self.var_feedback),
            ("Error", self.var_error),
            ("PWM", self.var_pwm),
            ("Kp", self.var_kp),
            ("Ki", self.var_ki),
            ("Kd", self.var_kd),
        ]

        for i, (label, var) in enumerate(stats):
            box = ttk.Frame(stats_frame)
            box.grid(row=0, column=i, padx=8, pady=8, sticky="nsew")
            ttk.Label(box, text=label, font=("Segoe UI", 10, "bold")).pack()
            ttk.Label(box, textvariable=var, font=("Segoe UI", 11)).pack()

        graph_frame = ttk.LabelFrame(self.root, text="Live Graph")
        graph_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.fig = Figure(figsize=(10, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Setpoint, Feedback, and PWM")
        self.ax.set_xlabel("Time (s)")
        self.ax.set_ylabel("Value")
        self.ax.grid(True)

        self.line_setpoint, = self.ax.plot([], [], label="Setpoint")
        self.line_feedback, = self.ax.plot([], [], label="Feedback")
        self.line_pwm, = self.ax.plot([], [], label="PWM")
        self.ax.legend()

        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        bottom = ttk.Label(self.root, text="Expected serial format: DATA,setpoint,feedback,error,pwm,kp,ki,kd,mode,enabled")
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

    def send_setpoint(self):
        sp = self.sp_entry.get().strip()
        self.send_cmd(f"SP {sp}")

    def send_gains(self):
        kp = self.kp_entry.get().strip()
        ki = self.ki_entry.get().strip()
        kd = self.kd_entry.get().strip()
        self.send_cmd(f"KP {kp}")
        time.sleep(0.05)
        self.send_cmd(f"KI {ki}")
        time.sleep(0.05)
        self.send_cmd(f"KD {kd}")

    def read_serial(self):
        while self.running:
            try:
                line = self.ser.readline().decode(errors="ignore").strip()
                if not line:
                    continue
                if line.startswith("DATA,"):
                    self.handle_data_line(line)
            except Exception:
                break

    def handle_data_line(self, line):
        try:
            parts = line.split(",")
            if len(parts) != 10:
                return

            _, setpoint, feedback, error, pwm, kp, ki, kd, mode, enabled = parts

            self.var_setpoint.set(setpoint)
            self.var_feedback.set(feedback)
            self.var_error.set(error)
            self.var_pwm.set(pwm)
            self.var_kp.set(kp)
            self.var_ki.set(ki)
            self.var_kd.set(kd)
            self.var_mode.set(mode)
            self.var_enabled.set(enabled)

            t = time.time() - self.start_time
            self.time_data.append(t)
            self.setpoint_data.append(float(setpoint))
            self.feedback_data.append(float(feedback))
            self.pwm_data.append(float(pwm))
        except Exception:
            pass

    def update_plot(self):
        self.line_setpoint.set_data(self.time_data, self.setpoint_data)
        self.line_feedback.set_data(self.time_data, self.feedback_data)
        self.line_pwm.set_data(self.time_data, self.pwm_data)

        if len(self.time_data) > 1:
            self.ax.set_xlim(min(self.time_data), max(self.time_data))
        else:
            self.ax.set_xlim(0, 10)

        all_vals = list(self.setpoint_data) + list(self.feedback_data) + list(self.pwm_data)
        if all_vals:
            ymin = min(all_vals) - 50
            ymax = max(all_vals) + 50
            if ymin == ymax:
                ymax = ymin + 1
            self.ax.set_ylim(ymin, ymax)
        else:
            self.ax.set_ylim(0, 4095)

        self.canvas.draw()
        self.root.after(200, self.update_plot)


if __name__ == "__main__":
    root = tk.Tk()
    app = STM32MonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.disconnect_serial(), root.destroy()))
    root.mainloop()
