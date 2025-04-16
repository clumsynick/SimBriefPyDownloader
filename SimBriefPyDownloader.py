#!/usr/bin/env python3


import os
import json
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText
import time
from datetime import datetime, timedelta

APP_VERSION = "1.0.1"
CONFIG_PATH = os.path.expanduser("~/.simbrief_downloader_config.json")
SIMBRIEF_API_URL = "https://www.simbrief.com/api/xml.fetcher.php?userid={username}&json=1"
FLIGHTPLAN_BASE_URL = "https://www.simbrief.com/ofp/flightplans/"

class SimBriefPyDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title(f"SimBriefPyDownloader (v{APP_VERSION})")

        # Dark Theme
        self.root.configure(bg="#2b2b2b")
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TLabel", background="#2b2b2b", foreground="#ffffff", font=('Arial', 10))
        style.configure("TButton", background="#3c3f41", foreground="#ffffff", font=('Arial', 10, 'bold'))
        style.configure("TCheckbutton", background="#2b2b2b", foreground="#ffffff")
        style.configure("Horizontal.TProgressbar", troughcolor="#3c3f41", background="#61892f")

        # Flight info display
        self.flight_info_label = ttk.Label(root, text="Flight Info: N/A", font=("Arial", 12, "bold"), foreground="#ffffff")
        self.flight_info_label.grid(row=0, column=0, columnspan=4, sticky='w', padx=5, pady=5)

        # Username
        ttk.Label(root, text="SimBrief ID:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
        self.username_entry = ttk.Entry(root, width=30)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5)

        # Formats
        ttk.Label(root, text="File Formats:").grid(row=2, column=0, sticky='w', padx=5, pady=5)
        self.formats = {
            "PDF": tk.BooleanVar(),
            "FMS": tk.BooleanVar(),
            "FF757": tk.BooleanVar(),
            "FF767": tk.BooleanVar(),
            "XPE": tk.BooleanVar(),
            "TDS": tk.BooleanVar(),
        }
        col = 1
        for fmt, var in self.formats.items():
            ttk.Checkbutton(root, text=fmt, variable=var).grid(row=2, column=col, padx=2, pady=5, sticky='w')
            col += 1

        # Target directories
        ttk.Label(root, text="Target Directory per Format:").grid(row=3, column=0, sticky='w', padx=5, pady=5)
        self.directories = {}
        row = 4
        for fmt in self.formats:
            ttk.Label(root, text=f"{fmt}:").grid(row=row, column=0, sticky='w', padx=5, pady=2)
            entry = ttk.Entry(root, width=40)
            entry.grid(row=row, column=1, padx=5, pady=2)
            browse_btn = ttk.Button(root, text="Browse", command=lambda f=fmt, e=entry: self.select_directory(f, e))
            browse_btn.grid(row=row, column=2, padx=5, pady=2)
            self.directories[fmt] = entry
            row += 1

        # Progressbar
        self.progress = ttk.Progressbar(root, mode='determinate', length=400)
        self.progress.grid(row=row, column=0, columnspan=3, padx=5, pady=10)
        row += 1

        # Console log
        self.console = ScrolledText(root, height=8, bg="#1e1e1e", fg="#ffffff", insertbackground='#ffffff')
        self.console.grid(row=row, column=0, columnspan=4, padx=5, pady=5)
        row += 1

        # Buttons
        save_btn = ttk.Button(root, text="Save Settings", command=self.save_settings)
        save_btn.grid(row=row, column=0, padx=5, pady=10)

        download_btn = ttk.Button(root, text="🚀 Download Flightplan 🚀", command=self.download_flightplan)
        download_btn.grid(row=row, column=1, padx=5, pady=10)

        clean_btn = ttk.Button(root, text="🧹 Clean Old Files", command=self.clean_old_files)
        clean_btn.grid(row=row, column=2, padx=5, pady=10)

        license_btn = ttk.Button(root, text="📄 License (GPL)", command=self.show_license)
        license_btn.grid(row=row, column=3, padx=5, pady=10, sticky='e')

        # Initial load
        self.last_flight_info = self.load_last_flight_info()
        self.load_settings()

    def show_license(self):
        license_text = """
SimBriefPyDownloader - Flightplan Downloader

Author: Nicolei Rademacher
Copyright (C) 2025

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
        license_window = tk.Toplevel(self.root)
        license_window.title("License - GPL v3+")
        license_window.configure(bg="#2b2b2b")
        text_area = ScrolledText(license_window, wrap=tk.WORD, bg="#1e1e1e", fg="#ffffff", insertbackground='#ffffff')
        text_area.pack(expand=True, fill='both')
        text_area.insert(tk.END, license_text)
        text_area.config(state='disabled')

    # Hier kommen jetzt alle fehlenden Methoden vollständig rein

    def log(self, message):
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)

    def select_directory(self, fmt, entry):
        directory = filedialog.askdirectory(title=f"Select target directory for {fmt}")
        if directory:
            entry.delete(0, tk.END)
            entry.insert(0, directory)

    def save_settings(self):
        config = {
            "username": self.username_entry.get(),
            "formats": [fmt for fmt, var in self.formats.items() if var.get()],
            "directories": {fmt: entry.get() for fmt, entry in self.directories.items()},
            "last_flight_info": self.last_flight_info
        }
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=4)
        messagebox.showinfo("Saved", "Settings have been saved!")

    def load_settings(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                self.username_entry.insert(0, config.get("username", ""))
                for fmt, var in self.formats.items():
                    var.set(fmt in config.get("formats", []))
                for fmt, entry in self.directories.items():
                    entry.insert(0, config.get("directories", {}).get(fmt, ""))

    def load_last_flight_info(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
                return config.get("last_flight_info", {})
        return {}

    def save_last_flight_info(self, flight_info):
        self.last_flight_info = flight_info
        self.save_settings()

    def update_flight_info_display(self, icao_airline, flight_number, aircraft, origin, destination, is_new, origin_name, destination_name):
        display_text = f"Flight {icao_airline} {flight_number} | Aircraft: {aircraft} | {origin} ➔ {destination} | {origin_name} ➔ {destination_name}"
        color = "#4CAF50" if is_new else "#ffffff"
        self.flight_info_label.config(text=display_text, foreground=color)

    def get_next_filename(self, directory, base_name, extension):
        existing_files = os.listdir(directory)
        counter = 1
        while True:
            filename = f"{base_name}{counter:02}.{extension}"
            if filename not in existing_files:
                return filename
            counter += 1

    def download_file(self, url, save_directory, filename):
        os.makedirs(save_directory, exist_ok=True)
        file_path = os.path.join(save_directory, filename)
        response = requests.get(url, stream=True)
        response.raise_for_status()
        total_length = response.headers.get('content-length')
        dl = 0
        total_length = int(total_length) if total_length is not None else None

        with open(file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)
                    dl += len(chunk)
                    if total_length:
                        self.progress['value'] = (dl / total_length) * 100
                        self.root.update_idletasks()

        self.progress['value'] = 100
        self.root.update_idletasks()

    def clean_old_files(self):
        confirm = messagebox.askyesno("Confirm", "Do you really want to delete all flightplan files older than 7 days in the target directories?")
        if not confirm:
            return

        now = time.time()
        cutoff = now - (7 * 86400)

        for fmt, entry in self.directories.items():
            directory = entry.get()
            if not directory or not os.path.isdir(directory):
                continue
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff:
                        try:
                            os.remove(file_path)
                            self.log(f"Deleted old file: {file_path}")
                        except Exception as e:
                            self.log(f"Error deleting file {file_path}: {e}")
        messagebox.showinfo("Cleanup", "Old files cleanup completed!")

    def download_flightplan(self):
        username = self.username_entry.get().strip()
        if not username:
            messagebox.showerror("Error", "Please enter your SimBrief username!")
            return

        try:
            url = SIMBRIEF_API_URL.format(username=username)
            self.log(f"Fetching SimBrief data from: {url}")
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            fetch = data.get("fetch", {})
            general = data.get("general", {})
            params = data.get("params", {})
            origin = data.get("origin", {})
            destination = data.get("destination", {})
            aircraft = data.get("aircraft", {})
            destination = data.get("destination", {})

            if not all([fetch, params, origin, destination, aircraft]):
                messagebox.showwarning("Warning", "Incomplete data received from SimBrief. Check your flightplan.")
                return

            origin_icao = origin.get("icao_code")
            destination_icao = destination.get("icao_code")
            timecode = params.get("time_generated")
            icao_airline = general.get("icao_airline", "Private Charter")
            flight_number = general.get("flight_number", "N/A")
            aircraft_type = aircraft.get("icao_code", "N/A")
            origin_name = origin.get("name", "N/A")
            destination_name = destination.get("name", "N/A")

            current_flight_info = {
                "icao_airline": icao_airline,
                "flight_number": flight_number,
                "aircraft": aircraft_type,
                "origin": origin_icao,
                "destination": destination_icao,
                "timecode": timecode,
                "origin_name": timecode,
                "destination_name": timecode
            }

            is_new_route = current_flight_info != self.last_flight_info
            self.update_flight_info_display(icao_airline, flight_number, aircraft_type, origin_icao, destination_icao, is_new_route, origin_name, destination_name)

            if is_new_route:
                self.log("New route detected!")
                self.save_last_flight_info(current_flight_info)
            else:
                self.log("No new route detected.")

            downloaded_any = False

            for fmt, var in self.formats.items():
                if var.get():
                    target_dir = self.directories[fmt].get()
                    if not target_dir:
                        messagebox.showwarning("Warning", f"No target directory set for {fmt}.")
                        continue

                    base_name = f"{origin_icao}{destination_icao}"
                    if fmt == "PDF":
                        base_filename = f"{base_name}_PDF_{timecode}"
                        file_url = f"{FLIGHTPLAN_BASE_URL}{base_filename}.pdf"
                        extension = "pdf"
                    elif fmt == "FMS":
                        base_filename = f"{base_name}_XPN_{timecode}"
                        file_url = f"{FLIGHTPLAN_BASE_URL}{base_filename}.fms"
                        extension = "fms"
                    elif fmt == "XPE":
                        base_filename = f"{base_name}_XPE_{timecode}"
                        file_url = f"{FLIGHTPLAN_BASE_URL}{base_filename}.fms"
                        extension = "fms"
                    elif fmt in ("FF757", "FF767"):
                        base_filename = f"{base_name}_VMX_{timecode}"
                        file_url = f"{FLIGHTPLAN_BASE_URL}{base_filename}.flp--VM5"
                        extension = "flp"
                    elif fmt == "TDS":
                        base_filename = f"{base_name}_GTN_{timecode}"
                        file_url = f"{FLIGHTPLAN_BASE_URL}{base_filename}.gfp--VM5"
                        extension = "gfp"
                    else:
                        continue

                    filename = self.get_next_filename(target_dir, base_name, extension)

                    try:
                        self.log(f"Downloading {fmt} to {target_dir}/{filename}")
                        self.progress['value'] = 0
                        self.download_file(file_url, target_dir, filename)
                        downloaded_any = True
                        self.log(f"Saved: {filename}")
                    except Exception as e:
                        self.log(f"Failed to download {fmt}: {e}")

            if downloaded_any:
                messagebox.showinfo("Success", "Selected flightplan files have been downloaded successfully!")
            else:
                messagebox.showwarning("Notice", "No files were downloaded. Check your selection and SimBrief plan.")

        except Exception as e:
            messagebox.showerror("Error", f"Error while fetching data: {e}")
            self.log(f"Error while fetching data: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SimBriefPyDownloader(root)
    root.mainloop()
