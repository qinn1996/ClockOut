#!/usr/bin/env python3
import gi
import subprocess
import os
from datetime import datetime, timedelta

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

class ShutdownApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="ClockOut")
        self.set_border_width(10)
        self.set_default_size(300, 200)
        self.shutdown_scheduled = False
        self.progress_timeout_id = None
        self.total_seconds = 0
        self.start_time = None
        self.icon_right_margin = 40

        # Get paths
        script_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(script_dir, "clockoutbg.png")
        enter_path = os.path.join(script_dir, "enter.png")

        # Load background
        pixbuf = GdkPixbuf.Pixbuf.new_from_file(image_path)
        scaled_pixbuf = pixbuf.scale_simple(
            pixbuf.get_width() // 1.5, pixbuf.get_height() // 1.5, GdkPixbuf.InterpType.BILINEAR
        )
        self.background = Gtk.Image.new_from_pixbuf(scaled_pixbuf)

        # Load and scale enter icon
        enter_pixbuf = GdkPixbuf.Pixbuf.new_from_file(enter_path)
        scaled_enter = enter_pixbuf.scale_simple(
            enter_pixbuf.get_width() // 2,
            enter_pixbuf.get_height() // 2,
            GdkPixbuf.InterpType.BILINEAR
        )

        # Theme-based color inversion
        style_context = self.get_style_context()
        success, bg_color = style_context.lookup_color('theme_bg_color')
        if success and (0.2126 * bg_color.red + 0.7152 * bg_color.green + 0.0722 * bg_color.blue) <= 0.5:
            scaled_enter = self.invert_pixbuf(scaled_enter)

        enter_icon = Gtk.Image.new_from_pixbuf(scaled_enter)
        enter_icon.set_margin_end(self.icon_right_margin)

        # EventBox for transparency
        self.event_box = Gtk.EventBox()
        self.event_box.add(self.background)
        
        # Theme brightness
        self.event_box.set_opacity(0.06 if success and (0.2126 * bg_color.red + 0.7152 * bg_color.green + 0.0722 * bg_color.blue) > 0.5 else 0.11)

        # Main layout
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.vbox.set_halign(Gtk.Align.CENTER)
        self.vbox.set_valign(Gtk.Align.CENTER)

        # Progress bar
        self.progress = Gtk.ProgressBar()
        self.progress.set_hexpand(True)
        self.progress.set_size_request(-1, 3)
        self.progress.get_style_context().add_class("gtk-progress-bar")
        self.progress.set_no_show_all(True)

        # UI elements
        self.overlay = Gtk.Overlay()
        self.add(self.overlay)
        self.overlay.add(self.event_box)
        self.overlay.add_overlay(self.vbox)

        # Deaktiviere Fokus-Rahmen für Radio-Buttons
        self.radio_time = Gtk.RadioButton(label="Uhrzeit setzen")
        self.radio_time.set_can_focus(False)
        self.radio_duration = Gtk.RadioButton.new_with_label_from_widget(self.radio_time, "Zeitspanne setzen")
        self.radio_duration.set_can_focus(False)
        
        self.entry_time = Gtk.Entry(placeholder_text="HH:MM (24h-Format)")
        self.entry_duration = Gtk.Entry(placeholder_text="Minuten (MM) o. Stunden (HH:MM)")
        
        # Button with adjusted spacing
        button_box = Gtk.Box(spacing=10)
        button_label = Gtk.Label(label="         Herunterfahren planen")
        button_box.pack_start(button_label, False, False, 0)
        button_box.pack_start(enter_icon, False, False, 0)
        self.button_schedule = Gtk.Button()
        self.button_schedule.add(button_box)
        
        self.label_status = Gtk.Label()

        # Über-Button
        self.about_button = Gtk.Button(label="Über")
        self.about_button.connect("clicked", self.show_about_dialog)
        self.about_button.set_margin_top(10)
        self.about_button.set_halign(Gtk.Align.CENTER)
        self.about_button.set_valign(Gtk.Align.END)

        # Assemble UI
        for widget in [self.radio_time, self.radio_duration, self.entry_time, 
                      self.entry_duration, self.button_schedule, self.label_status]:
            self.vbox.pack_start(widget, False, False, 0)
        
        self.vbox.pack_start(self.progress, False, False, 5)
        self.vbox.pack_end(self.about_button, False, False, 5)

        # Signal connections
        self.radio_time.connect("toggled", self.toggle_input_fields)
        self.entry_time.connect("activate", self.schedule_shutdown)
        self.entry_duration.connect("activate", self.schedule_shutdown)
        self.button_schedule.connect("clicked", self.schedule_shutdown)
        self.connect("destroy", self.on_destroy)

        # Initialization
        self.entry_duration.set_visible(False)
        self.radio_time.set_active(True)
        GLib.idle_add(self.toggle_input_fields)
        self.show_all()
        self.progress.hide()

    def show_about_dialog(self, widget):
        about_dialog = Gtk.Dialog(
            title="Über ClockOut",
            parent=self,
            flags=Gtk.DialogFlags.MODAL
        )
        about_dialog.set_default_size(300, 250)
        
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content.set_border_width(20)
        
        # Logo laden und skalieren
        script_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(script_dir, "clockout.png")
        if os.path.exists(logo_path):
            logo_pixbuf = GdkPixbuf.Pixbuf.new_from_file(logo_path)
            scaled_logo = logo_pixbuf.scale_simple(
                int(logo_pixbuf.get_width() * 0.1),
                int(logo_pixbuf.get_height() * 0.1),
                GdkPixbuf.InterpType.BILINEAR
            )
            logo_image = Gtk.Image.new_from_pixbuf(scaled_logo)
            logo_box = Gtk.Box()
            logo_box.set_halign(Gtk.Align.CENTER)
            logo_box.pack_start(logo_image, False, False, 0)
            content.pack_start(logo_box, False, False, 10)

        labels = [
            Gtk.Label(label="ClockOut, v. 1.1"),
            Gtk.Label(label="\nJean P. König, 2025"),
            ]
        
        # Icon Credit in einer Zeile
        icon_credit_box = Gtk.Box(spacing=5)
        icon_credit_box.set_halign(Gtk.Align.CENTER)
        icon_label = Gtk.Label(label="Eingabe-Symbol von")
        link_label = Gtk.Label()
        link_label.set_markup('<a href="https://icons8.com/" title="besuche icons8.com">icons8</a>')
        
        icon_credit_box.pack_start(icon_label, False, False, 0)
        icon_credit_box.pack_start(link_label, False, False, 0)
        
        for label in labels:
            content.pack_start(label, False, False, 0)
        content.pack_start(icon_credit_box, False, False, 5)

        # Dialog-Buttons
        close_button = Gtk.Button.new_with_label("Schließen")
        close_button.connect("clicked", lambda x: about_dialog.destroy())
        about_dialog.get_content_area().add(content)
        about_dialog.get_content_area().pack_end(close_button, False, False, 10)
        
        about_dialog.show_all()

    def invert_pixbuf(self, pixbuf):
        # Convert pixbuf to mutable byte array
        pixels = bytearray(pixbuf.get_pixels())
        n_channels = pixbuf.get_n_channels()
        rowstride = pixbuf.get_rowstride()

        # Invert colors
        for y in range(pixbuf.get_height()):
            for x in range(pixbuf.get_width()):
                offset = y * rowstride + x * n_channels
                if offset + 2 < len(pixels):
                    pixels[offset] = 255 - pixels[offset]     # Red
                    pixels[offset+1] = 255 - pixels[offset+1] # Green
                    pixels[offset+2] = 255 - pixels[offset+2] # Blue

        # Create new pixbuf from modified data
        return GdkPixbuf.Pixbuf.new_from_bytes(
            GLib.Bytes.new(pixels),
            pixbuf.get_colorspace(),
            pixbuf.get_has_alpha(),
            pixbuf.get_bits_per_sample(),
            pixbuf.get_width(),
            pixbuf.get_height(),
            rowstride
        )

    def toggle_input_fields(self, widget=None):
        if self.radio_time.get_active():
            self.entry_time.show()
            self.entry_duration.hide()
        else:
            self.entry_time.hide()
            self.entry_duration.show()

    def schedule_shutdown(self, widget):
        if self.radio_time.get_active():
            self.schedule_by_time()
        else:
            self.schedule_by_duration()

    def schedule_by_time(self):
        try:
            shutdown_time = datetime.strptime(self.entry_time.get_text(), "%H:%M").time()
            now = datetime.now()
            shutdown_datetime = datetime.combine(now.date(), shutdown_time)
            
            if shutdown_datetime < now:
                shutdown_datetime += timedelta(days=1)
            
            self.total_seconds = int((shutdown_datetime - now).total_seconds())
            self.start_progress(shutdown_datetime)
            self.execute_shutdown(self.total_seconds, self.format_time_string(self.total_seconds))
            
        except ValueError:
            self.show_error("❌ Ungültige Eingabe!", "Ungültige Uhrzeit! Format: HH:MM")

    def schedule_by_duration(self):
        try:
            input_str = self.entry_duration.get_text()
            if ":" in input_str:
                hours, minutes = map(int, input_str.split(":", 1))
                if hours < 0 or minutes < 0 or minutes >= 60:
                    raise ValueError
                total_minutes = hours * 60 + minutes
            else:
                total_minutes = int(input_str)
            
            if total_minutes <= 0:
                raise ValueError
            
            self.total_seconds = total_minutes * 60
            shutdown_datetime = datetime.now() + timedelta(seconds=self.total_seconds)
            self.start_progress(shutdown_datetime)
            self.execute_shutdown(self.total_seconds, self.format_datetime_string(shutdown_datetime))
            
        except ValueError:
            self.show_error("❌ Ungültige Eingabe!", 
                           "Ungültiges Format! Verwende Minuten (z.B. 90) oder Stunden:Minuten (z.B. 1:30).")

    def start_progress(self, end_time):
        self.progress.set_fraction(1.0)
        self.progress.show()
        self.start_time = datetime.now()
        
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)
        self.progress_timeout_id = GLib.timeout_add_seconds(1, self.update_progress, end_time)

    def update_progress(self, end_time):
        remaining = (end_time - datetime.now()).total_seconds()
        if remaining <= 0:
            self.progress.set_fraction(0.0)
            self.progress.hide()
            return False
        
        progress = 1 - (self.total_seconds - remaining) / self.total_seconds
        self.progress.set_fraction(max(0.0, progress))
        return True

    def format_time_string(self, seconds):
        minutes_total = seconds // 60
        if minutes_total == 1:
            return "✅ Shutdown in einer Minute geplant."
        if minutes_total == 60:
            return "✅ Shutdown in einer Stunde geplant."
        
        if minutes_total > 60:
            hours, mins = divmod(minutes_total, 60)
            hours_str = "einer Stunde" if hours == 1 else f"{hours} Stunden"
            mins_str = "einer Minute" if mins == 1 else f"{mins} Minuten" if mins > 0 else ""
            return f"✅ Shutdown in {hours_str}\n{' und ' + mins_str if mins_str else ''} geplant."
        
        return f"✅ Shutdown in {minutes_total} Minuten geplant."

    def format_datetime_string(self, dt):
        now = datetime.now()
        delta_days = (dt.date() - now.date()).days
        
        if delta_days == 1:
            return f"✅ Shutdown erfolgt \nmorgenum {dt.strftime('%H:%M Uhr')}."
        elif delta_days > 1:
            return f"✅ Shutdown erfolgt am \n{dt.strftime('%d.%m.%Y um %H:%M Uhr')}."
        else:
            return f"✅ Shutdown erfolgt um {dt.strftime('%H:%M Uhr')}."

    def execute_shutdown(self, delay_seconds, shutdown_str):
        try:
            subprocess.run(["shutdown", "-h", f"+{delay_seconds//60}"], check=True)
            self.shutdown_scheduled = True
            self.label_status.set_text(shutdown_str)
            self.send_notification("Shutdown geplant", shutdown_str.replace("✅ ", "").replace("\n", "").strip())
        except subprocess.CalledProcessError:
            self.show_error("⚠️ Fehler beim Shutdown-Befehl!", "Fehler beim Shutdown-Befehl!")

    def show_error(self, text, notification_msg):
        # Bestehenden Shutdown abbrechen
        if self.shutdown_scheduled:
            subprocess.run(["shutdown", "-c"], check=True)
            self.shutdown_scheduled = False
            text = "❌ Shutdown abgebrochen!\n" + "❌ " + text.split(" ", 1)[-1]
            notification_msg = "Shutdown abgebrochen: " + notification_msg

        self.label_status.set_text(text)
        self.send_notification("Fehler", notification_msg)
        self.progress.hide()
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)

    def on_destroy(self, widget):
        if self.shutdown_scheduled:
            subprocess.run(["shutdown", "-c"], check=True)
            self.send_notification("Shutdown abgebrochen", "Der geplante Shutdown wurde abgebrochen.")
        if self.progress_timeout_id:
            GLib.source_remove(self.progress_timeout_id)
        Gtk.main_quit()

    def send_notification(self, title, message):
        try:
            subprocess.run(["notify-send", title, message], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Fehler beim Senden der Notification: {e}")

win = ShutdownApp()
win.show_all()
Gtk.main()
