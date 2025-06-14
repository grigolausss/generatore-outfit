import os
import random
import json
import tkinter as tk
from tkinter import messagebox, colorchooser
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ExifTags, ImageStat
import traceback

class OutfitGeneratorLogic:
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    ACCESSORY_MARGIN = 100  # General margin for accessories from canvas edges
    WATERMARK_MARGIN_TOP = 100
    WATERMARK_MARGIN_BOTTOM_TIKTOK = 200
    ACCESSORY_PRIORITIES = {
       "scarpe": 1, "occhiali": 1, # Highest priority
       "cinture": 2, "orologi": 2,
       "bracciali": 3,
       "wallet": 4, "profumi": 4, # Lower priority
       "auto": 5 # Lowest, or handle separately due to size
    }
    DEFAULT_PRIORITY = 10
    MIN_CONTRAST_THRESHOLD = 2.0
    MIN_TEXT_CONTRAST_THRESHOLD = 3.0

    def __init__(self):
        script_dir = os.path.dirname(os.path.realpath(__file__))

        # Percorsi base - Defaulting to relative paths from the project root
        # Assumes 'il secondo programma' is a subdirectory of the project root.
        self.base_path = os.path.normpath(os.path.join(script_dir, "..", "foto per generatore"))
        self.output_path = os.path.normpath(os.path.join(script_dir, "..", "immagini generate"))
        # Watermark path is initialized here but typically overridden by GUI selection.
        # Keeping the original specific path as a placeholder default.
        self.watermark_path = "/Users/grigolausss/Desktop/WhisperMind/logo/logo nuovo senza sfondo.PNG"
        self.fonts_path = os.path.normpath(os.path.join(script_dir, "..", "fonts"))
        self.palette_file = "custom_background_palette.json" # Relative to script/execution dir

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

    def is_position_safe(self, x, y, item_w, item_h):
        safe_left = self.ACCESSORY_MARGIN
        safe_top = self.ACCESSORY_MARGIN
        safe_right = self.TARGET_WIDTH - self.ACCESSORY_MARGIN
        safe_bottom = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN

        return (x >= safe_left and x + item_w <= safe_right and
                y >= safe_top and y + item_h <= safe_bottom)

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

    def generate_outfits(self, width_entry, height_entry, quantity_spinbox, output_entry, format_combo, show_names, use_watermark, watermark_path_var, watermark_position, selected_font, blur_slider, brightness_slider, spacing_slider, size_main_slider, size_accessory_slider, accessory_count_slider_obj, actual_object_spacing_slider_obj, font_color_rgb, root):
        try:
            width = int(width_entry.get()) # Retained for potential legacy use, TARGET_WIDTH/HEIGHT is primary
            height = int(height_entry.get()) # Retained for potential legacy use, TARGET_WIDTH/HEIGHT is primary
            quantity = int(quantity_spinbox.get())
            output_folder = output_entry.get()

            if not output_folder or not os.path.exists(output_folder): # Ensure output folder is selected and exists
                messagebox.showerror("Errore", "Seleziona una cartella di salvataggio valida.")
                return

            # Check if essential category paths are selected (assuming tk.StringVar for paths)
            # If category_paths stores StringVars from the GUI, .get() would be needed here.
            # Current implementation assumes paths are direct strings after __init__ or GUI updates.
            if not self.category_paths.get("maglie") or not self.load_images_from_folder(self.category_paths["maglie"]):
                 messagebox.showerror("Errore", "La cartella 'maglie' non è selezionata o non contiene immagini.")
                 return
            if not self.category_paths.get("pantaloni") or not self.load_images_from_folder(self.category_paths["pantaloni"]):
                 messagebox.showerror("Errore", "La cartella 'pantaloni' non è selezionata o non contiene immagini.")
                 return
            if not self.category_paths.get("sfondi") or not self.load_images_from_folder(self.category_paths["sfondi"]):
                 messagebox.showerror("Errore", "La cartella 'sfondi' non è selezionata o non contiene immagini.")
                 return

            category_images = {category: self.load_images_from_folder(self.category_paths[category]) for category in self.accessory_types if self.category_paths.get(category)}


            optional_accessories = [cat for cat in self.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]]
            # Corrected: Use accessory_count_slider_obj for max_accessories
            max_accessories = max(2, accessory_count_slider_obj.get())

            font = None
            font_size = 30 # Default font size
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
                canvas = Image.new("RGBA", (self.TARGET_WIDTH, self.TARGET_HEIGHT), (255, 255, 255, 0))

                # Sfondo
                if random.random() < 0.6:
                    background = self.neutral_background(self.TARGET_WIDTH, self.TARGET_HEIGHT)
                else:
                    background_path = random.choice([img[0] for img in category_images["sfondi"]])
                    background = self.fix_image_orientation(Image.open(background_path).convert("RGBA"))
                    background = background.resize((self.TARGET_WIDTH, self.TARGET_HEIGHT), Image.Resampling.LANCZOS)

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
                # Corrected: Use actual_object_spacing_slider_obj for object_spacing
                object_spacing = actual_object_spacing_slider_obj.get() * 2
                # spacing is for vertical distance between shirt and pants
                spacing = spacing_slider.get() * 3

                content_width_for_main_items = self.TARGET_WIDTH - 2 * self.ACCESSORY_MARGIN
                content_height_for_main_items = self.TARGET_HEIGHT - 2 * self.ACCESSORY_MARGIN

                # Dimensioni degli oggetti principali
                shirt_max_width = int(content_width_for_main_items * 0.5 * size_main_factor)
                shirt_max_height = int(content_height_for_main_items * 0.35 * size_main_factor)
                pants_max_width = int(content_width_for_main_items * 0.5 * size_main_factor)
                pants_max_height = int(content_height_for_main_items * 0.35 * size_main_factor)

                # Carica maglia e pantaloni
                shirt_data = random.choice(category_images["maglie"])
                shirt_img = self.fix_image_orientation(Image.open(shirt_data[0]).convert("RGBA"))
                shirt_img = self.resize_image(shirt_img, shirt_max_width, shirt_max_height)
                shirt_name = shirt_data[1]

                pants_data = random.choice(category_images["pantaloni"])
                pants_img = self.fix_image_orientation(Image.open(pants_data[0]).convert("RGBA"))
                pants_img = self.resize_image(pants_img, pants_max_width, pants_max_height)
                pants_name = pants_data[1]

                # --- Main Garment Placement Strategy ---
                # Randomly chooses 'center', 'left', or 'right' for the main garment block.
                placement_options = ['center', 'left', 'right']
                chosen_placement = random.choice(placement_options)

                # Usable area for content, excluding accessory margins.
                content_width = self.TARGET_WIDTH - 2 * self.ACCESSORY_MARGIN
                content_height = self.TARGET_HEIGHT - 2 * self.ACCESSORY_MARGIN # For vertical centering of garment block

                # X-coordinate calculation based on chosen placement
                offset_amount = content_width // 7 # Amount to shift for 'left'/'right' placements

                if chosen_placement == 'center':
                    shirt_x = self.ACCESSORY_MARGIN + (content_width - shirt_img.width) // 2
                    pants_x = self.ACCESSORY_MARGIN + (content_width - pants_img.width) // 2
                elif chosen_placement == 'left':
                    # Calculate centered position first, then apply offset
                    base_center_x_shirt = self.ACCESSORY_MARGIN + (content_width - shirt_img.width) // 2
                    base_center_x_pants = self.ACCESSORY_MARGIN + (content_width - pants_img.width) // 2
                    shirt_x = base_center_x_shirt - offset_amount
                    pants_x = base_center_x_pants - offset_amount
                elif chosen_placement == 'right':
                    # Calculate centered position first, then apply offset
                    base_center_x_shirt = self.ACCESSORY_MARGIN + (content_width - shirt_img.width) // 2
                    base_center_x_pants = self.ACCESSORY_MARGIN + (content_width - pants_img.width) // 2
                    shirt_x = base_center_x_shirt + offset_amount
                    pants_x = base_center_x_pants + offset_amount

                # Ensure x positions are firmly within accessory margins and don't push content outside visual bounds.
                # The min second argument should be the rightmost allowed start for the image.
                shirt_x = max(self.ACCESSORY_MARGIN, min(shirt_x, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - shirt_img.width))
                pants_x = max(self.ACCESSORY_MARGIN, min(pants_x, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - pants_img.width))

                total_garment_height = shirt_img.height + pants_img.height + spacing

                # Calculate initial Y to center the block within the content height
                shirt_y = self.ACCESSORY_MARGIN + (content_height - total_garment_height) // 2

                # Ensure shirt_y respects the top accessory margin
                shirt_y = max(self.ACCESSORY_MARGIN, shirt_y)

                # Ensure the entire block does not go below the bottom accessory margin
                # (i.e., shirt_y + total_garment_height should not exceed self.TARGET_HEIGHT - self.ACCESSORY_MARGIN)
                if shirt_y + total_garment_height > self.TARGET_HEIGHT - self.ACCESSORY_MARGIN:
                    shirt_y = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - total_garment_height
                    # Re-check against top margin in case of very large items
                    shirt_y = max(self.ACCESSORY_MARGIN, shirt_y)

                pants_y = shirt_y + shirt_img.height + spacing

                canvas.paste(shirt_img, (shirt_x, shirt_y), shirt_img)
                occupied_areas.append((shirt_x, shirt_y, shirt_img.width, shirt_img.height))

                if show_names.get():
                    text_width = draw.textlength(shirt_name, font=font) if font else 100
                    text_x = shirt_x + (shirt_img.width - text_width) // 2
                    text_y = shirt_y + shirt_img.height + 10
                    if text_x + text_width > self.TARGET_WIDTH - self.ACCESSORY_MARGIN:
                        text_x = self.TARGET_WIDTH - self.ACCESSORY_MARGIN - text_width
                    if text_y + font_size > self.TARGET_HEIGHT - self.ACCESSORY_MARGIN: # Using font_size as proxy for text_height
                        text_y = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - font_size
                    font_color = font_color_rgb
                    draw.text((text_x, text_y), shirt_name, font=font, fill=font_color)
                    occupied_areas.append((text_x, text_y, text_width, font_size))

                canvas.paste(pants_img, (pants_x, pants_y), pants_img)
                occupied_areas.append((pants_x, pants_y, pants_img.width, pants_img.height))

                if show_names.get():
                    text_width = draw.textlength(pants_name, font=font) if font else 100
                    text_x = pants_x + (pants_img.width - text_width) // 2
                    text_y = pants_y + pants_img.height + 10
                    if text_x + text_width > self.TARGET_WIDTH - self.ACCESSORY_MARGIN:
                        text_x = self.TARGET_WIDTH - self.ACCESSORY_MARGIN - text_width
                    if text_y + font_size > self.TARGET_HEIGHT - self.ACCESSORY_MARGIN: # Using font_size as proxy for text_height
                        text_y = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - font_size
                    font_color = font_color_rgb
                    draw.text((text_x, text_y), pants_name, font=font, fill=font_color)
                    occupied_areas.append((text_x, text_y, text_width, font_size))

                # Posizionamento watermark (DO THIS AFTER ALL ITEMS AND THEIR TEXT ARE PLACED)
                # The code structure should be:
                # 1. Place shirt, pants + their text names (add to occupied_areas)
                # 2. Place accessories + their text names (add to occupied_areas)
                # 3. Then, do watermark logic. (This means moving this block further down if it's not already)
                # Assuming this block is already correctly positioned logically after all items and names:

                if use_watermark.get() and watermark_path_var.get():
                    watermark_original = self.fix_image_orientation(Image.open(watermark_path_var.get()).convert("RGBA"))

                    max_wm_width = int(self.TARGET_WIDTH * 0.25)
                    watermark = watermark_original # Use 'watermark' for the potentially resized version

                    if watermark.width > max_wm_width:
                        aspect_ratio = watermark.height / watermark.width
                        new_wm_width = max_wm_width
                        new_wm_height = int(new_wm_width * aspect_ratio)
                        if new_wm_height > 0:
                            watermark = watermark.resize((new_wm_width, new_wm_height), Image.Resampling.LANCZOS)
                        else:
                            print(f"Warning: Watermark ({watermark_path_var.get()}) resized to zero height. Skipping.")
                            watermark = None # Skip if resizing leads to invalid dimensions

                    if watermark: # Proceed if watermark is valid
                        padding_top = self.WATERMARK_MARGIN_TOP
                        padding_bottom = self.WATERMARK_MARGIN_BOTTOM_TIKTOK

                        if watermark_position.get() == "Sopra":
                            wm_y = padding_top
                        else: # "Sotto"
                            wm_y = self.TARGET_HEIGHT - watermark.height - padding_bottom

                        wm_x = (self.TARGET_WIDTH - watermark.width) // 2

                        watermark_rect = (wm_x, wm_y, watermark.width, watermark.height)
                        watermark_overlaps = False
                        for occ_x, occ_y, occ_w, occ_h in occupied_areas:
                            if (watermark_rect[0] < occ_x + occ_w and
                                watermark_rect[0] + watermark_rect[2] > occ_x and
                                watermark_rect[1] < occ_y + occ_h and
                                watermark_rect[1] + watermark_rect[3] > occ_y):
                                watermark_overlaps = True
                                break

                        if not watermark_overlaps:
                            canvas.paste(watermark, (wm_x, wm_y), watermark)
                            # DO NOT add to occupied_areas as per instruction for one-way overlap check
                        else:
                            print(f"Warning: Watermark placement at ({wm_x}, {wm_y}) would overlap with existing items. Skipping watermark.")

                # ---- Accessory Placement Setup ----
                # Defines zones (left/right of garments) based on main garment placement.
                # `object_spacing` is used to ensure accessories don't touch the garment block directly.
                garment_block_x_start = min(shirt_x, pants_x)
                garment_block_x_end = max(shirt_x + shirt_img.width, pants_x + pants_img.width)

                accessory_zones = []
                zone_y_start = self.ACCESSORY_MARGIN
                zone_y_end = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN

                if chosen_placement == 'center':
                    # Zone to the left of centered garments
                    accessory_zones.append({
                        "id": "left_of_center",
                        "x_start": self.ACCESSORY_MARGIN,
                        "x_end": garment_block_x_start - object_spacing,
                        "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "left"
                    })
                    # Zone to the right of centered garments
                    accessory_zones.append({
                        "id": "right_of_center",
                        "x_start": garment_block_x_end + object_spacing,
                        "x_end": self.TARGET_WIDTH - self.ACCESSORY_MARGIN,
                        "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "right"
                    })
                elif chosen_placement == 'left':
                    # Primary zone is to the right of left-placed garments
                    accessory_zones.append({
                        "id": "right_of_left_garments",
                        "x_start": garment_block_x_end + object_spacing,
                        "x_end": self.TARGET_WIDTH - self.ACCESSORY_MARGIN,
                        "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "right"
                    })
                elif chosen_placement == 'right':
                    # Primary zone is to the left of right-placed garments
                    accessory_zones.append({
                        "id": "left_of_right_garments",
                        "x_start": self.ACCESSORY_MARGIN,
                        "x_end": garment_block_x_start - object_spacing,
                        "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "left"
                    })

                # Filter out zones that are too narrow or short.
                accessory_zones = [z for z in accessory_zones if z["x_end"] - z["x_start"] > 50 and z["y_end"] - z["y_start"] > 50]

                # Fallback: If specific zones are invalid (e.g., garments too wide), use the whole content area.
                if not accessory_zones:
                     accessory_zones.append({
                        "id": "full_content_area_fallback",
                        "x_start": self.ACCESSORY_MARGIN, "x_end": self.TARGET_WIDTH - self.ACCESSORY_MARGIN,
                        "y_start": self.ACCESSORY_MARGIN, "y_end": self.TARGET_HEIGHT - self.ACCESSORY_MARGIN,
                        "target_side": "none"
                    })

                # --- Accessory Selection and Prioritization ---
                # Selects accessories based on defined priorities and available images.
                # `optional_accessories` was defined earlier.
                available_accessories_with_images = [cat for cat in optional_accessories if category_images.get(cat)] # Check if cat images are loaded

                # Sorts by priority (lower number = higher priority), then shuffles within each priority group.
                sorted_accessories = sorted(
                    available_accessories_with_images,
                    key=lambda cat: (self.ACCESSORY_PRIORITIES.get(cat, self.DEFAULT_PRIORITY), random.random())
                )

                num_to_select = min(max_accessories, len(sorted_accessories))
                selected_accessories = sorted_accessories[:num_to_select] # Top N accessories are selected.
                # These will be attempted for placement in this priority order.

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
                    item_img_original = self.fix_image_orientation(Image.open(item_data[0]).convert("RGBA"))

                    # Resize based on category-specific factors, using content_width/height as reference
                    size_rules = accessory_sizes.get(accessory, (0.15, 0.15)) # Default size if not in rules
                    max_item_w = int(content_width_for_main_items * size_rules[0] * size_accessory_factor)
                    max_item_h = int(content_height_for_main_items * size_rules[1] * size_accessory_factor)
                    item_img = self.resize_image(item_img_original, max_item_w, max_item_h)
                    item_name = item_data[1]

                    # --- Initial Semantic Placement ---
                    x, y = 0, 0 # Default, will be updated

                    if accessory == "occhiali":
                        x = shirt_x + (shirt_img.width - item_img.width) // 2
                        y = shirt_y - item_img.height - (object_spacing // 4 if object_spacing > 10 else 5) # Place slightly above shirt
                    elif accessory == "cinture":
                        x = shirt_x + (shirt_img.width - item_img.width) // 2
                        y = shirt_y + shirt_img.height - item_img.height // 2 + spacing // 3 # Between shirt and pants like
                    elif accessory == "scarpe":
                        x = pants_x + (pants_img.width - item_img.width) // 2
                        y = pants_y + pants_img.height + (object_spacing // 4 if object_spacing > 10 else 5)
                    elif accessory == "auto": # Special handling for 'auto'
                        # Try to place in the largest available zone, or fallback to margin-aware placement
                        if accessory_zones:
                            largest_zone = max(accessory_zones, key=lambda z: (z["x_end"] - z["x_start"]) * (z["y_end"] - z["y_start"]))
                            x = largest_zone["x_start"] + (largest_zone["x_end"] - largest_zone["x_start"] - item_img.width) // 2
                            y = largest_zone["y_start"] + (largest_zone["y_end"] - largest_zone["y_start"] - item_img.height) // 2
                        else: # Fallback if no zones defined (should not happen with the fallback zone logic)
                            x = random.choice([self.ACCESSORY_MARGIN, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - item_img.width])
                            y = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - item_img.height
                    # For "bracciali", "orologi", "wallet", "profumi", we'll let the zone selection guide initial x,y more directly.
                    # Their initial x,y will be calculated within the chosen zone during the attempt loop.

                    # --- Collision Avoidance and Zone-based Placement Loop ---
                    attempts = 0
                    max_attempts_per_zone = 15
                    max_total_attempts = 50
                    placed = False

                    # Store semantic starting point if calculated, otherwise it will be zone-based
                    semantic_x, semantic_y = x, y

                    # Shuffle zones to try different areas if the first choice is crowded
                    shuffled_zones = random.sample(accessory_zones, len(accessory_zones)) if accessory_zones else []

                    for current_zone in shuffled_zones:
                        if placed: break

                        # Determine initial placement within the current_zone
                        # For specific items, use semantic. For others, center in zone or random.
                        if accessory in ["occhiali", "cinture", "scarpe"]:
                            current_x = semantic_x
                            current_y = semantic_y
                        elif accessory in ["bracciali", "orologi"]:
                             # Try to place on the target_side of the zone, near garments
                            if current_zone["target_side"] == "left":
                                current_x = current_zone["x_end"] - item_img.width - (object_spacing //2) # Near garment block
                            elif current_zone["target_side"] == "right":
                                current_x = current_zone["x_start"] + (object_spacing //2) # Near garment block
                            else: # center placement
                                current_x = current_zone["x_start"] + (current_zone["x_end"] - current_zone["x_start"] - item_img.width) // 2
                            current_y = shirt_y + shirt_img.height // 3 # Example y, adjust per item

                        else: # "wallet", "profumi", etc. - more flexible
                            current_x = random.randint(current_zone["x_start"], max(current_zone["x_start"], current_zone["x_end"] - item_img.width))
                            current_y = random.randint(current_zone["y_start"], max(current_zone["y_start"], current_zone["y_end"] - item_img.height))


                        for attempt_in_zone in range(max_attempts_per_zone):
                            if attempts >= max_total_attempts: break

                            shift_x = random.randint(-15, 15)
                            shift_y = random.randint(-15, 15)
                            final_x = current_x + shift_x
                            final_y = current_y + shift_y

                            # Clamp to current zone boundaries
                            final_x = max(current_zone["x_start"], min(final_x, current_zone["x_end"] - item_img.width))
                            final_y = max(current_zone["y_start"], min(final_y, current_zone["y_end"] - item_img.height))

                            # Final check against overall canvas safety using ACCESSORY_MARGIN (is_position_safe)
                            if not self.is_position_safe(final_x, final_y, item_img.width, item_img.height):
                                attempts += 1
                                continue

                            overlaps = False
                            for occ_x, occ_y, occ_w, occ_h in occupied_areas:
                                if (final_x < occ_x + occ_w + object_spacing and
                                    final_x + item_img.width > occ_x - object_spacing and
                                    final_y < occ_y + occ_h + object_spacing and
                                    final_y + item_img.height > occ_y - object_spacing):
                                    overlaps = True
                                    break

                            if not overlaps:
                                x, y = final_x, final_y
                                placed = True
                                break
                            attempts += 1
                        if placed: break

                    if not placed:
                        continue

                    canvas.paste(item_img, (x, y), item_img)
                    occupied_areas.append((x, y, item_img.width, item_img.height))

                    if show_names.get():
                        text_width = draw.textlength(item_name, font=font) if font else 100 # Get text width
                        # Ensure text_x is within bounds
                        text_x = x + (item_img.width - text_width) // 2
                        text_x = max(self.ACCESSORY_MARGIN, min(text_x, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - text_width))

                        # Ensure text_y is within bounds
                        text_y = y + item_img.height + 5 # Small gap for text below item
                        text_y = max(self.ACCESSORY_MARGIN, min(text_y, self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - font_size))

                        # Check if text placement itself is safe (not overlapping other things)
                        # This is a simplified check; a more robust check would add text bounds to occupied_areas
                        # For now, rely on the general clamping and hope for the best for text overlaps.
                        draw.text((text_x, text_y), item_name, font=font, fill=font_color_rgb)
                        # Optionally, add text bounding box to occupied_areas if text overlap becomes an issue
                        # occupied_areas.append((text_x, text_y, text_width, font_size))

                # Salva l'immagine
                # **IMPORTANT**: The watermark logic MUST be executed AFTER all item names are drawn and added to occupied_areas
                # but BEFORE this "Salva l'immagine" step.
                # The previous diff block for watermark placement should conceptually be here if it's not already.

                output_format = format_combo.get().lower()
                base_filename = f"outfit_{i+1}.{output_format}" # Ensure i is defined in this scope; it comes from the loop `for i in range(quantity):`
                unique_filename = self.get_unique_filename(output_folder, base_filename)
                output_path = os.path.join(output_folder, unique_filename)
                canvas = canvas.convert("RGB") if output_format == "jpg" else canvas
                canvas.save(output_path, quality=95 if output_format == "jpg" else None)

            messagebox.showinfo("Successo", f"{quantity} immagini generate con successo in {output_folder}!")
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Errore", f"Si è verificato un errore: {str(e)}")

    # Helper functions for contrast check
    def get_average_color(self, image_obj, box=None):
        target_image = image_obj
        if box:
            try:
                target_image = image_obj.crop(box)
            except Exception as e: # Catch potential errors with invalid box
                # print(f"Error cropping image for avg color: {e}. Using uncropped image.")
                # Fallback to uncropped might be problematic if image_obj is the whole canvas
                # Better to return a default if box is bad.
                return (128, 128, 128)


        if target_image.width == 0 or target_image.height == 0:
            return (128, 128, 128)

        if target_image.mode == 'RGBA':
            alpha = target_image.split()[-1]
            mask = Image.eval(alpha, lambda a: 255 if a > 50 else 0)
            if not mask.getbbox():
                 return (128,128,128)
            try:
                stat = ImageStat.Stat(target_image, mask)
            except Exception:
                stat = ImageStat.Stat(target_image.convert('RGB'))
        else:
            stat = ImageStat.Stat(target_image.convert('RGB'))

        if not stat.count or stat.count[0] == 0: return (128, 128, 128)
        return tuple(map(int, stat.mean[:3]))

    def get_relative_luminance(self, rgb_tuple):
        r, g, b = [x / 255.0 for x in rgb_tuple]
        return 0.299 * r + 0.587 * g + 0.114 * b

    def get_contrast_ratio(self, lum1, lum2):
        l1 = max(lum1, lum2)
        l2 = min(lum1, lum2)
        return (l1 + 0.05) / (l2 + 0.05)

    def generate_single_outfit_preview(self, width_entry, height_entry, show_names, use_watermark, watermark_path_var, watermark_position, selected_font, blur_slider_val, brightness_slider_val, spacing_slider_val, size_main_slider_val, size_accessory_slider_val, accessory_count_val, object_spacing_val, font_color_rgb, root):
        try:
            # width and height from entry are not directly used for canvas size, TARGET_WIDTH/HEIGHT are.
            # They might be used for other calculations if not refactored out yet.
            # For preview, these specific entries might be less relevant if a fixed preview size is desired.
            # However, keeping them for consistency with generate_outfits structure for now.
            width = int(width_entry.get())
            height = int(height_entry.get())

            # Directly use passed values from sliders
            blur_value = blur_slider_val
            brightness_value = brightness_slider_val
            spacing = spacing_slider_val * 3 # Matches original logic: spacing_slider.get() * 3
            size_main_factor = size_main_slider_val / 100
            size_accessory_factor = size_accessory_slider_val / 100
            max_accessories = max(2, accessory_count_val) # Renamed from object_spacing_slider
            object_spacing = object_spacing_val * 2 # Renamed from object_spacing_slider

            # Path checks for essential categories (assuming self.category_paths holds tk.StringVar or similar)
            # For a preview, direct path access might be more robust if GUI elements aren't fully stable.
            # This logic is retained from generate_outfits.
            if not self.category_paths["maglie"].get() or not self.category_paths["pantaloni"].get() or not self.category_paths["sfondi"].get():
                messagebox.showerror("Errore", "Seleziona almeno le cartelle per Maglie, Pantaloni e Sfondi.")
                return None

            category_images = {category: self.load_images_from_folder(self.category_paths[category].get()) for category in self.accessory_types}

            if not category_images["maglie"]:
                messagebox.showerror("Errore", "La cartella 'maglie' non contiene immagini valide.")
                return None
            if not category_images["pantaloni"]:
                messagebox.showerror("Errore", "La cartella 'pantaloni' non contiene immagini valide.")
                return None
            if not category_images["sfondi"]: # Check for sfondi (backgrounds)
                messagebox.showerror("Errore", "La cartella 'sfondi' non contiene immagini valide.")
                return None


            font = None
            font_size = 30 # Default font size, consider making this a parameter if variable
            if show_names.get():
                selected_font_name = selected_font.get()
                if selected_font_name == "Random":
                    available_font_names = [f for f in self.available_fonts if f != "Random"]
                    if available_font_names:
                        selected_font_name = random.choice(available_font_names)
                    else:
                        selected_font_name = None # Fallback if only "Random" and no actual fonts

                if selected_font_name and selected_font_name in self.font_objects:
                    try:
                        font = ImageFont.truetype(self.font_objects[selected_font_name], font_size)
                    except Exception as e:
                        messagebox.showwarning("Attenzione", f"Errore nel caricamento del font: {e}. Uso font predefinito.")
                        font = ImageFont.load_default()
                elif selected_font_name: # Font name selected but not found in objects (should not happen with proper loading)
                     messagebox.showwarning("Attenzione", f"Font '{selected_font_name}' selezionato ma non trovato. Uso font predefinito.")
                     font = ImageFont.load_default()
                else: # No font selected or "Random" yielded no font
                    font = ImageFont.load_default()


            # --- Start of single image generation (adapted from the loop in generate_outfits) ---
            canvas = Image.new("RGBA", (self.TARGET_WIDTH, self.TARGET_HEIGHT), (255, 255, 255, 0))

            # Sfondo
            if random.random() < 0.6: # 60% chance for neutral background
                background = self.neutral_background(self.TARGET_WIDTH, self.TARGET_HEIGHT)
            else:
                # Ensure 'sfondi' images are available before choosing
                sfondi_images = category_images.get("sfondi", [])
                if not sfondi_images: # Should have been caught by initial checks, but as a safeguard
                    messagebox.showerror("Errore", "Nessuna immagine di sfondo disponibile per la generazione.")
                    return None # Or use neutral background as fallback
                background_path = random.choice([img[0] for img in sfondi_images])
                background = self.fix_image_orientation(Image.open(background_path).convert("RGBA"))
                background = background.resize((self.TARGET_WIDTH, self.TARGET_HEIGHT), Image.Resampling.LANCZOS)

            # Effetti sfondo
            if blur_value > 0:
                background = background.filter(ImageFilter.GaussianBlur(blur_value))

            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(1 + brightness_value / 100)

            canvas.paste(background, (0, 0))
            draw = ImageDraw.Draw(canvas)
            occupied_areas = [] # Stores (x, y, w, h) of placed items and text

            # Calculate max dimensions for main garments based on content area and scaling factors
            content_width_for_main_items = self.TARGET_WIDTH - 2 * self.ACCESSORY_MARGIN
            content_height_for_main_items = self.TARGET_HEIGHT - 2 * self.ACCESSORY_MARGIN

            shirt_max_width = int(content_width_for_main_items * 0.5 * size_main_factor)
            shirt_max_height = int(content_height_for_main_items * 0.35 * size_main_factor)
            pants_max_width = int(content_width_for_main_items * 0.5 * size_main_factor)
            pants_max_height = int(content_height_for_main_items * 0.35 * size_main_factor)

            # Load and resize main garments
            # Ensure 'maglie' and 'pantaloni' images are available
            if not category_images.get("maglie"): return None # Should be caught earlier
            shirt_data = random.choice(category_images["maglie"])
            shirt_img = self.fix_image_orientation(Image.open(shirt_data[0]).convert("RGBA"))
            shirt_img = self.resize_image(shirt_img, shirt_max_width, shirt_max_height)
            shirt_name = shirt_data[1]

            if not category_images.get("pantaloni"): return None # Should be caught earlier
            pants_data = random.choice(category_images["pantaloni"])
            pants_img = self.fix_image_orientation(Image.open(pants_data[0]).convert("RGBA"))
            pants_img = self.resize_image(pants_img, pants_max_width, pants_max_height)
            pants_name = pants_data[1]

            # --- Main Garment Placement Strategy ---
            # Determines if the shirt/pants block is centered, or shifted left/right.
            placement_options = ['center', 'left', 'right']
            chosen_placement = random.choice(placement_options) # Randomly select one strategy

            # Usable width and height for content, excluding margins
            content_width = self.TARGET_WIDTH - 2 * self.ACCESSORY_MARGIN
            content_height = self.TARGET_HEIGHT - 2 * self.ACCESSORY_MARGIN # For vertical centering

            # Offset for 'left'/'right' placements
            offset_amount = content_width // 7 # Arbitrary shift amount, 1/7th of content width

            # Calculate X coordinates based on chosen placement
            if chosen_placement == 'center':
                shirt_x = self.ACCESSORY_MARGIN + (content_width - shirt_img.width) // 2
                pants_x = self.ACCESSORY_MARGIN + (content_width - pants_img.width) // 2
            elif chosen_placement == 'left':
                base_center_x_shirt = self.ACCESSORY_MARGIN + (content_width - shirt_img.width) // 2
                base_center_x_pants = self.ACCESSORY_MARGIN + (content_width - pants_img.width) // 2
                shirt_x = base_center_x_shirt - offset_amount
                pants_x = base_center_x_pants - offset_amount
            elif chosen_placement == 'right':
                base_center_x_shirt = self.ACCESSORY_MARGIN + (content_width - shirt_img.width) // 2
                base_center_x_pants = self.ACCESSORY_MARGIN + (content_width - pants_img.width) // 2
                shirt_x = base_center_x_shirt + offset_amount
                pants_x = base_center_x_pants + offset_amount

            shirt_x = max(self.ACCESSORY_MARGIN, min(shirt_x, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - shirt_img.width))
            pants_x = max(self.ACCESSORY_MARGIN, min(pants_x, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - pants_img.width))

            total_garment_height = shirt_img.height + pants_img.height + spacing
            shirt_y = self.ACCESSORY_MARGIN + (content_height - total_garment_height) // 2
            shirt_y = max(self.ACCESSORY_MARGIN, shirt_y)
            if shirt_y + total_garment_height > self.TARGET_HEIGHT - self.ACCESSORY_MARGIN:
                shirt_y = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - total_garment_height
                shirt_y = max(self.ACCESSORY_MARGIN, shirt_y)
            pants_y = shirt_y + shirt_img.height + spacing

            canvas.paste(shirt_img, (shirt_x, shirt_y), shirt_img)
            occupied_areas.append((shirt_x, shirt_y, shirt_img.width, shirt_img.height))
            # Contrast check for shirt
            shirt_box_on_canvas = (shirt_x, shirt_y, shirt_x + shirt_img.width, shirt_y + shirt_img.height)
            avg_shirt_color = self.get_average_color(shirt_img)
            avg_bg_color_shirt = self.get_average_color(canvas, box=shirt_box_on_canvas)
            lum_shirt = self.get_relative_luminance(avg_shirt_color)
            lum_bg_shirt = self.get_relative_luminance(avg_bg_color_shirt)
            contrast_shirt = self.get_contrast_ratio(lum_shirt, lum_bg_shirt)
            if contrast_shirt < self.MIN_CONTRAST_THRESHOLD:
                print(f"Warning: Low contrast ({contrast_shirt:.2f}) for SHIRT. Item color: {avg_shirt_color}, Bg color: {avg_bg_color_shirt}")

            if show_names.get():
                text_width_shirt = draw.textlength(shirt_name, font=font) if font else 0
                text_x_shirt = shirt_x + (shirt_img.width - text_width_shirt) // 2
                text_y_shirt = shirt_y + shirt_img.height + 5 # Small gap
                text_x_shirt = max(self.ACCESSORY_MARGIN, min(text_x_shirt, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - text_width_shirt))
                text_y_shirt = max(self.ACCESSORY_MARGIN, min(text_y_shirt, self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - font_size))
                draw.text((text_x_shirt, text_y_shirt), shirt_name, font=font, fill=font_color_rgb)
                if text_width_shirt > 0 :
                    occupied_areas.append((text_x_shirt, text_y_shirt, text_width_shirt, font_size))
                    # Contrast check for shirt text
                    text_bbox_shirt = (text_x_shirt, text_y_shirt, text_x_shirt + text_width_shirt, text_y_shirt + font_size)
                    avg_text_bg_color_shirt = self.get_average_color(canvas, box=text_bbox_shirt)
                    lum_text_shirt = self.get_relative_luminance(font_color_rgb)
                    lum_text_bg_shirt = self.get_relative_luminance(avg_text_bg_color_shirt)
                    text_contrast_shirt = self.get_contrast_ratio(lum_text_shirt, lum_text_bg_shirt)
                    if text_contrast_shirt < self.MIN_TEXT_CONTRAST_THRESHOLD:
                        print(f"Warning: Low contrast ({text_contrast_shirt:.2f}) for SHIRT TEXT '{shirt_name}'. Text: {font_color_rgb}, Bg: {avg_text_bg_color_shirt}")


            canvas.paste(pants_img, (pants_x, pants_y), pants_img)
            occupied_areas.append((pants_x, pants_y, pants_img.width, pants_img.height))
            # Contrast check for pants
            pants_box_on_canvas = (pants_x, pants_y, pants_x + pants_img.width, pants_y + pants_img.height)
            avg_pants_color = self.get_average_color(pants_img)
            avg_bg_color_pants = self.get_average_color(canvas, box=pants_box_on_canvas)
            lum_pants = self.get_relative_luminance(avg_pants_color)
            lum_bg_pants = self.get_relative_luminance(avg_bg_color_pants)
            contrast_pants = self.get_contrast_ratio(lum_pants, lum_bg_pants)
            if contrast_pants < self.MIN_CONTRAST_THRESHOLD:
                print(f"Warning: Low contrast ({contrast_pants:.2f}) for PANTS. Item color: {avg_pants_color}, Bg color: {avg_bg_color_pants}")

            if show_names.get():
                text_width_pants = draw.textlength(pants_name, font=font) if font else 0
                text_x_pants = pants_x + (pants_img.width - text_width_pants) // 2
                text_y_pants = pants_y + pants_img.height + 5
                text_x_pants = max(self.ACCESSORY_MARGIN, min(text_x_pants, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - text_width_pants))
                text_y_pants = max(self.ACCESSORY_MARGIN, min(text_y_pants, self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - font_size))
                draw.text((text_x_pants, text_y_pants), pants_name, font=font, fill=font_color_rgb)
                if text_width_pants > 0:
                    occupied_areas.append((text_x_pants, text_y_pants, text_width_pants, font_size))
                    # Contrast check for pants text
                    text_bbox_pants = (text_x_pants, text_y_pants, text_x_pants + text_width_pants, text_y_pants + font_size)
                    avg_text_bg_color_pants = self.get_average_color(canvas, box=text_bbox_pants)
                    lum_text_pants = self.get_relative_luminance(font_color_rgb)
                    lum_text_bg_pants = self.get_relative_luminance(avg_text_bg_color_pants)
                    text_contrast_pants = self.get_contrast_ratio(lum_text_pants, lum_text_bg_pants)
                    if text_contrast_pants < self.MIN_TEXT_CONTRAST_THRESHOLD:
                        print(f"Warning: Low contrast ({text_contrast_pants:.2f}) for PANTS TEXT '{pants_name}'. Text: {font_color_rgb}, Bg: {avg_text_bg_color_pants}")

            # --- Accessory Zone Definition ---
            # Defines areas where accessories can be placed, based on main garment position.
            garment_block_x_start = min(shirt_x, pants_x)
            garment_block_x_end = max(shirt_x + shirt_img.width, pants_x + pants_img.width)
            accessory_zones = []
            zone_y_start = self.ACCESSORY_MARGIN
            zone_y_end = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN # Full height within margins

            if chosen_placement == 'center':
                # Zone to the left of centered garments
                accessory_zones.append({"id": "left_of_center", "x_start": self.ACCESSORY_MARGIN, "x_end": garment_block_x_start - object_spacing, "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "left"})
                # Zone to the right of centered garments
                accessory_zones.append({"id": "right_of_center", "x_start": garment_block_x_end + object_spacing, "x_end": self.TARGET_WIDTH - self.ACCESSORY_MARGIN, "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "right"})
            elif chosen_placement == 'left':
                # Primary zone is to the right of left-placed garments
                accessory_zones.append({"id": "right_of_left_garments", "x_start": garment_block_x_end + object_spacing, "x_end": self.TARGET_WIDTH - self.ACCESSORY_MARGIN, "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "right"})
            elif chosen_placement == 'right':
                # Primary zone is to the left of right-placed garments
                accessory_zones.append({"id": "left_of_right_garments", "x_start": self.ACCESSORY_MARGIN, "x_end": garment_block_x_start - object_spacing, "y_start": zone_y_start, "y_end": zone_y_end, "target_side": "left"})

            # Filter out zones that are too small (e.g., if garments + spacing are very wide)
            accessory_zones = [z for z in accessory_zones if z["x_end"] - z["x_start"] > 50 and z["y_end"] - z["y_start"] > 50] # Min 50px usable width/height

            # Fallback if no specific zones are valid (e.g., garments too wide)
            if not accessory_zones:
                accessory_zones.append({"id": "full_content_area_fallback", "x_start": self.ACCESSORY_MARGIN, "x_end": self.TARGET_WIDTH - self.ACCESSORY_MARGIN, "y_start": self.ACCESSORY_MARGIN, "y_end": self.TARGET_HEIGHT - self.ACCESSORY_MARGIN, "target_side": "none"})

            # --- Accessory Selection by Priority ---
            # Selects which accessories to attempt to place based on predefined priorities.
            optional_accessories = [cat for cat in self.accessory_types if cat not in ["maglie", "pantaloni", "sfondi"]]
            available_accessories_with_images = [cat for cat in optional_accessories if category_images.get(cat)] # Ensure images are loaded

            # Sorts by priority (lower number = higher), then shuffles within each priority group for variety.
            sorted_accessories = sorted(available_accessories_with_images, key=lambda cat: (self.ACCESSORY_PRIORITIES.get(cat, self.DEFAULT_PRIORITY), random.random()))

            num_to_select = min(max_accessories, len(sorted_accessories)) # Use max_accessories from slider
            selected_accessories = sorted_accessories[:num_to_select] # These will be attempted in order.

            accessory_sizes = {"occhiali": (0.15, 0.15),"wallet": (0.15,0.15),"profumi": (0.2,0.2),"bracciali": (0.1,0.1),"orologi": (0.1,0.1),"cinture": (0.2,0.2),"scarpe": (0.25,0.25),"auto": (0.4,0.4)} # Relative size factors

            for accessory in selected_accessories:
                item_data = random.choice(category_images[accessory]) # Pick a random item from the chosen category
                item_img_original = self.fix_image_orientation(Image.open(item_data[0]).convert("RGBA"))
                size_rules = accessory_sizes.get(accessory, (0.15, 0.15))
                max_item_w = int(content_width_for_main_items * size_rules[0] * size_accessory_factor)
                max_item_h = int(content_height_for_main_items * size_rules[1] * size_accessory_factor)
                item_img = self.resize_image(item_img_original, max_item_w, max_item_h)
                item_name = item_data[1]

                x_acc, y_acc = 0,0 # Default for accessory x,y before semantic placement
                if accessory == "occhiali":
                    x_acc = shirt_x + (shirt_img.width - item_img.width) // 2
                    y_acc = shirt_y - item_img.height - (object_spacing // 4 if object_spacing > 10 else 5)
                elif accessory == "cinture":
                    x_acc = shirt_x + (shirt_img.width - item_img.width) // 2
                    y_acc = shirt_y + shirt_img.height - item_img.height // 2 + spacing // 3
                elif accessory == "scarpe":
                    x_acc = pants_x + (pants_img.width - item_img.width) // 2
                    y_acc = pants_y + pants_img.height + (object_spacing // 4 if object_spacing > 10 else 5)
                elif accessory == "auto":
                    if accessory_zones:
                        largest_zone = max(accessory_zones, key=lambda z: (z["x_end"] - z["x_start"]) * (z["y_end"] - z["y_start"]))
                        x_acc = largest_zone["x_start"] + (largest_zone["x_end"] - largest_zone["x_start"] - item_img.width) // 2
                        y_acc = largest_zone["y_start"] + (largest_zone["y_end"] - largest_zone["y_start"] - item_img.height) // 2
                    else:
                        x_acc = random.choice([self.ACCESSORY_MARGIN, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - item_img.width])
                        y_acc = self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - item_img.height

                attempts_acc = 0
                max_attempts_per_zone_acc = 15
                max_total_attempts_acc = 50
                placed_acc = False
                semantic_x_acc, semantic_y_acc = x_acc, y_acc
                shuffled_zones_acc = random.sample(accessory_zones, len(accessory_zones)) if accessory_zones else []

                for current_zone_acc in shuffled_zones_acc:
                    if placed_acc: break
                    current_x_loop, current_y_loop = x_acc, y_acc # Initialize with semantic or default
                    if accessory in ["occhiali", "cinture", "scarpe", "auto"]: # For these, semantic x,y is primary guide
                         current_x_loop, current_y_loop = semantic_x_acc, semantic_y_acc
                    elif accessory in ["bracciali", "orologi"]:
                        if current_zone_acc["target_side"] == "left": current_x_loop = current_zone_acc["x_end"] - item_img.width - (object_spacing //2)
                        elif current_zone_acc["target_side"] == "right": current_x_loop = current_zone_acc["x_start"] + (object_spacing //2)
                        else: current_x_loop = current_zone_acc["x_start"] + (current_zone_acc["x_end"] - current_zone_acc["x_start"] - item_img.width) // 2
                        current_y_loop = shirt_y + shirt_img.height // 3 # Example y
                    else: # wallet, profumi
                        current_x_loop = random.randint(current_zone_acc["x_start"], max(current_zone_acc["x_start"], current_zone_acc["x_end"] - item_img.width))
                        current_y_loop = random.randint(current_zone_acc["y_start"], max(current_zone_acc["y_start"], current_zone_acc["y_end"] - item_img.height))

                    for attempt_in_zone_acc in range(max_attempts_per_zone_acc):
                        if attempts_acc >= max_total_attempts_acc: break
                        shift_x_acc = random.randint(-15, 15)
                        shift_y_acc = random.randint(-15, 15)
                        final_x_acc = current_x_loop + shift_x_acc
                        final_y_acc = current_y_loop + shift_y_acc
                        final_x_acc = max(current_zone_acc["x_start"], min(final_x_acc, current_zone_acc["x_end"] - item_img.width))
                        final_y_acc = max(current_zone_acc["y_start"], min(final_y_acc, current_zone_acc["y_end"] - item_img.height))
                        if not self.is_position_safe(final_x_acc, final_y_acc, item_img.width, item_img.height):
                            attempts_acc += 1; continue
                        overlaps_acc = False
                        for occ_x, occ_y, occ_w, occ_h in occupied_areas:
                            if (final_x_acc < occ_x + occ_w + object_spacing and final_x_acc + item_img.width > occ_x - object_spacing and final_y_acc < occ_y + occ_h + object_spacing and final_y_acc + item_img.height > occ_y - object_spacing):
                                overlaps_acc = True; break
                        if not overlaps_acc:
                            x_acc, y_acc = final_x_acc, final_y_acc; placed_acc = True; break
                        attempts_acc += 1
                    if placed_acc: break
                if not placed_acc: continue

                canvas.paste(item_img, (x_acc, y_acc), item_img)
                occupied_areas.append((x_acc, y_acc, item_img.width, item_img.height))
                # Contrast check for accessory
                acc_box_on_canvas = (x_acc, y_acc, x_acc + item_img.width, y_acc + item_img.height)
                avg_acc_color = self.get_average_color(item_img) # Pass the item's own image
                avg_bg_color_acc = self.get_average_color(canvas, box=acc_box_on_canvas)
                lum_acc = self.get_relative_luminance(avg_acc_color)
                lum_bg_acc = self.get_relative_luminance(avg_bg_color_acc)
                contrast_acc = self.get_contrast_ratio(lum_acc, lum_bg_acc)
                if contrast_acc < self.MIN_CONTRAST_THRESHOLD:
                    print(f"Warning: Low contrast ({contrast_acc:.2f}) for ACCESSORY '{item_name}'. Item color: {avg_acc_color}, Bg: {avg_bg_color_acc}")

                if show_names.get():
                    text_width_acc = draw.textlength(item_name, font=font) if font else 0
                    text_x_acc = x_acc + (item_img.width - text_width_acc) // 2
                    text_y_acc = y_acc + item_img.height + 5
                    text_x_acc = max(self.ACCESSORY_MARGIN, min(text_x_acc, self.TARGET_WIDTH - self.ACCESSORY_MARGIN - text_width_acc))
                    text_y_acc = max(self.ACCESSORY_MARGIN, min(text_y_acc, self.TARGET_HEIGHT - self.ACCESSORY_MARGIN - font_size))
                    draw.text((text_x_acc, text_y_acc), item_name, font=font, fill=font_color_rgb)
                    if text_width_acc > 0:
                        occupied_areas.append((text_x_acc, text_y_acc, text_width_acc, font_size))
                        # Contrast check for accessory text
                        text_bbox_acc = (text_x_acc, text_y_acc, text_x_acc + text_width_acc, text_y_acc + font_size)
                        avg_text_bg_color_acc = self.get_average_color(canvas, box=text_bbox_acc)
                        lum_text_acc = self.get_relative_luminance(font_color_rgb)
                        lum_text_bg_acc = self.get_relative_luminance(avg_text_bg_color_acc)
                        text_contrast_acc = self.get_contrast_ratio(lum_text_acc, lum_text_bg_acc)
                        if text_contrast_acc < self.MIN_TEXT_CONTRAST_THRESHOLD:
                             print(f"Warning: Low contrast ({text_contrast_acc:.2f}) for ACCESSORY TEXT '{item_name}'. Text: {font_color_rgb}, Bg: {avg_text_bg_color_acc}")

            # Watermark (copied and adapted)
            if use_watermark.get() and watermark_path_var.get():
                watermark_original = self.fix_image_orientation(Image.open(watermark_path_var.get()).convert("RGBA"))
                max_wm_width = int(self.TARGET_WIDTH * 0.25)
                watermark = watermark_original
                if watermark.width > max_wm_width:
                    aspect_ratio = watermark.height / watermark.width
                    new_wm_width = max_wm_width
                    new_wm_height = int(new_wm_width * aspect_ratio)
                    if new_wm_height > 0: watermark = watermark.resize((new_wm_width, new_wm_height), Image.Resampling.LANCZOS)
                    else: watermark = None; print(f"Warning: Watermark ({watermark_path_var.get()}) resized to zero height. Skipping.")
                if watermark:
                    padding_top = self.WATERMARK_MARGIN_TOP
                    padding_bottom = self.WATERMARK_MARGIN_BOTTOM_TIKTOK
                    wm_y_pos = padding_top if watermark_position.get() == "Sopra" else self.TARGET_HEIGHT - watermark.height - padding_bottom
                    wm_x_pos = (self.TARGET_WIDTH - watermark.width) // 2
                    watermark_rect = (wm_x_pos, wm_y_pos, watermark.width, watermark.height)
                    watermark_overlaps = False
                    for occ_x, occ_y, occ_w, occ_h in occupied_areas:
                        if (watermark_rect[0] < occ_x + occ_w and watermark_rect[0] + watermark_rect[2] > occ_x and watermark_rect[1] < occ_y + occ_h and watermark_rect[1] + watermark_rect[3] > occ_y):
                            watermark_overlaps = True; break
                    if not watermark_overlaps: canvas.paste(watermark, (wm_x_pos, wm_y_pos), watermark)
                    else: print(f"Warning: Watermark placement at ({wm_x_pos}, {wm_y_pos}) would overlap. Skipping watermark.")

            return canvas

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Errore", f"Si è verificato un errore durante la generazione dell'anteprima: {str(e)}")
            return None