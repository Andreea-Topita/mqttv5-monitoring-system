import tkinter as tk

from src.ui.dialogs import show_error, show_info, show_warning
from src.ui.ui_constants import LIGHT_PURPLE, TOPIC_VALUES, QOS_VALUES


class PublishWindow(tk.Toplevel):
    def __init__(self, parent, monitor_service):
        super().__init__(parent)
        self.monitor_service = monitor_service

        self.geometry("700x500")
        self.title("Client MQTT - Publisher")
        self.config(padx=50, pady=50, bg=LIGHT_PURPLE)

        tk.Label(self, text="Topic:", bg=LIGHT_PURPLE, font=("Arial", 18)).place(x=5, y=5)
        self.topic_var = tk.StringVar(self)
        self.topic_var.set(TOPIC_VALUES[0])
        tk.OptionMenu(self, self.topic_var, *TOPIC_VALUES).place(x=125, y=2)

        tk.Label(self, text="QoS:", bg=LIGHT_PURPLE, font=("Arial", 16)).place(x=5, y=55)
        self.qos_var = tk.StringVar(self)
        self.qos_var.set(str(QOS_VALUES[0]))
        tk.OptionMenu(self, self.qos_var, *QOS_VALUES).place(x=123, y=45)

        tk.Label(self, text="Published message:", bg=LIGHT_PURPLE, font=("Arial", 15)).place(x=5, y=116)
        self.textbox = tk.Text(self, height=5, font=("Arial", 15))
        self.textbox.place(x=180, y=102)

        tk.Button(self, text="Publish", font=("Arial", 17), command=self.publish_message).place(x=10, y=230)
        tk.Button(self, text="Start Periodic Publish", command=self.start_periodic_publishing).place(x=10, y=320)
        tk.Button(self, text="Stop Periodic Publish", command=self.stop_periodic_publishing).place(x=200, y=320)

    def publish_message(self):
        topic = self.topic_var.get()
        qos = self.qos_var.get()

        if topic == "Select":
            show_warning("Invalid Input", "Vă rugăm să selectați un topic.")
            return

        if qos == "Select":
            show_warning("Invalid Input", "Vă rugăm să selectați un QoS.")
            return

        try:
            message = self.monitor_service.publish_metric(topic, int(qos))
            self.textbox.insert("end", f"{message}\n")
            show_info("Publish Status", f"Message published to {topic}.")
        except Exception as e:
            show_error("Publish Error", f"Error publishing message: {e}")

    def start_periodic_publishing(self):
        topic = self.topic_var.get()
        qos = self.qos_var.get()

        if topic == "Select" or qos == "Select":
            show_warning("Invalid Input", "Selectați topic și QoS.")
            return

        try:
            self.monitor_service.start_periodic_publish(topic, int(qos), interval=5)
            show_info("Periodic Publish", "Periodic publishing started.")
        except Exception as e:
            show_error("Periodic Publish Error", str(e))

    def stop_periodic_publishing(self):
        self.monitor_service.stop_periodic_publish()
        show_info("Periodic Publish", "Periodic publishing stopped.")