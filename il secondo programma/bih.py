import os
import random
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ExifTags
import traceback

# Funzione per correggere l'orientamento delle immagini
def fix_image_orientation(img):
    try:
        exif = img._getexif()
        if exif is None:
            return img
        for tag_id, value in exif.items():
            if ExifTags.TAGS.get(tag_id) == "Orientation":
                if value == 3:
                    img = img.rotate(180, expand=True)
                elif value == 6:
                    img = img.rotate(270, expand=True)
                elif value == 8:
                    img = img.rotate(90, expand=True)
                break
    except Exception:
        pass
    return img

# Funzione per generare un numero casuale sicuro
def safe_randint(start, end):
    if end < start:
        return start
    return random.randint(start, end)

class OutfitGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generatore Outfit - Whisper Mind")
        self.root.geometry("1440x900")
        self.root.attributes("-fullscreen", True)

        # Percorsi base
        self.base_path = "/Users/grigolausss/Desktop/strumenti/generatore di outfit il programma/foto per generatore"
        self.output_path = "/Users/grigolausss/Desktop/strumenti/generatore di outfit il programma/immagini generate"
        self.watermark_path = "/Users/grigolausss/Desktop/WhisperMind/logo/logo nuovo senza sfondo.PNG"
        self.fonts_path = "/Users/grigolausss/Desktop/strumenti/generatore di outfit il programma/fonts"
        self.palette_file = "custom_background_palette.json"

        # Categorie di immagini
        self.category_paths = {}
        self.accessory_types = ["maglie", "pantaloni", "occhiali", "wallet", "profumi", 
                                "bracciali", "orologi", "cinture", "scarpe", "auto", "sfondi"]

        for item in self.accessory_types:
            self.category_paths[item] = os.path.join(self.base_path, item.lower())

        # Variabili Tkinter
        self.show_names = tk.BooleanVar(value=False)
        self.use_watermark = tk.BooleanVar(value=True)
        self.watermark_position = tk.StringVar(value="Sopra")
        self.watermark_path_var = tk.StringVar(value=self.watermark_path)
        self.selected_font = tk.StringVar(value="Random")
        self.selected_font_color_rgb = (255, 255, 255)
        self.available_fonts = []
        self.font_objects = {}
        self.folders_visible = tk.BooleanVar(value=True)  # Stato della sezione cartelle

        # Palette di colori per gli sfondi a tinta unita
        self.background_palette = [
            (245, 245, 220),  # Beige chiaro
            (173, 216, 230),  # Blu chiaro
            (25, 25, 112),    # Blu scuro
            (144, 238, 144)   # Verde chiaro
        ]
        self.load_background_palette()

        self.load_fonts()
        self.create_widgets()

    def load_fonts(self):
        if not os.path.exists(self.fonts_path):
            messagebox.showwarning("Attenzione", f"La cartella dei font {self.fonts_path} non esiste. Creala e aggiungi i file .ttf.")
            return

        self.available_fonts = ["Random"]
        for file in os.listdir(self.fonts_path):
            if file.lower().endswith(".ttf"):
                font_path = os.path.join(self.fonts_path, file)
                font_name = os.path.splitext(file)[0]
                self.available_fonts.append(font_name)
                try:
                    self.font_objects[font_name] = font_path
                except Exception as e:
                    messagebox.showwarning("Attenzione", f"Errore nel caricamento del font {font_name}: {e}")

    def load_background_palette(self):
        if os.path.exists(self.palette_file):
            try:
                with open(self.palette_file, 'r') as f:
                    loaded_palette = json.load(f)
                    self.background_palette = [tuple(color) for color in loaded_palette]
            except Exception as e:
                messagebox.showwarning("Attenzione", f"Errore nel caricamento della tavolozza degli sfondi: {e}")

    def save_background_palette(self):
        try:
            with open(self.palette_file, 'w') as f:
                json.dump(self.background_palette, f, indent=4)
        except Exception as e:
            messagebox.showerror("Errore", f"Errore nel salvataggio della tavolozza degli sfondi: {e}")

    def get_unique_filename(self, base_path, filename):
        base_name, ext = os.path.splitext(filename)
        counter = 1
        new_filename = filename
        new_path = os.path.join(base_path, new_filename)

        while os.path.exists(new_path):
            new_filename = f"{base_name} ({counter}){ext}"
            new_path = os.path.join(base_path, new_filename)
            counter += 1
        return new_filename

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(main_frame, bg="#f0f0f0")
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        def on_mouse_wheel(event):
            delta = 0
            if event.delta:
                delta = -event.delta // 120
            elif event.num == 4:
                delta = -1
            elif event.num == 5:
                delta = 1
            canvas.yview_scroll(delta, "units")

        canvas.bind_all("<MouseWheel>", on_mouse_wheel)
        canvas.bind_all("<Button-4>", on_mouse_wheel)
        canvas.bind_all("<Button-5>", on_mouse_wheel)

        # Titolo
        title_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
        title_frame.pack(fill="x", pady=20)
        tk.Label(title_frame, text="Generatore Outfit - Whisper Mind", font=("Helvetica", 20, "bold"), bg="#f0f0f0").pack()

        # Sezione cartelle con freccetta
        folders_container = tk.Frame(scrollable_frame, bg="#f0f0f0")
        folders_container.pack(fill="x", padx=20, pady=10)

        folders_header = tk.Frame(folders_container, bg="#f0f0f0")
        folders_header.pack(fill="x")
        tk.Label(folders_header, text="📂 Impostazioni Cartelle", font=("Helvetica", 14, "bold"), bg="#f0f0f0").pack(side="left")
        toggle_button = tk.Button(folders_header, text="▼", command=self.toggle_folders)
        toggle_button.pack(side="left", padx=5)

        self.folders_frame = tk.LabelFrame(folders_container, text="", bg="#ffffff", fg="#333333", padx=10, pady=10)
        self.folders_frame.pack(fill="x")

        for idx, item in enumerate(self.accessory_types):
            folder_inner_frame = tk.Frame(self.folders_frame, bg="#ffffff")
            folder_inner_frame.pack(fill="x", pady=5)
            tk.Label(folder_inner_frame, text=f"{item.capitalize()}:", width=15, anchor="w", bg="#ffffff").pack(side="left")
            path_entry = tk.Entry(folder_inner_frame, width=60)
            path_entry.insert(0, self.category_paths[item])
            path_entry.config(state="readonly")
            path_entry.pack(side="left", padx=5)
            browse_btn = tk.Button(folder_inner_frame, text="Sfoglia", command=lambda e=path_entry: self.select_folder(e))
            browse_btn.pack(side="left", padx=5)
            self.category_paths[item] = path_entry

        # Effetti immagine
        effects_frame = tk.LabelFrame(scrollable_frame, text="🎨 Effetti Immagine", font=("Helvetica", 14, "bold"), bg="#ffffff", fg="#333333", padx=10, pady=10)
        effects_frame.pack(fill="x", padx=20, pady=10)

        blur_frame = tk.Frame(effects_frame, bg="#ffffff")
        blur_frame.pack(fill="x", pady=5)
        tk.Label(blur_frame, text="✨ Sfocatura sfondo (0–10):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.blur_slider = tk.Scale(blur_frame, from_=0, to=10, orient="horizontal", length=300)
        self.blur_slider.set(2)
        self.blur_slider.pack(side="left", padx=5)

        brightness_frame = tk.Frame(effects_frame, bg="#ffffff")
        brightness_frame.pack(fill="x", pady=5)
        tk.Label(brightness_frame, text="💡 Luminosità sfondo (-100 a 100):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.brightness_slider = tk.Scale(brightness_frame, from_=-100, to=100, orient="horizontal", length=300)
        self.brightness_slider.set(-30)
        self.brightness_slider.pack(side="left", padx=5)

        spacing_frame = tk.Frame(effects_frame, bg="#ffffff")
        spacing_frame.pack(fill="x", pady=5)
        tk.Label(spacing_frame, text="📏 Distanza maglia-pantaloni (0-100):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.spacing_slider = tk.Scale(spacing_frame, from_=0, to=100, orient="horizontal", length=300)
        self.spacing_slider.set(20)
        self.spacing_slider.pack(side="left", padx=5)

        size_main_frame = tk.Frame(effects_frame, bg="#ffffff")
        size_main_frame.pack(fill="x", pady=5)
        tk.Label(size_main_frame, text="📏 Grandezza maglie/pantaloni (50-200%):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.size_main_slider = tk.Scale(size_main_frame, from_=50, to=200, orient="horizontal", length=300)
        self.size_main_slider.set(120)
        self.size_main_slider.pack(side="left", padx=5)

        size_accessory_frame = tk.Frame(effects_frame, bg="#ffffff")
        size_accessory_frame.pack(fill="x", pady=5)
        tk.Label(size_accessory_frame, text="📏 Grandezza accessori (50-200%):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.size_accessory_slider = tk.Scale(size_accessory_frame, from_=50, to=200, orient="horizontal", length=300)
        self.size_accessory_slider.set(80)
        self.size_accessory_slider.pack(side="left", padx=5)

        object_spacing_frame = tk.Frame(effects_frame, bg="#ffffff")
        object_spacing_frame.pack(fill="x", pady=5)
        tk.Label(object_spacing_frame, text="📏 Distanza tra oggetti (0-100):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.object_spacing_slider = tk.Scale(object_spacing_frame, from_=0, to=100, orient="horizontal", length=300)
        self.object_spacing_slider.set(30)
        self.object_spacing_slider.pack(side="left", padx=5)

        # Opzioni di generazione
        generation_frame = tk.LabelFrame(scrollable_frame, text="⚙️ Opzioni di Generazione", font=("Helvetica", 14, "bold"), bg="#ffffff", fg="#333333", padx=10, pady=10)
        generation_frame.pack(fill="x", padx=20, pady=10)

        res_frame = tk.Frame(generation_frame, bg="#ffffff")
        res_frame.pack(fill="x", pady=5)
        tk.Label(res_frame, text="📐 Risoluzione (Larghezza x Altezza):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        res_inner_frame = tk.Frame(res_frame, bg="#ffffff")
        res_inner_frame.pack(side="left")
        self.width_entry = tk.Entry(res_inner_frame, width=10)
        self.width_entry.insert(0, "1080")
        self.width_entry.pack(side="left", padx=5)
        tk.Label(res_inner_frame, text="x", bg="#ffffff").pack(side="left")
        self.height_entry = tk.Entry(res_inner_frame, width=10)
        self.height_entry.insert(0, "1920")
        self.height_entry.pack(side="left", padx=5)
        self.width_entry.bind("<Return>", lambda event: self.generate_outfits())
        self.height_entry.bind("<Return>", lambda event: self.generate_outfits())

        format_frame = tk.Frame(generation_frame, bg="#ffffff")
        format_frame.pack(fill="x", pady=5)
        tk.Label(format_frame, text="🖼️ Formato immagine:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.format_combo = ttk.Combobox(format_frame, values=["PNG", "JPG"], state="readonly", width=10)
        self.format_combo.set("PNG")
        self.format_combo.pack(side="left", padx=5)

        quantity_frame = tk.Frame(generation_frame, bg="#ffffff")
        quantity_frame.pack(fill="x", pady=5)
        tk.Label(quantity_frame, text="📸 Numero immagini da generare:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.quantity_spinbox = tk.Spinbox(quantity_frame, from_=1, to=100, width=5)
        self.quantity_spinbox.pack(side="left", padx=5)
        self.quantity_spinbox.bind("<Return>", lambda event: self.generate_outfits())

        output_frame = tk.Frame(generation_frame, bg="#ffffff")
        output_frame.pack(fill="x", pady=5)
        tk.Label(output_frame, text="📂 Cartella di salvataggio:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.output_entry = tk.Entry(output_frame, width=40)
        self.output_entry.insert(0, self.output_path)
        self.output_entry.config(state="readonly")
        self.output_entry.pack(side="left", padx=5)
        output_btn = tk.Button(output_frame, text="Sfoglia", command=lambda: self.select_folder(self.output_entry))
        output_btn.pack(side="left", padx=5)

        tk.Button(generation_frame, text="Apri Cartella Output", command=self.open_output_folder).pack(pady=5)

        # Opzioni watermark
        watermark_frame = tk.LabelFrame(scrollable_frame, text="💧 Opzioni Watermark", font=("Helvetica", 14, "bold"), bg="#ffffff", fg="#333333", padx=10, pady=10)
        watermark_frame.pack(fill="x", padx=20, pady=10)

        self.use_watermark_check = tk.Checkbutton(watermark_frame, text="Usa Watermark", variable=self.use_watermark, bg="#ffffff")
        self.use_watermark_check.pack(anchor="w", pady=5)

        watermark_path_frame = tk.Frame(watermark_frame, bg="#ffffff")
        watermark_path_frame.pack(fill="x", pady=5)
        tk.Label(watermark_path_frame, text="💧 Percorso Watermark (PNG):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.watermark_entry = tk.Entry(watermark_path_frame, width=40, textvariable=self.watermark_path_var)
        self.watermark_entry.config(state="readonly")
        self.watermark_entry.pack(side="left", padx=5)
        watermark_btn = tk.Button(watermark_path_frame, text="Sfoglia", command=self.select_watermark)
        watermark_btn.pack(side="left", padx=5)

        watermark_pos_frame = tk.Frame(watermark_frame, bg="#ffffff")
        watermark_pos_frame.pack(fill="x", pady=5)
        tk.Label(watermark_pos_frame, text="📍 Posizione Watermark:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.watermark_combo = ttk.Combobox(watermark_pos_frame, values=["Sopra", "Sotto"], state="readonly", textvariable=self.watermark_position, width=10)
        self.watermark_combo.set("Sopra")
        self.watermark_combo.pack(side="left", padx=5)

        # Opzioni accessori e testo
        accessories_frame = tk.LabelFrame(scrollable_frame, text="🔧 Accessori e Testo", font=("Helvetica", 14, "bold"), bg="#ffffff", fg="#333333", padx=10, pady=10)
        accessories_frame.pack(fill="x", padx=20, pady=10)

        accessory_count_frame = tk.Frame(accessories_frame, bg="#ffffff")
        accessory_count_frame.pack(fill="x", pady=5)
        tk.Label(accessory_count_frame, text="🔢 Numero accessori (2 a max):", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.accessory_slider = tk.Scale(accessory_count_frame, from_=2, to=len([cat for cat in self.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]]), orient="horizontal", length=300)
        self.accessory_slider.set(3)
        self.accessory_slider.pack(side="left", padx=5)
        random_btn = tk.Button(accessory_count_frame, text="Random", command=self.random_accessory_count)
        random_btn.pack(side="left", padx=5)

        font_frame = tk.Frame(accessories_frame, bg="#ffffff")
        font_frame.pack(fill="x", pady=5)
        tk.Label(font_frame, text="✍️ Font per nomi:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.font_combo = ttk.Combobox(font_frame, values=self.available_fonts, state="readonly", textvariable=self.selected_font, width=15)
        self.font_combo.set("Random")
        self.font_combo.pack(side="left", padx=5)

        color_frame = tk.Frame(accessories_frame, bg="#ffffff")
        color_frame.pack(fill="x", pady=5)
        tk.Label(color_frame, text="🎨 Colore font:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        color_inner_frame = tk.Frame(color_frame, bg="#ffffff")
        color_inner_frame.pack(side="left")
        self.color_preview = tk.Label(color_inner_frame, text="  ", bg="#FFFFFF", width=5, height=1)
        self.color_preview.pack(side="left", padx=5)
        tk.Button(color_inner_frame, text="Scegli Colore", command=self.open_color_picker).pack(side="left", padx=5)
        tk.Button(color_inner_frame, text="Gestisci Tavolozza Font", command=self.open_palette_manager).pack(side="left", padx=5)
        tk.Button(color_inner_frame, text="Gestisci Tavolozza Sfondi", command=self.open_background_palette_manager).pack(side="left", padx=5)

        self.show_names_check = tk.Checkbutton(accessories_frame, text="Mostra nomi sotto oggetti", variable=self.show_names, bg="#ffffff")
        self.show_names_check.pack(anchor="w", pady=5)

        # Pulsante di generazione
        generate_frame = tk.Frame(scrollable_frame, bg="#f0f0f0")
        generate_frame.pack(fill="x", pady=20)
        self.generate_btn = tk.Button(generate_frame, text="🚀 Genera Outfit", bg="#4CAF50", fg="white", font=("Helvetica", 16, "bold"), command=self.generate_outfits)
        self.generate_btn.pack()

    def toggle_folders(self):
        if self.folders_visible.get():
            self.folders_frame.pack_forget()
            self.folders_visible.set(False)
            self.folders_header.winfo_children()[1].config(text="▶")
        else:
            self.folders_frame.pack(fill="x")
            self.folders_visible.set(True)
            self.folders_header.winfo_children()[1].config(text="▼")

    def open_output_folder(self):
        output_folder = self.output_entry.get()
        if os.path.exists(output_folder):
            os.system(f"open '{output_folder}'")
        else:
            messagebox.showerror("Errore", "La cartella di output non esiste.")

    def open_color_picker(self):
        color_window = tk.Toplevel(self.root)
        color_window.title("Selettore Colore")
        color_window.geometry("300x500")

        r_var = tk.IntVar(value=self.selected_font_color_rgb[0])
        g_var = tk.IntVar(value=self.selected_font_color_rgb[1])
        b_var = tk.IntVar(value=self.selected_font_color_rgb[2])
        brightness_var = tk.DoubleVar(value=1.0)
        saturation_var = tk.DoubleVar(value=1.0)

        tk.Label(color_window, text="Anteprima Colore", font=("Helvetica", 12)).pack(pady=10)
        color_display = tk.Label(color_window, bg="#FFFFFF", width=20, height=2)
        color_display.pack(pady=5)

        def update_color(*args):
            r = r_var.get()
            g = g_var.get()
            b = b_var.get()
            brightness = brightness_var.get()
            saturation = saturation_var.get()

            r = int((r * saturation) + (128 * (1 - saturation)))
            g = int((g * saturation) + (128 * (1 - saturation)))
            b = int((b * saturation) + (128 * (1 - saturation)))

            r = int(r * brightness)
            g = int(g * brightness)
            b = int(b * brightness)

            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))

            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            color_display.config(bg=hex_color)
            self.selected_font_color_rgb = (r, g, b)
            self.color_preview.config(bg=hex_color)

        tk.Label(color_window, text="Rosso (R):").pack()
        tk.Scale(color_window, from_=0, to=255, orient="horizontal", variable=r_var, command=update_color).pack(fill="x", padx=10)
        tk.Label(color_window, text="Verde (G):").pack()
        tk.Scale(color_window, from_=0, to=255, orient="horizontal", variable=g_var, command=update_color).pack(fill="x", padx=10)
        tk.Label(color_window, text="Blu (B):").pack()
        tk.Scale(color_window, from_=0, to=255, orient="horizontal", variable=b_var, command=update_color).pack(fill="x", padx=10)

        tk.Label(color_window, text="Saturazione (Grigio → Colore):").pack()
        tk.Scale(color_window, from_=0, to=1, resolution=0.01, orient="horizontal", variable=saturation_var, command=update_color).pack(fill="x", padx=10)

        tk.Label(color_window, text="Luminosità (Nero → Colore):").pack()
        tk.Scale(color_window, from_=0, to=1, resolution=0.01, orient="horizontal", variable=brightness_var, command=update_color).pack(fill="x", padx=10)

        def pick_color():
            color = colorchooser.askcolor(title="Scegli un colore")[0]
            if color:
                r_var.set(int(color[0]))
                g_var.set(int(color[1]))
                b_var.set(int(color[2]))
                brightness_var.set(1.0)
                saturation_var.set(1.0)
                update_color()

        tk.Button(color_window, text="Selettore Colore Rapido", command=pick_color).pack(pady=10)
        update_color()

    def open_palette_manager(self):
        # Nota: Il gestore della tavolozza font non era definito nel codice originale.
        # Per coerenza, assumo che tu voglia una tavolozza simile a quella degli sfondi.
        # Creo una tavolozza font di default vuota.
        self.color_palette = [(255, 255, 255), (0, 0, 0)]  # Tavolozza font di default

        palette_window = tk.Toplevel(self.root)
        palette_window.title("Gestisci Tavolozza Font")
        palette_window.geometry("300x400")

        palette_frame = tk.Frame(palette_window)
        palette_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def update_palette_display():
            for widget in palette_frame.winfo_children():
                widget.destroy()

            for idx, color in enumerate(self.color_palette):
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                frame = tk.Frame(palette_frame)
                frame.pack(fill="x", pady=2)

                tk.Label(frame, bg=color_hex, width=5, height=2).pack(side="left", padx=5)
                tk.Label(frame, text=f"R:{color[0]} G:{color[1]} B:{color[2]}").pack(side="left", padx=5)
                tk.Button(frame, text="Modifica", command=lambda i=idx: modify_color(i)).pack(side="left", padx=5)
                tk.Button(frame, text="Rimuovi", command=lambda i=idx: remove_color(i)).pack(side="left", padx=5)

        def add_color():
            color = colorchooser.askcolor(title="Aggiungi Colore")[0]
            if color:
                self.color_palette.append((int(color[0]), int(color[1]), int(color[2])))
                update_palette_display()

        def modify_color(idx):
            color = colorchooser.askcolor(title="Modifica Colore", initialcolor=self.color_palette[idx])[0]
            if color:
                self.color_palette[idx] = (int(color[0]), int(color[1]), int(color[2]))
                update_palette_display()

        def remove_color(idx):
            if len(self.color_palette) > 1:
                self.color_palette.pop(idx)
                update_palette_display()
            else:
                messagebox.showwarning("Attenzione", "Deve esserci almeno un colore nella tavolozza!")

        tk.Button(palette_window, text="Aggiungi Colore", command=add_color).pack(pady=5)
        update_palette_display()

    def open_background_palette_manager(self):
        palette_window = tk.Toplevel(self.root)
        palette_window.title("Gestisci Tavolozza Sfondi")
        palette_window.geometry("300x400")

        palette_frame = tk.Frame(palette_window)
        palette_frame.pack(fill="both", expand=True, padx=10, pady=10)

        def update_palette_display():
            for widget in palette_frame.winfo_children():
                widget.destroy()

            for idx, color in enumerate(self.background_palette):
                color_hex = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                frame = tk.Frame(palette_frame)
                frame.pack(fill="x", pady=2)

                tk.Label(frame, bg=color_hex, width=5, height=2).pack(side="left", padx=5)
                tk.Label(frame, text=f"R:{color[0]} G:{color[1]} B:{color[2]}").pack(side="left", padx=5)
                tk.Button(frame, text="Modifica", command=lambda i=idx: modify_color(i)).pack(side="left", padx=5)
                tk.Button(frame, text="Rimuovi", command=lambda i=idx: remove_color(i)).pack(side="left", padx=5)

        def add_color():
            color = colorchooser.askcolor(title="Aggiungi Colore")[0]
            if color:
                self.background_palette.append((int(color[0]), int(color[1]), int(color[2])))
                self.save_background_palette()
                update_palette_display()

        def modify_color(idx):
            color = colorchooser.askcolor(title="Modifica Colore", initialcolor=self.background_palette[idx])[0]
            if color:
                self.background_palette[idx] = (int(color[0]), int(color[1]), int(color[2]))
                self.save_background_palette()
                update_palette_display()

        def remove_color(idx):
            if len(self.background_palette) > 1:
                self.background_palette.pop(idx)
                self.save_background_palette()
                update_palette_display()
            else:
                messagebox.showwarning("Attenzione", "Deve esserci almeno un colore nella tavolozza!")

        tk.Button(palette_window, text="Aggiungi Colore", command=add_color).pack(pady=5)
        update_palette_display()

    def select_folder(self, entry_widget):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            entry_widget.config(state="normal")
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder_selected)
            entry_widget.config(state="readonly")

    def select_watermark(self):
        file_selected = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if file_selected:
            self.watermark_path_var.set(file_selected)

    def random_accessory_count(self):
        max_accessories = len([cat for cat in self.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]])
        self.accessory_slider.set(safe_randint(2, max_accessories))  # Minimo 2 accessori

    def load_images_from_folder(self, folder_path):
        valid_extensions = (".png", ".jpg", ".jpeg", ".PNG", ".JPG", ".JPEG")
        images = []
        if not os.path.exists(folder_path):
            print(f"DEBUG: La cartella {folder_path} non esiste.")
            return images
        for file in os.listdir(folder_path):
            if file.lower().endswith(valid_extensions):
                full_path = os.path.join(folder_path, file)
                images.append((full_path, os.path.splitext(file)[0]))
        return images

    def resize_image(self, image, max_width, max_height):
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return image

    def get_font_color(self):
        return self.selected_font_color_rgb

    def neutral_background(self, width, height):
        bg_color = random.choice(self.background_palette)
        return Image.new("RGBA", (width, height), bg_color)

    def is_position_safe(self, x, y, width, height, img_width, img_height):
        safe_width = width - 150
        safe_height = height - 75 - 125
        safe_left = 0
        safe_top = 75
        safe_right = safe_width
        safe_bottom = safe_height + 75

        return (x >= safe_left and x + img_width <= safe_right and
                y >= safe_top and y + img_height <= safe_bottom)

    def generate_outfits(self):
        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            quantity = int(self.quantity_spinbox.get())
            output_folder = self.output_entry.get()
            if not output_folder or not os.path.exists(output_folder):
                messagebox.showerror("Errore", "Seleziona una cartella di salvataggio valida.")
                return
            if not self.category_paths["maglie"].get() or not self.category_paths["pantaloni"].get() or not self.category_paths["sfondi"].get():
                messagebox.showerror("Errore", "Seleziona almeno le cartelle per Maglie, Pantaloni e Sfondi.")
                return

            category_images = {}
            for category in self.accessory_types:
                folder = self.category_paths[category].get()
                category_images[category] = self.load_images_from_folder(folder)

            if not category_images["maglie"]:
                messagebox.showerror("Errore", "La cartella 'maglie' non contiene immagini valide.")
                return
            if not category_images["pantaloni"]:
                messagebox.showerror("Errore", "La cartella 'pantaloni' non contiene immagini valide.")
                return
            if not category_images["sfondi"]:
                messagebox.showerror("Errore", "La cartella 'sfondi' non contiene immagini valide.")
                return

            optional_accessories = [cat for cat in self.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]]
            max_accessories = max(2, self.accessory_slider.get())  # Minimo 2 accessori

            font = None
            font_size = 30
            if self.show_names.get():
                selected_font_name = self.selected_font.get()
                if selected_font_name == "Random":
                    available_font_names = [f for f in self.available_fonts if f != "Random"]
                    if available_font_names:
                        selected_font_name = random.choice(available_font_names)
                    else:
                        selected_font_name = None
                if selected_font_name and selected_font_name in self.font_objects:
                    try:
                        font = ImageFont.truetype(self.font_objects[selected_font_name], font_size)
                    except Exception as e:
                        messagebox.showwarning("Attenzione", f"Errore nel caricamento del font: {e}. Uso font predefinito.")
                        font = ImageFont.load_default()
                else:
                    font = ImageFont.load_default()

            for i in range(quantity):
                canvas = Image.new("RGBA", (width, height), (255, 255, 255, 0))

                # Sfondo
                if random.random() < 0.6:
                    background = self.neutral_background(width, height)
                else:
                    background_path = random.choice([img[0] for img in category_images["sfondi"]])
                    background = fix_image_orientation(Image.open(background_path).convert("RGBA"))
                    background = background.resize((width, height), Image.Resampling.LANCZOS)

                # Effetti sfondo
                blur_value = self.blur_slider.get()
                if blur_value > 0:
                    background = background.filter(ImageFilter.GaussianBlur(blur_value))

                brightness_value = self.brightness_slider.get()
                enhancer = ImageEnhance.Brightness(background)
                background = enhancer.enhance(1 + brightness_value / 100)

                canvas.paste(background, (0, 0))
                draw = ImageDraw.Draw(canvas)

                occupied_areas = []

                # Parametri di ridimensionamento
                size_main_factor = self.size_main_slider.get() / 100
                size_accessory_factor = self.size_accessory_slider.get() / 100
                object_spacing = self.object_spacing_slider.get() * 2
                spacing = self.spacing_slider.get() * 3

                # Dimensioni degli oggetti principali
                shirt_max_width = int((width - 150) * 0.5 * size_main_factor)
                shirt_max_height = int((height - 200) * 0.35 * size_main_factor)
                pants_max_width = int((width - 150) * 0.5 * size_main_factor)
                pants_max_height = int((height - 200) * 0.35 * size_main_factor)

                # Carica maglia e pantaloni
                shirt_data = random.choice(category_images["maglie"])
                shirt_img = fix_image_orientation(Image.open(shirt_data[0]).convert("RGBA"))
                shirt_img = self.resize_image(shirt_img, shirt_max_width, shirt_max_height)
                shirt_name = shirt_data[1]

                pants_data = random.choice(category_images["pantaloni"])
                pants_img = fix_image_orientation(Image.open(pants_data[0]).convert("RGBA"))
                pants_img = self.resize_image(pants_img, pants_max_width, pants_max_height)
                pants_name = pants_data[1]

                # Posizionamento centrale di maglia e pantaloni
                shirt_x = ((width - 150) - shirt_img.width) // 2
                shirt_y = 75 + int((height - 200 - shirt_img.height - pants_img.height - spacing) * 0.25)
                shirt_x = max(0, min(width - 150 - shirt_img.width, shirt_x))

                canvas.paste(shirt_img, (shirt_x, shirt_y), shirt_img)
                occupied_areas.append((shirt_x, shirt_y, shirt_img.width, shirt_img.height))

                if self.show_names.get():
                    text_width = draw.textlength(shirt_name, font=font) if font else 100
                    text_x = shirt_x + (shirt_img.width - text_width) // 2
                    text_y = shirt_y + shirt_img.height + 10
                    if text_x + text_width > width - 150:
                        text_x = width - 150 - text_width
                    if text_y + font_size > height - 125:
                        text_y = height - 125 - font_size
                    font_color = self.get_font_color()
                    draw.text((text_x, text_y), shirt_name, font=font, fill=font_color)
                    occupied_areas.append((text_x, text_y, text_width, font_size))

                pants_x = ((width - 150) - pants_img.width) // 2
                pants_y = shirt_y + shirt_img.height + spacing
                pants_x = max(0, min(width - 150 - pants_img.width, pants_x))
                if pants_y + pants_img.height > height - 125:
                    pants_y = height - 125 - pants_img.height
                canvas.paste(pants_img, (pants_x, pants_y), pants_img)
                occupied_areas.append((pants_x, pants_y, pants_img.width, pants_img.height))

                if self.show_names.get():
                    text_width = draw.textlength(pants_name, font=font) if font else 100
                    text_x = pants_x + (pants_img.width - text_width) // 2
                    text_y = pants_y + pants_img.height + 10
                    if text_x + text_width > width - 150:
                        text_x = width - 150 - text_width
                    if text_y + font_size > height - 125:
                        text_y = height - 125 - font_size
                    font_color = self.get_font_color()
                    draw.text((text_x, text_y), pants_name, font=font, fill=font_color)
                    occupied_areas.append((text_x, text_y, text_width, font_size))

                # Posizionamento watermark
                if self.use_watermark.get() and self.watermark_path_var.get():
                    watermark = fix_image_orientation(Image.open(self.watermark_path_var.get()).convert("RGBA"))
                    watermark = self.resize_image(watermark, (width - 150) // 3, (height - 200) // 4)
                    padding = 50 if self.watermark_position.get() == "Sopra" else 100
                    wm_x = ((width - 150) - watermark.width) // 2
                    wm_y = 75 + padding if self.watermark_position.get() == "Sopra" else height - 125 - watermark.height - padding
                    canvas.paste(watermark, (wm_x, wm_y), watermark)
                    occupied_areas.append((wm_x, wm_y, watermark.width, watermark.height))

                # Posizionamento accessori con logica di allineamento
                available_accessories = [cat for cat in optional_accessories if category_images[cat]]
                if len(available_accessories) < 2:
                    messagebox.showwarning("Attenzione", "Non ci sono abbastanza accessori disponibili (minimo 2 richiesti).")
                    continue
                selected_accessories = random.sample(available_accessories, min(max_accessories, len(available_accessories)))

                # Definizione delle dimensioni degli accessori per categoria
                accessory_sizes = {
                    "occhiali": (0.15 * size_accessory_factor, 0.15 * size_main_factor),
                    "wallet": (0.15 * size_accessory_factor, 0.15 * size_main_factor),
                    "profumi": (0.2 * size_accessory_factor, 0.2 * size_main_factor),
                    "bracciali": (0.1 * size_accessory_factor, 0.1 * size_main_factor),
                    "orologi": (0.1 * size_accessory_factor, 0.1 * size_main_factor),
                    "cinture": (0.2 * size_accessory_factor, 0.2 * size_main_factor),
                    "scarpe": (0.25 * size_accessory_factor,
