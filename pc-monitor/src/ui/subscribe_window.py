import tkinter as tk

from src.ui.dialogs import show_error, show_info, show_warning
from src.ui.ui_constants import LIGHT_PURPLE, TOPIC_VALUES, QOS_VALUES


class SubscribeWindow(tk.Toplevel):
    def __init__(self, parent, monitor_service):
        super().__init__(parent)
        self.monitor_service = monitor_service

        self.geometry("700x500")
        self.title("Client MQTT - Subscriber")
        self.config(padx=50, pady=50, bg=LIGHT_PURPLE)

        self.subscriptions = {
            "Cpu load": {0: "UNSUBSCRIBED", 1: "UNSUBSCRIBED", 2: "UNSUBSCRIBED"},
            "Memory usage": {0: "UNSUBSCRIBED", 1: "UNSUBSCRIBED", 2: "UNSUBSCRIBED"},
            "Disk usage": {0: "UNSUBSCRIBED", 1: "UNSUBSCRIBED", 2: "UNSUBSCRIBED"},
        }

        tk.Label(self, text="Topic:", bg=LIGHT_PURPLE, font=("Arial", 18)).place(x=5, y=5)
        self.topic_var = tk.StringVar(self)
        self.topic_var.set(TOPIC_VALUES[0])
        tk.OptionMenu(self, self.topic_var, *TOPIC_VALUES, command=self.update_status).place(x=125, y=2)

        tk.Label(self, text="QoS:", bg=LIGHT_PURPLE, font=("Arial", 16)).place(x=5, y=55)
        self.qos_var = tk.StringVar(self)
        self.qos_var.set(str(QOS_VALUES[0]))
        tk.OptionMenu(self, self.qos_var, *QOS_VALUES, command=self.update_status).place(x=123, y=45)

        tk.Label(self, text="Message:", bg=LIGHT_PURPLE, font=("Arial", 16)).place(x=5, y=110)
        self.textbox = tk.Text(self, height=6, font=("Arial", 16))
        self.textbox.place(x=125, y=95)

        tk.Label(self, text="Status:", bg=LIGHT_PURPLE, font=("Arial", 16)).place(x=5, y=230)
        self.status_label = tk.Label(self, text="UNSUBSCRIBED", font=("Arial", 12), width=20, height=2)
        self.status_label.place(x=125, y=225)

        tk.Button(self, text="Subscribe", command=self.subscribe_to_topic, font=("Arial", 15), width=25).place(x=5, y=330)
        tk.Button(self, text="Unsubscribe", command=self.unsubscribe_to_topic, font=("Arial", 15), width=25).place(x=300, y=330)

    def update_status(self, *args):
        topic = self.topic_var.get()
        qos = self.qos_var.get()

        try:
            qos = int(qos)
            current_status = self.subscriptions[topic][qos]
            self.status_label.config(text=current_status)
        except Exception:
            self.status_label.config(text="UNSUBSCRIBED")

    def subscribe_to_topic(self):
        topic = self.topic_var.get()
        qos = self.qos_var.get()

        if topic == "Select":
            show_warning("Invalid Input", "Vă rugăm să selectați un topic.")
            return

        if qos == "Select":
            show_warning("Invalid Input", "Vă rugăm să selectați un QoS.")
            return

        qos = int(qos)

        if self.subscriptions[topic][qos] == "SUBSCRIBED":
            show_warning("Subscribe", "Sunteți deja abonat la acest topic.")
            return

        try:
            self.monitor_service.subscribe(topic, qos)
            self.subscriptions[topic][qos] = "SUBSCRIBED"
            self.status_label.config(text="SUBSCRIBED")
            show_info("Subscribe Status", f"Subscribed to {topic}.")
        except Exception as e:
            show_error("Subscribe Error", f"Error subscribing: {e}")

    def unsubscribe_to_topic(self):
        topic = self.topic_var.get()
        qos = self.qos_var.get()

        if topic == "Select":
            show_warning("Invalid Input", "Vă rugăm să selectați un topic.")
            return

        if qos == "Select":
            show_warning("Invalid Input", "Vă rugăm să selectați un QoS.")
            return

        qos = int(qos)

        try:
            self.monitor_service.unsubscribe(topic)
            self.subscriptions[topic][qos] = "UNSUBSCRIBED"
            self.status_label.config(text="UNSUBSCRIBED")
            show_info("Unsubscribe Status", f"Unsubscribed from {topic}.")
        except Exception as e:
            show_error("Unsubscribe Error", f"Error unsubscribing: {e}")

    def append_message(self, topic, message):
        self.textbox.insert("end", f"[{topic}] {message}\n")