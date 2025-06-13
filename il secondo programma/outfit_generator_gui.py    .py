import os  # Aggiunto per risolvere "os non è definito"
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from outfit_generator_logic import OutfitGeneratorLogic

class OutfitGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Generatore Outfit - Whisper Mind")
        self.root.geometry("1440x900")
        self.root.attributes("-fullscreen", True)

        # Inizializza la logica di generazione
        self.logic = OutfitGeneratorLogic()

        # Variabili Tkinter
        self.show_names = tk.BooleanVar(value=False)
        self.use_watermark = tk.BooleanVar(value=True)
        self.watermark_position = tk.StringVar(value="Sopra")
        self.watermark_path_var = tk.StringVar(value=self.logic.watermark_path)
        self.selected_font = tk.StringVar(value="Random")
        self.selected_font_color_rgb = (255, 255, 255)
        self.folders_visible = tk.BooleanVar(value=True)

        self.create_widgets()

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
        self.toggle_button = tk.Button(folders_header, text="▼", command=self.toggle_folders)
        self.toggle_button.pack(side="left", padx=5)

        self.folders_frame = tk.LabelFrame(folders_container, text="", bg="#ffffff", fg="#333333", padx=10, pady=10)
        self.folders_frame.pack(fill="x")

        for item in self.logic.accessory_types:
            folder_inner_frame = tk.Frame(self.folders_frame, bg="#ffffff")
            folder_inner_frame.pack(fill="x", pady=5)
            tk.Label(folder_inner_frame, text=f"{item.capitalize()}:", width=15, anchor="w", bg="#ffffff").pack(side="left")
            path_entry = tk.Entry(folder_inner_frame, width=60)
            path_entry.insert(0, self.logic.category_paths[item])
            path_entry.config(state="readonly")
            path_entry.pack(side="left", padx=5)
            browse_btn = tk.Button(folder_inner_frame, text="Sfoglia", command=lambda e=path_entry: self.select_folder(e))
            browse_btn.pack(side="left", padx=5)
            self.logic.category_paths[item] = path_entry

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
        self.output_entry = tk.Entry(output_frame, width=50)
        self.output_entry.insert(0, self.logic.output_path)
        self.output_entry.config(state="readonly")
        self.output_entry.pack(side="left", padx=10)
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
        self.accessory_slider = tk.Scale(accessory_count_frame, from_=2, to=len([cat for cat in self.logic.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]]), orient="horizontal", length=300)
        self.accessory_slider.set(3)
        self.accessory_slider.pack(side="left", padx=5)
        random_btn = tk.Button(accessory_count_frame, text="Random", command=self.random_accessory_count)
        random_btn.pack(side="left", padx=5)

        font_frame = tk.Frame(accessories_frame, bg="#ffffff")
        font_frame.pack(fill="x", pady=5)
        tk.Label(font_frame, text="✍️ Font per nomi:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        self.font_combo = ttk.Combobox(font_frame, values=self.logic.available_fonts, state="readonly", textvariable=self.selected_font, width=15)
        self.font_combo.set("Random")
        self.font_combo.pack(side="left", padx=5)

        color_frame = tk.Frame(accessories_frame, bg="#ffffff")
        color_frame.pack(fill="x", pady=5)
        tk.Label(color_frame, text="🎨 Colore font:", width=25, anchor="w", bg="#ffffff").pack(side="left")
        color_inner_frame = tk.Frame(color_frame, bg="#ffffff")
        color_inner_frame.pack(side="left")
        self.color_preview = tk.Label(color_inner_frame, bg="#FFFFFF", width=5, height=1)
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
            self.toggle_button.config(text="▶")
        else:
            self.folders_frame.pack(fill="x")
            self.folders_visible.set(True)
            self.toggle_button.config(text="▼")

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
        self.logic.open_palette_manager(self.root, self.selected_font_color_rgb)

    def open_background_palette_manager(self):
        self.logic.open_background_palette_manager(self.root)

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
        self.logic.random_accessory_count(self.accessory_slider)

    def generate_outfits(self):
        self.logic.generate_outfits(
            width_entry=self.width_entry,
            height_entry=self.height_entry,
            quantity_spinbox=self.quantity_spinbox,
            output_entry=self.output_entry,
            format_combo=self.format_combo,
            show_names=self.show_names,
            use_watermark=self.use_watermark,
            watermark_path_var=self.watermark_path_var,
            watermark_position=self.watermark_position,
            selected_font=self.selected_font,
            blur_slider=self.blur_slider,
            brightness_slider=self.brightness_slider,
            spacing_slider=self.spacing_slider,
            size_main_slider=self.size_main_slider,
            size_accessory_slider=self.size_accessory_slider,
            object_spacing_slider=self.accessory_slider,  # Usa accessory_slider per il numero di accessori
            font_color_rgb=self.selected_font_color_rgb,
            root=self.root
        )

if __name__ == "__main__":
    root = tk.Tk()
    app = OutfitGeneratorApp(root)
    root.mainloop()