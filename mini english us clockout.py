#!/usr/bin/env python3
import gi
import subprocess
from datetime import datetime, timedelta

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Pango

class ShutdownApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="ClockOut")
        self.set_border_width(10)
        self.set_default_size(300, 200)
        self.shutdown_scheduled = False

        # Main layout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Time mode selection (without focus indicator)
        self.radio_time = Gtk.RadioButton(label="Set time")
        self.radio_time.set_can_focus(False)
        self.radio_time.connect("toggled", self.toggle_input_fields)
        self.radio_duration = Gtk.RadioButton.new_with_label_from_widget(self.radio_time, "Set duration")
        self.radio_duration.set_can_focus(False)
        vbox.pack_start(self.radio_time, False, False, 0)
        vbox.pack_start(self.radio_duration, False, False, 0)

        # Input fields
        self.entry_time = Gtk.Entry()
        self.entry_time.set_placeholder_text("HH:MM (24-hour format)")
        self.entry_time.connect("activate", self.schedule_shutdown)
        vbox.pack_start(self.entry_time, False, False, 0)

        self.entry_duration = Gtk.Entry()
        self.entry_duration.set_placeholder_text("MM or HH:MM")
        self.entry_duration.connect("activate", self.schedule_shutdown)
        vbox.pack_start(self.entry_duration, False, False, 0)

        # Schedule button
        self.button_schedule = Gtk.Button(label="Schedule Shutdown")
        self.button_schedule.set_can_default(True)
        self.button_schedule.grab_default()
        self.button_schedule.connect("clicked", self.schedule_shutdown)
        vbox.pack_start(self.button_schedule, False, False, 0)

        # Status display
        self.label_status = Gtk.Label(label="")
        vbox.pack_start(self.label_status, False, False, 0)

        # Version text
        version_label = Gtk.Label(label="v. 1.1, Jean P. König")
        version_label.set_halign(Gtk.Align.END)
        version_label.set_margin_end(5)
        version_label.set_margin_bottom(5)
        font_desc = Pango.FontDescription("8")
        version_label.override_font(font_desc)
        vbox.pack_end(version_label, False, False, 0)

        self.connect("destroy", self.on_destroy)
        self.entry_duration.set_visible(False)
        self.radio_time.set_active(True)
        GLib.idle_add(self.toggle_input_fields)
        self.show_all()

    def toggle_input_fields(self, widget=None):
        if self.radio_time.get_active():
            self.entry_time.set_visible(True)
            self.entry_duration.set_visible(False)
        else:
            self.entry_time.set_visible(False)
            self.entry_duration.set_visible(True)

    def schedule_shutdown(self, widget):
        if self.radio_time.get_active():
            self.schedule_by_time()
        else:
            self.schedule_by_duration()

    def schedule_by_time(self):
        shutdown_time_str = self.entry_time.get_text()
        try:
            shutdown_time = datetime.strptime(shutdown_time_str, "%H:%M").time()
            now = datetime.now()
            shutdown_datetime = datetime.combine(now.date(), shutdown_time)

            if shutdown_datetime < now:
                shutdown_datetime += timedelta(days=1)

            delay_seconds = int((shutdown_datetime - now).total_seconds())
            hours, remainder = divmod(delay_seconds, 3600)
            minutes = remainder // 60

            # UI message for time input
            hours_str = "one hour" if hours == 1 else f"{hours} hours" if hours > 0 else ""
            minutes_str = "one minute" if minutes == 1 else f"{minutes} minutes" if minutes > 0 else ""
            
            if hours and minutes:
                ui_message = f"✅ Shutdown in {hours_str} \nand {minutes_str}."
            elif hours:
                ui_message = f"✅ Shutdown in {hours_str}."
            else:
                ui_message = f"✅ Shutdown in {minutes_str}."

            # Notification without emoji
            notification_message = ui_message.replace("✅ ", "").replace("\n","")
            self.execute_shutdown(delay_seconds, ui_message, notification_message)

        except ValueError:
            error_msg = "❌ Invalid input!"
            notification_msg = "Invalid time! Format: HH:MM"
            if self.shutdown_scheduled:
                self.cancel_shutdown()
                error_msg = "❌ Shutdown canceled!\n" + error_msg
                notification_msg = "Shutdown canceled: " + notification_msg
            self.label_status.set_text(error_msg)
            self.send_notification("Error", notification_msg)

    def schedule_by_duration(self):
        input_str = self.entry_duration.get_text()
        try:
            if ":" in input_str:
                parts = input_str.split(":")
                if len(parts) != 2:
                    raise ValueError
                hours = int(parts[0])
                minutes = int(parts[1])
                if hours < 0 or minutes < 0 or minutes >= 60:
                    raise ValueError
                total_minutes = hours * 60 + minutes
            else:
                total_minutes = int(input_str)
            
            if total_minutes <= 0:
                raise ValueError

            shutdown_datetime = datetime.now() + timedelta(minutes=total_minutes)
            now_date = datetime.now().date()
            shutdown_date = shutdown_datetime.date()

            # Date formatting
            days_diff = (shutdown_date - now_date).days
            if days_diff == 0:
                time_str = shutdown_datetime.strftime("%H:%M")
                date_str = "\nfor " + time_str
            elif days_diff == 1:
                time_str = shutdown_datetime.strftime("%H:%M")
                date_str = "\nfor tomorrow " + time_str
            else:
                date_str = shutdown_datetime.strftime("for \n%m/%d/%Y at %H:%M")

            # UI message with emoji
            ui_message = f"✅ Shutdown scheduled {date_str}"
            notification_message = ui_message.replace("✅ ", "").replace("\n", "")
                        
            self.execute_shutdown(total_minutes*60, ui_message, notification_message)

        except ValueError:
            error_msg = "❌ Invalid input!"
            notification_msg = "Invalid input! Use minutes (e.g. 90) or hours:minutes (e.g. 1:30)."
            if self.shutdown_scheduled:
                self.cancel_shutdown()
                error_msg = "❌ Shutdown canceled!\n" + error_msg
                notification_msg = "Shutdown canceled: " + notification_msg
            self.label_status.set_text(error_msg)
            self.send_notification("Error", notification_msg)

    def execute_shutdown(self, delay_seconds, ui_message, notification_message):
        try:
            subprocess.run(["shutdown", "-h", f"+{delay_seconds//60}"], check=True)
            self.shutdown_scheduled = True
            self.label_status.set_text(ui_message)
            self.send_notification("Shutdown Scheduled", notification_message)
        except subprocess.CalledProcessError:
            self.shutdown_scheduled = False
            self.label_status.set_text("⚠️ Shutdown command error!")
            self.send_notification("Error", "Shutdown command failed!")

    def cancel_shutdown(self):
        try:
            subprocess.run(["shutdown", "-c"], check=True)
            self.shutdown_scheduled = False
        except subprocess.CalledProcessError:
            pass

    def on_destroy(self, widget):
        if self.shutdown_scheduled:
            self.cancel_shutdown()
            self.send_notification("Shutdown canceled", "Scheduled shutdown has been canceled.")
        Gtk.main_quit()

    def send_notification(self, title, message):
        try:
            subprocess.run(["notify-send", title, message], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Notification error: {e}")

win = ShutdownApp()
win.show_all()
Gtk.main()
