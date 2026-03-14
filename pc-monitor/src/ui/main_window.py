import tkinter as tk
from tkinter import PhotoImage

from src.services.monitor_service import MonitorService
from src.ui.dialogs import show_error, show_info, show_warning
from src.ui.publish_window import PublishWindow
from src.ui.subscribe_window import SubscribeWindow
from src.ui.ui_constants import LIGHT_PURPLE, TOPIC_VALUES, QOS_VALUES


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Client MQTT v5")
        self.geometry("750x600")
        self.resizable(False, False)
        self.config(padx=50, pady=50, bg=LIGHT_PURPLE)

        self.monitor_service = MonitorService(on_message_callback=self.on_message)
        self.publish_window = None
        self.subscribe_window = None

        self._build_menu()
        self._build_main_ui()

    def _build_menu(self):
        menubar = tk.Menu(self)
        file_menu = tk.Menu(menubar, tearoff=0)

        file_menu.add_command(label="Connect", command=self.connect)
        file_menu.add_command(label="Disconnect", command=self.disconnect)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)

        menubar.add_cascade(label="File", menu=file_menu)
        self.config(menu=menubar)

    def _build_main_ui(self):
        try:
            mqtt_img = PhotoImage(file="mqtt_logo__.png")
            canvas = tk.Canvas(self, width=230, height=190, bg=LIGHT_PURPLE, highlightthickness=0)
            canvas.create_image(100, 100, image=mqtt_img)
            canvas.image = mqtt_img
            canvas.grid(row=0, column=3, columnspan=2, pady=(10, 10))
        except Exception as e:
            show_warning("Image Error", f"Imaginea nu s-a putut încărca: {e}")

        self.frame_login = tk.LabelFrame(self, text="Login", bg=LIGHT_PURPLE, padx=5, pady=5, font=("Arial", 14))
        self.frame_login.grid(row=2, column=0, columnspan=10, sticky="n", pady=(10, 20))

        tk.Label(self.frame_login, text="Adresa Broker:", bg=LIGHT_PURPLE, font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
        self.broker_entry = tk.Entry(self.frame_login)
        self.broker_entry.insert(0, "localhost")
        self.broker_entry.grid(row=0, column=1, padx=10, pady=10)

        tk.Label(self.frame_login, text="Broker Port:", bg=LIGHT_PURPLE, font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10)
        self.port_entry = tk.Entry(self.frame_login)
        self.port_entry.insert(0, "1883")
        self.port_entry.grid(row=1, column=1, padx=10, pady=10)

        tk.Label(self.frame_login, text="ID Client:", bg=LIGHT_PURPLE, font=("Arial", 12)).grid(row=2, column=0, padx=10, pady=10)
        self.client_id_entry = tk.Entry(self.frame_login)
        self.client_id_entry.insert(0, "mqtt")
        self.client_id_entry.grid(row=2, column=1, padx=10, pady=10)

        tk.Label(self.frame_login, text="Username:", bg=LIGHT_PURPLE, font=("Arial", 12)).grid(row=0, column=3, padx=10, pady=10)
        self.username_entry = tk.Entry(self.frame_login)
        self.username_entry.grid(row=0, column=5, padx=10, pady=10)

        tk.Label(self.frame_login, text="Password:", bg=LIGHT_PURPLE, font=("Arial", 12)).grid(row=1, column=3, padx=10, pady=10)
        self.password_entry = tk.Entry(self.frame_login, show="*")
        self.password_entry.grid(row=1, column=5, padx=10, pady=10)

        tk.Label(self, text="Last Will Topic:", bg=LIGHT_PURPLE, font=("Arial", 12)).place(x=5, y=400)
        self.topic_var = tk.StringVar(self)
        self.topic_var.set(TOPIC_VALUES[0])
        tk.OptionMenu(self, self.topic_var, *TOPIC_VALUES).place(x=120, y=395)

        tk.Label(self, text="QoS:", bg=LIGHT_PURPLE, font=("Arial", 12)).place(x=290, y=400)
        self.qos_var = tk.StringVar(self)
        self.qos_var.set(str(QOS_VALUES[0]))
        tk.OptionMenu(self, self.qos_var, *QOS_VALUES).place(x=330, y=395)

        tk.Label(self, text="Message:", bg=LIGHT_PURPLE, font=("Arial", 12)).place(x=430, y=400)
        self.last_will_text = tk.Text(self, height=1, width=25, font=("Arial", 12))
        self.last_will_text.place(x=500, y=398)

        tk.Button(self, text="Publish", font=("Arial", 18), command=self.open_publish_window).grid(row=3, column=0, padx=5, pady=(50, 5))
        tk.Button(self, text="Subscribe", font=("Arial", 18), command=self.open_subscribe_window).grid(row=3, column=3, padx=5, pady=(50, 5))

        tk.Button(self.frame_login, text="Connect", font=("Arial", 10), bg=LIGHT_PURPLE, command=self.connect).grid(row=2, column=3, pady=5)
        tk.Button(self.frame_login, text="Disconnect", font=("Arial", 10), bg=LIGHT_PURPLE, command=self.disconnect).grid(row=2, column=5, pady=5)

    def connect(self):
        broker_address = self.broker_entry.get().strip()
        broker_port = self.port_entry.get().strip()
        client_id = self.client_id_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not broker_address or not broker_port or not client_id or not username or not password:
            show_error("Error", "Toate câmpurile trebuie completate.")
            return

        try:
            broker_port = int(broker_port)
        except ValueError:
            show_error("Error", "Portul brokerului trebuie să fie numeric.")
            return

        selected_topic = self.topic_var.get()
        selected_qos = self.qos_var.get()
        message = self.last_will_text.get("1.0", "end-1c")

        last_will_topic = selected_topic if selected_topic != "Select" else "Cpu load"
        last_will_message = message if message else "Clientul s-a deconectat."
        last_will_qos = int(selected_qos) if selected_qos != "Select" else 0

        try:
            self.monitor_service.connect(
                broker_address=broker_address,
                broker_port=broker_port,
                client_id=client_id,
                username=username,
                password=password,
                last_will_topic=last_will_topic,
                last_will_message=last_will_message,
                last_will_qos=last_will_qos,
                last_will_retain=False,
            )
            show_info("Connected", "Successfully connected to the broker!")
        except Exception as e:
            show_error("Connection Error", f"Failed to connect to the broker: {e}")

    def disconnect(self):
        try:
            self.monitor_service.disconnect()
            show_info("Disconnect", "Successfully disconnected from the broker.")
        except Exception as e:
            show_error("Disconnect Error", f"Failed to disconnect: {e}")

    def open_publish_window(self):
        if self.publish_window is None or not self.publish_window.winfo_exists():
            self.publish_window = PublishWindow(self, self.monitor_service)
        else:
            self.publish_window.lift()

    def open_subscribe_window(self):
        if self.subscribe_window is None or not self.subscribe_window.winfo_exists():
            self.subscribe_window = SubscribeWindow(self, self.monitor_service)
        else:
            self.subscribe_window.lift()

    def on_message(self, topic, message):
        if self.subscribe_window and self.subscribe_window.winfo_exists():
            self.subscribe_window.append_message(topic, message)

    def exit_app(self):
        self.destroy()