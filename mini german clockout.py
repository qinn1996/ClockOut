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

        # Hauptlayout
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.add(vbox)

        # Zeitmodus wählen (ohne Fokus-Indikator)
        self.radio_time = Gtk.RadioButton(label="Uhrzeit setzen")
        self.radio_time.set_can_focus(False)
        self.radio_time.connect("toggled", self.toggle_input_fields)
        self.radio_duration = Gtk.RadioButton.new_with_label_from_widget(self.radio_time, "Zeitspanne setzen")
        self.radio_duration.set_can_focus(False)
        vbox.pack_start(self.radio_time, False, False, 0)
        vbox.pack_start(self.radio_duration, False, False, 0)

        # Eingabefelder
        self.entry_time = Gtk.Entry()
        self.entry_time.set_placeholder_text("HH:MM (24h-Format)")
        self.entry_time.connect("activate", self.schedule_shutdown)
        vbox.pack_start(self.entry_time, False, False, 0)

        self.entry_duration = Gtk.Entry()
        self.entry_duration.set_placeholder_text("MM oder HH:MM")
        self.entry_duration.connect("activate", self.schedule_shutdown)
        vbox.pack_start(self.entry_duration, False, False, 0)

        # Planungs-Button
        self.button_schedule = Gtk.Button(label="Herunterfahren planen")
        self.button_schedule.set_can_default(True)
        self.button_schedule.grab_default()
        self.button_schedule.connect("clicked", self.schedule_shutdown)
        vbox.pack_start(self.button_schedule, False, False, 0)

        # Statusanzeige
        self.label_status = Gtk.Label(label="")
        vbox.pack_start(self.label_status, False, False, 0)

        # Versionstext
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

            # UI-Nachricht für Zeitangabe
            hours_str = "einer Stunde" if hours == 1 else f"{hours} Stunden" if hours > 0 else ""
            minutes_str = "einer Minute" if minutes == 1 else f"{minutes} Minuten" if minutes > 0 else ""
            
            if hours and minutes:
                ui_message = f"✅ Shutdown in {hours_str} \nund {minutes_str} geplant."
            elif hours:
                ui_message = f"✅ Shutdown in {hours_str} \n geplant."
            else:
                ui_message = f"✅ Shutdown in {minutes_str}\n geplant."

            # Notification ohne Emoji
            notification_message = ui_message.replace("✅ ", "").replace("\n","")
            self.execute_shutdown(delay_seconds, ui_message, notification_message)

        except ValueError:
            error_msg = "❌ Ungültige Eingabe!"
            notification_msg = "Ungültige Uhrzeit! Format: HH:MM"
            if self.shutdown_scheduled:
                self.cancel_shutdown()
                error_msg = "❌ Shutdown abgebrochen!\n" + error_msg
                notification_msg = "Shutdown abgebrochen: " + notification_msg
            self.label_status.set_text(error_msg)
            self.send_notification("Fehler", notification_msg)

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

            # Datumsformatierung
            days_diff = (shutdown_date - now_date).days
            if days_diff == 0:
                time_str = shutdown_datetime.strftime("%H:%M Uhr.")
                date_str = "\num " + time_str
            elif days_diff == 1:
                time_str = shutdown_datetime.strftime("%H:%M Uhr.")
                date_str = "\nmorgen um " + time_str
            else:
                date_str = shutdown_datetime.strftime("am \n%d.%m.%Y um %H:%M Uhr.")

            # UI-Nachricht mit Emoji
            ui_message = f"✅ Shutdown erfolgt {date_str}"
            notification_message = ui_message.replace("✅ ", "").replace("\n", "")
                        
            self.execute_shutdown(total_minutes*60, ui_message, notification_message)

        except ValueError:
            error_msg = "❌ Ungültige Eingabe!"
            notification_msg = "Ungültige Eingabe! Verwende Minuten (z.B. 90) oder Stunden:Minuten (z.B. 1:30)."
            if self.shutdown_scheduled:
                self.cancel_shutdown()
                error_msg = "❌ Shutdown abgebrochen!\n" + error_msg
                notification_msg = "Shutdown abgebrochen: " + notification_msg
            self.label_status.set_text(error_msg)
            self.send_notification("Fehler", notification_msg)

    def execute_shutdown(self, delay_seconds, ui_message, notification_message):
        try:
            subprocess.run(["shutdown", "-h", f"+{delay_seconds//60}"], check=True)
            self.shutdown_scheduled = True
            self.label_status.set_text(ui_message)
            self.send_notification("Shutdown geplant", notification_message)
        except subprocess.CalledProcessError:
            self.shutdown_scheduled = False
            self.label_status.set_text("⚠️ Fehler beim Shutdown-Befehl!")
            self.send_notification("Fehler", "Fehler beim Shutdown-Befehl!")

    def cancel_shutdown(self):
        try:
            subprocess.run(["shutdown", "-c"], check=True)
            self.shutdown_scheduled = False
        except subprocess.CalledProcessError:
            pass

    def on_destroy(self, widget):
        if self.shutdown_scheduled:
            self.cancel_shutdown()
            self.send_notification("Shutdown abgebrochen", "Der geplante Shutdown wurde abgebrochen.")
        Gtk.main_quit()

    def send_notification(self, title, message):
        try:
            subprocess.run(["notify-send", title, message], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Senden der Notification: {e}")

win = ShutdownApp()
win.show_all()
Gtk.main()
