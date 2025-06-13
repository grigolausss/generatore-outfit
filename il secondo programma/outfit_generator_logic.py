import os
import random
import json
import tkinter as tk
from tkinter import messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ExifTags
import traceback

class OutfitGeneratorLogic:
    def __init__(self):
        # Percorsi base
        self.base_path = "/Users/grigolausss/Desktop/strumenti/generatore di outfit il programma/foto per generatore"
        self.output_path = "/Users/grigolausss/Desktop/strumenti/generatore di outfit il programma/immagini generate"
        self.watermark_path = "/Users/grigolausss/Desktop/WhisperMind/logo/logo nuovo senza sfondo.PNG"
        self.fonts_path = "/Users/grigolausss/Desktop/strumenti/generatore di outfit il programma/fonts"
        self.palette_file = "custom_background_palette.json"

        # Categorie di immagini
        self.accessory_types = ["maglie", "pantaloni", "occhiali", "wallet", "profumi", 
                                "bracciali", "orologi", "cinture", "scarpe", "auto", "sfondi"]
        self.category_paths = {item: os.path.join(self.base_path, item.lower()) for item in self.accessory_types}

        # Font
        self.available_fonts = []
        self.font_objects = {}
        self.load_fonts()

        # Palette di colori
        self.background_palette = [
            (245, 245, 220),  # Beige chiaro
            (173, 216, 230),  # Blu chiaro
            (25, 25, 112),    # Blu scuro
            (144, 238, 144)   # Verde chiaro
        ]
        self.color_palette = [(255, 255, 255), (0, 0, 0)]  # Tavolozza font di default
        self.load_background_palette()

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

    def fix_image_orientation(self, img):
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

    def safe_randint(self, start, end):
        if end < start:
            return start
        return random.randint(start, end)

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

    def open_palette_manager(self, root, selected_font_color_rgb):
        palette_window = tk.Toplevel(root)
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

    def open_background_palette_manager(self, root):
        palette_window = tk.Toplevel(root)
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

    def random_accessory_count(self, accessory_slider):
        max_accessories = len([cat for cat in self.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]])
        accessory_slider.set(self.safe_randint(2, max_accessories))

    def generate_outfits(self, width_entry, height_entry, quantity_spinbox, output_entry, format_combo, show_names, use_watermark, watermark_path_var, watermark_position, selected_font, blur_slider, brightness_slider, spacing_slider, size_main_slider, size_accessory_slider, object_spacing_slider, font_color_rgb, root):
        try:
            width = int(width_entry.get())
            height = int(height_entry.get())
            quantity = int(quantity_spinbox.get())
            output_folder = output_entry.get()
            if not output_folder or not os.path.exists(output_folder):
                messagebox.showerror("Errore", "Seleziona una cartella di salvataggio valida.")
                return
            if not self.category_paths["maglie"].get() or not self.category_paths["pantaloni"].get() or not self.category_paths["sfondi"].get():
                messagebox.showerror("Errore", "Seleziona almeno le cartelle per Maglie, Pantaloni e Sfondi.")
                return

            category_images = {category: self.load_images_from_folder(self.category_paths[category].get()) for category in self.accessory_types}

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
            max_accessories = max(2, object_spacing_slider.get())

            font = None
            font_size = 30
            if show_names.get():
                selected_font_name = selected_font.get()
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
                    background = self.fix_image_orientation(Image.open(background_path).convert("RGBA"))
                    background = background.resize((width, height), Image.Resampling.LANCZOS)

                # Effetti sfondo
                blur_value = blur_slider.get()
                if blur_value > 0:
                    background = background.filter(ImageFilter.GaussianBlur(blur_value))

                brightness_value = brightness_slider.get()
                enhancer = ImageEnhance.Brightness(background)
                background = enhancer.enhance(1 + brightness_value / 100)

                canvas.paste(background, (0, 0))
                draw = ImageDraw.Draw(canvas)

                occupied_areas = []

                # Parametri di ridimensionamento
                size_main_factor = size_main_slider.get() / 100
                size_accessory_factor = size_accessory_slider.get() / 100
                object_spacing = object_spacing_slider.get() * 2
                spacing = spacing_slider.get() * 3

                # Dimensioni degli oggetti principali
                shirt_max_width = int((width - 150) * 0.5 * size_main_factor)
                shirt_max_height = int((height - 200) * 0.35 * size_main_factor)
                pants_max_width = int((width - 150) * 0.5 * size_main_factor)
                pants_max_height = int((height - 200) * 0.35 * size_main_factor)

                # Carica maglia e pantaloni
                shirt_data = random.choice(category_images["maglie"])
                shirt_img = self.fix_image_orientation(Image.open(shirt_data[0]).convert("RGBA"))
                shirt_img = self.resize_image(shirt_img, shirt_max_width, shirt_max_height)
                shirt_name = shirt_data[1]

                pants_data = random.choice(category_images["pantaloni"])
                pants_img = self.fix_image_orientation(Image.open(pants_data[0]).convert("RGBA"))
                pants_img = self.resize_image(pants_img, pants_max_width, pants_max_height)
                pants_name = pants_data[1]

                # Posizionamento centrale di maglia e pantaloni
                shirt_x = ((width - 150) - shirt_img.width) // 2
                shirt_y = 75 + int((height - 200 - shirt_img.height - pants_img.height - spacing) * 0.25)
                shirt_x = max(0, min(width - 150 - shirt_img.width, shirt_x))

                canvas.paste(shirt_img, (shirt_x, shirt_y), shirt_img)
                occupied_areas.append((shirt_x, shirt_y, shirt_img.width, shirt_img.height))

                if show_names.get():
                    text_width = draw.textlength(shirt_name, font=font) if font else 100
                    text_x = shirt_x + (shirt_img.width - text_width) // 2
                    text_y = shirt_y + shirt_img.height + 10
                    if text_x + text_width > width - 150:
                        text_x = width - 150 - text_width
                    if text_y + font_size > height - 125:
                        text_y = height - 125 - font_size
                    font_color = font_color_rgb
                    draw.text((text_x, text_y), shirt_name, font=font, fill=font_color)
                    occupied_areas.append((text_x, text_y, text_width, font_size))

                pants_x = ((width - 150) - pants_img.width) // 2
                pants_y = shirt_y + shirt_img.height + spacing
                pants_x = max(0, min(width - 150 - pants_img.width, pants_x))
                if pants_y + pants_img.height > height - 125:
                    pants_y = height - 125 - pants_img.height
                canvas.paste(pants_img, (pants_x, pants_y), pants_img)
                occupied_areas.append((pants_x, pants_y, pants_img.width, pants_img.height))

                if show_names.get():
                    text_width = draw.textlength(pants_name, font=font) if font else 100
                    text_x = pants_x + (pants_img.width - text_width) // 2
                    text_y = pants_y + pants_img.height + 10
                    if text_x + text_width > width - 150:
                        text_x = width - 150 - text_width
                    if text_y + font_size > height - 125:
                        text_y = height - 125 - font_size
                    font_color = font_color_rgb
                    draw.text((text_x, text_y), pants_name, font=font, fill=font_color)
                    occupied_areas.append((text_x, text_y, text_width, font_size))

                # Posizionamento watermark
                if use_watermark.get() and watermark_path_var.get():
                    watermark = self.fix_image_orientation(Image.open(watermark_path_var.get()).convert("RGBA"))
                    watermark = self.resize_image(watermark, (width - 150) // 3, (height - 200) // 4)
                    padding = 50 if watermark_position.get() == "Sopra" else 100
                    wm_x = ((width - 150) - watermark.width) // 2
                    wm_y = 75 + padding if watermark_position.get() == "Sopra" else height - 125 - watermark.height - padding
                    canvas.paste(watermark, (wm_x, wm_y), watermark)
                    occupied_areas.append((wm_x, wm_y, watermark.width, watermark.height))

                # Posizionamento accessori
                available_accessories = [cat for cat in optional_accessories if category_images[cat]]
                if len(available_accessories) < 2:
                    messagebox.showwarning("Attenzione", "Non ci sono abbastanza accessori disponibili (minimo 2 richiesti).")
                    continue
                selected_accessories = random.sample(available_accessories, min(max_accessories, len(available_accessories)))

                # Dimensioni degli accessori per categoria
                accessory_sizes = {
                    "occhiali": (0.15 * size_accessory_factor, 0.15 * size_main_factor),
                    "wallet": (0.15 * size_accessory_factor, 0.15 * size_main_factor),
                    "profumi": (0.2 * size_accessory_factor, 0.2 * size_main_factor),
                    "bracciali": (0.1 * size_accessory_factor, 0.1 * size_main_factor),
                    "orologi": (0.1 * size_accessory_factor, 0.1 * size_main_factor),
                    "cinture": (0.2 * size_accessory_factor, 0.2 * size_main_factor),
                    "scarpe": (0.25 * size_accessory_factor, 0.25 * size_main_factor),
                    "auto": (0.4 * size_accessory_factor, 0.4 * size_main_factor)
                }

                for accessory in selected_accessories:
                    item_data = random.choice(category_images[accessory])
                    item_img = self.fix_image_orientation(Image.open(item_data[0]).convert("RGBA"))
                    max_width = int((width - 150) * accessory_sizes[accessory][0])
                    max_height = int((height - 200) * accessory_sizes[accessory][1])
                    item_img = self.resize_image(item_img, max_width, max_height)
                    item_name = item_data[1]

                    # Posizionamento logico in base alla categoria
                    if accessory == "occhiali":
                        x = shirt_x + (shirt_img.width - item_img.width) // 2
                        y = shirt_y - item_img.height - 10
                    elif accessory in ["bracciali", "orologi"]:
                        side = random.choice(["left", "right"])
                        x = shirt_x - item_img.width - 20 if side == "left" else shirt_x + shirt_img.width + 20
                        y = shirt_y + shirt_img.height // 2
                    elif accessory == "cinture":
                        x = shirt_x + (shirt_img.width - item_img.width) // 2
                        y = shirt_y + shirt_img.height + spacing // 2
                    elif accessory == "scarpe":
                        x = pants_x + (pants_img.width - item_img.width) // 2
                        y = pants_y + pants_img.height + 20
                    elif accessory == "auto":
                        x = random.choice([0, width - 150 - item_img.width])
                        y = height - 125 - item_img.height
                    else:  # wallet, profumi
                        side = random.choice(["left", "right"])
                        x = shirt_x - item_img.width - 50 if side == "left" else shirt_x + shirt_img.width + 50
                        y = shirt_y + self.safe_randint(0, shirt_img.height)

                    # Verifica sicurezza posizione
                    attempts = 0
                    max_attempts = 50
                    placed = False
                    while attempts < max_attempts:
                        if self.is_position_safe(x, y, width, height, item_img.width, item_img.height):
                            overlaps = False
                            for occ_x, occ_y, occ_w, occ_h in occupied_areas:
                                if (x < occ_x + occ_w + object_spacing and x + item_img.width > occ_x - object_spacing and
                                    y < occ_y + occ_h + object_spacing and y + item_img.height > occ_y - object_spacing):
                                    overlaps = True
                                    break
                            if not overlaps:
                                placed = True
                                break
                        x += self.safe_randint(-20, 20)
                        y += self.safe_randint(-20, 20)
                        attempts += 1

                    if not placed:
                        continue

                    canvas.paste(item_img, (x, y), item_img)
                    occupied_areas.append((x, y, item_img.width, item_img.height))

                    if show_names.get():
                        text_width = draw.textlength(item_name, font=font) if font else 100
                        text_x = x + (item_img.width - text_width) // 2
                        text_y = y + item_img.height + 10
                        if text_x + text_width > width - 150:
                            text_x = width - 150 - text_width
                        if text_y + font_size > height - 125:
                            text_y = height - 125 - font_size
                        draw.text((text_x, text_y), item_name, font=font, fill=font_color_rgb)
                        occupied_areas.append((text_x, text_y, text_width, font_size))

                # Salva l'immagine
                output_format = format_combo.get().lower()
                base_filename = f"outfit_{i+1}.{output_format}"
                unique_filename = self.get_unique_filename(output_folder, base_filename)
                output_path = os.path.join(output_folder, unique_filename)
                canvas = canvas.convert("RGB") if output_format == "jpg" else canvas
                canvas.save(output_path, quality=95 if output_format == "jpg" else None)

            messagebox.showinfo("Successo", f"{quantity} immagini generate con successo in {output_folder}!")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Errore", f"Si è verificato un errore: {str(e)}")