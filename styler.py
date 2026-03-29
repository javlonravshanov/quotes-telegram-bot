"""
styler.py — Quote image renderer with 5 Instagram styles.
All output: 1080x1080 pixels
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import textwrap
import os
import uuid
import random
import io

# ─── Font paths ───────────────────────────────────────────────────────────────
FONT_POPPINS_BOLD    = "/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
FONT_POPPINS_REG     = "/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf"
FONT_POPPINS_LIGHT   = "/usr/share/fonts/truetype/google-fonts/Poppins-Light.ttf"
FONT_LORA            = "/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf"
FONT_CALADEA         = "/usr/share/fonts/truetype/crosextra/Caladea-Regular.ttf"
FONT_CALADEA_BOLD    = "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf"
FONT_DEJAVU_SERIF    = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_DEJAVU_SERIF_IT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf"

SIZE = (1080, 1080)
OUT_DIR = "/tmp"


def _save(img: Image.Image) -> str:
    path = os.path.join(OUT_DIR, f"quote_{uuid.uuid4().hex[:8]}.jpg")
    img = img.convert("RGB")
    img.save(path, "JPEG", quality=95)
    return path


def _load_photo(photo_bytes: bytes) -> Image.Image:
    img = Image.open(io.BytesIO(photo_bytes)).convert("RGBA")
    # Crop to square from center
    w, h = img.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    img = img.crop((left, top, left + side, top + side))
    return img.resize(SIZE, Image.LANCZOS)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines = []
    current = ""
    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    for word in words:
        test = (current + " " + word).strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _draw_centered_text(draw, lines, font, y_start, fill, line_spacing=1.2):
    dummy_img = Image.new("RGB", (1, 1))
    dummy_draw = ImageDraw.Draw(dummy_img)
    for i, line in enumerate(lines):
        bbox = dummy_draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        x = (SIZE[0] - w) // 2
        bbox_h = bbox[3] - bbox[1]
        y = y_start + i * int(bbox_h * line_spacing)
        draw.text((x, y), line, font=font, fill=fill)
    return y_start + len(lines) * int(line_spacing * 60)


def _get_line_height(font, text="Ag"):
    dummy_img = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[3] - bbox[1]


# ─── Style 1: Airy & Minimal ─────────────────────────────────────────────────
# Clean photo, white text directly on image. Small context + big main quote.
# Like img 1, 10, 11, 12, 13 from references.
def style_airy(quote: str, photo_bytes: bytes = None, handle: str = None) -> str:
    if photo_bytes:
        img = _load_photo(photo_bytes).convert("RGBA")
    else:
        # Fallback: soft gradient
        img = Image.new("RGBA", SIZE, (180, 200, 220, 255))

    # Split quote into context (small) + main (bold) if has newline or is long
    parts = quote.strip().split("\n", 1)
    if len(parts) == 2:
        context_text, main_text = parts[0].strip(), parts[1].strip()
    elif len(quote) > 60:
        # Auto-split: first ~30% words as context, rest as main
        words = quote.split()
        split_at = max(1, len(words) // 4)
        context_text = " ".join(words[:split_at])
        main_text = " ".join(words[split_at:])
    else:
        context_text = None
        main_text = quote

    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    main_font_size = 72 if len(main_text) < 40 else 56 if len(main_text) < 80 else 44
    main_font = ImageFont.truetype(FONT_POPPINS_BOLD, main_font_size)
    ctx_font  = ImageFont.truetype(FONT_POPPINS_LIGHT, 32)

    main_lines = _wrap_text(main_text, main_font, 880)
    lh = _get_line_height(main_font)
    total_h = len(main_lines) * int(lh * 1.25)
    if context_text:
        total_h += 50

    y = (SIZE[1] - total_h) // 2

    # Draw context line
    if context_text:
        ctx_lines = _wrap_text(context_text, ctx_font, 800)
        for line in ctx_lines:
            bbox = draw.textbbox((0, 0), line, font=ctx_font)
            x = (SIZE[0] - (bbox[2] - bbox[0])) // 2
            draw.text((x, y), line, font=ctx_font, fill=(255, 255, 255, 210))
        y += 50

    # Draw main quote with subtle shadow
    for i, line in enumerate(main_lines):
        bbox = draw.textbbox((0, 0), line, font=main_font)
        x = (SIZE[0] - (bbox[2] - bbox[0])) // 2
        draw_y = y + i * int(lh * 1.25)
        # Shadow
        draw.text((x + 2, draw_y + 2), line, font=main_font, fill=(0, 0, 0, 80))
        draw.text((x, draw_y), line, font=main_font, fill=(255, 255, 255, 245))

    result = Image.alpha_composite(img, overlay)
    return _save(result)


# ─── Style 2: Pure Minimal ───────────────────────────────────────────────────
# Light gray textured background, small centered serif text, lots of space.
# Like img 3 from references.
def style_minimal(quote: str, photo_bytes: bytes = None, handle: str = None) -> str:
    # Create subtle paper texture
    import random as rnd
    base_color = rnd.choice([
        (235, 236, 238),  # cool gray
        (240, 238, 232),  # warm white
        (228, 232, 236),  # blue-gray
    ])
    img = Image.new("RGB", SIZE, base_color)

    # Add subtle noise texture
    pixels = img.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            noise = rnd.randint(-8, 8)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
            )

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_LORA, 42)

    lines = _wrap_text(quote, font, 700)
    lh = _get_line_height(font)
    total_h = len(lines) * int(lh * 1.6)
    y = (SIZE[1] - total_h) // 2 + 20

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (SIZE[0] - (bbox[2] - bbox[0])) // 2
        draw_y = y + i * int(lh * 1.6)
        draw.text((x, draw_y), line, font=font, fill=(40, 40, 40, 255))

    return _save(img)


# ─── Style 3: Book Page / Highlight ──────────────────────────────────────────
# Warm paper texture, text with yellow highlighter strip behind key words.
# Like img 14 from references.
def style_book(quote: str, photo_bytes: bytes = None, handle: str = None) -> str:
    import random as rnd
    # Warm paper background
    bg = (245, 240, 228)
    img = Image.new("RGB", SIZE, bg)
    pixels = img.load()
    for y in range(SIZE[1]):
        for x in range(SIZE[0]):
            noise = rnd.randint(-5, 5)
            r, g, b = pixels[x, y]
            pixels[x, y] = (
                max(0, min(255, r + noise)),
                max(0, min(255, g + noise)),
                max(0, min(255, b + noise)),
            )

    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype(FONT_CALADEA, 54)

    lines = _wrap_text(quote, font, 720)
    lh = _get_line_height(font)
    line_h = int(lh * 1.55)
    total_h = len(lines) * line_h
    y_start = (SIZE[1] - total_h) // 2

    highlight_colors = [(255, 242, 0, 180), (180, 255, 120, 160), (255, 210, 100, 160)]
    highlight = rnd.choice(highlight_colors)

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        tw = bbox[2] - bbox[0]
        x = (SIZE[0] - tw) // 2
        draw_y = y_start + i * line_h

        # Highlight strip
        pad_x, pad_y = 12, 6
        hl_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
        hl_draw = ImageDraw.Draw(hl_layer)
        hl_draw.rectangle(
            [x - pad_x, draw_y - pad_y, x + tw + pad_x, draw_y + lh + pad_y],
            fill=highlight
        )
        img_rgba = img.convert("RGBA")
        img_rgba = Image.alpha_composite(img_rgba, hl_layer)
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)

        draw.text((x, draw_y), line, font=font, fill=(30, 25, 20))

    return _save(img)


# ─── Style 4: Dark Brand Card ─────────────────────────────────────────────────
# Dark navy/black background, bold white sans, accent color on key words.
# Big decorative quote mark. Optional handle. Like img 4,5,7,8,9.
def style_dark(quote: str, photo_bytes: bytes = None, handle: str = None) -> str:
    import random as rnd

    palettes = [
        {"bg": (10, 14, 26),  "accent": (100, 220, 100),  "text": (255, 255, 255)},
        {"bg": (12, 12, 18),  "accent": (200, 180, 255),  "text": (255, 255, 255)},
        {"bg": (18, 18, 14),  "accent": (255, 210, 80),   "text": (255, 255, 255)},
        {"bg": (10, 20, 18),  "accent": (80, 220, 200),   "text": (255, 255, 255)},
    ]
    palette = rnd.choice(palettes)
    bg, accent, text_col = palette["bg"], palette["accent"], palette["text"]

    img = Image.new("RGB", SIZE, bg)
    draw = ImageDraw.Draw(img)

    # Subtle circle decoration in corner
    draw.ellipse([700, -100, 1180, 380], outline=(*accent, 40), width=2)
    draw.ellipse([720, -80, 1160, 360], outline=(*accent, 20), width=1)

    # Big quote mark
    qfont = ImageFont.truetype(FONT_POPPINS_BOLD, 140)
    draw.text((80, 80), "\u201c", font=qfont, fill=(*accent, 255))

    # Main quote text
    words = quote.split()
    # Accent last 2-3 words
    accent_start = max(0, len(words) - 3)
    main_words = words[:accent_start]
    accent_words = words[accent_start:]

    main_text = " ".join(main_words)
    accent_text = " ".join(accent_words)

    font_main = ImageFont.truetype(FONT_POPPINS_BOLD, 64)
    font_accent = ImageFont.truetype(FONT_POPPINS_BOLD, 64)

    all_lines = _wrap_text(quote, font_main, 860)
    lh = _get_line_height(font_main)
    total_h = len(all_lines) * int(lh * 1.35)
    y = (SIZE[1] - total_h) // 2 + 60

    # Draw all lines — last line(s) in accent color
    for i, line in enumerate(all_lines):
        bbox = draw.textbbox((0, 0), line, font=font_main)
        x = 100
        draw_y = y + i * int(lh * 1.35)
        color = accent if i >= len(all_lines) - 1 else text_col
        draw.text((x, draw_y), line, font=font_main, fill=color)

    # Closing quote mark small
    draw.text((SIZE[0] - 160, y + total_h - 20), "\u201d", font=ImageFont.truetype(FONT_POPPINS_BOLD, 80), fill=(*accent, 200))

    # Handle / watermark
    if handle:
        h_font = ImageFont.truetype(FONT_POPPINS_REG, 28)
        draw.text((80, SIZE[1] - 80), handle, font=h_font, fill=(*accent, 200))

    # Subtle bottom line
    draw.line([(80, SIZE[1] - 100), (SIZE[0] - 80, SIZE[1] - 100)], fill=(*accent, 60), width=1)

    return _save(img)


# ─── Style 5: Warm Editorial ─────────────────────────────────────────────────
# Photo background, large bold headline + smaller subtitle. Like img 2.
def style_warm(quote: str, photo_bytes: bytes = None, handle: str = None) -> str:
    if photo_bytes:
        img = _load_photo(photo_bytes).convert("RGBA")
        # Darken slightly for readability
        enhancer = ImageEnhance.Brightness(img.convert("RGB"))
        img = enhancer.enhance(0.65).convert("RGBA")
    else:
        # Deep warm gradient
        img = Image.new("RGBA", SIZE, (40, 30, 20, 255))

    overlay = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Bottom gradient overlay for text area
    for y_i in range(400):
        alpha = int((y_i / 400) * 180)
        draw.line([(0, SIZE[1] - 400 + y_i), (SIZE[0], SIZE[1] - 400 + y_i)],
                  fill=(0, 0, 0, alpha))

    result = Image.alpha_composite(img, overlay)
    draw2 = ImageDraw.Draw(result)

    # Split quote
    parts = quote.strip().split("\n", 1)
    if len(parts) == 2:
        sub_text, main_text = parts[0].strip(), parts[1].strip()
    else:
        words = quote.split()
        split = max(1, len(words) // 3)
        sub_text = " ".join(words[:split])
        main_text = " ".join(words[split:])

    font_main = ImageFont.truetype(FONT_POPPINS_BOLD, 80 if len(main_text) < 30 else 62)
    font_sub  = ImageFont.truetype(FONT_POPPINS_LIGHT, 36)

    main_lines = _wrap_text(main_text, font_main, 900)
    sub_lines  = _wrap_text(sub_text, font_sub, 880)

    lh_main = _get_line_height(font_main)
    lh_sub  = _get_line_height(font_sub)

    total_h = len(sub_lines) * int(lh_sub * 1.4) + 20 + len(main_lines) * int(lh_main * 1.2)
    y = SIZE[1] - total_h - 100

    # Sub text
    for i, line in enumerate(sub_lines):
        bbox = draw2.textbbox((0, 0), line, font=font_sub)
        x = (SIZE[0] - (bbox[2] - bbox[0])) // 2
        draw2.text((x, y + i * int(lh_sub * 1.4)), line, font=font_sub, fill=(255, 255, 255, 200))

    y += len(sub_lines) * int(lh_sub * 1.4) + 20

    # Main text
    for i, line in enumerate(main_lines):
        bbox = draw2.textbbox((0, 0), line, font=font_main)
        x = (SIZE[0] - (bbox[2] - bbox[0])) // 2
        draw2.text((x, y + i * int(lh_main * 1.2)), line, font=font_main, fill=(255, 255, 255, 255))

    if handle:
        hf = ImageFont.truetype(FONT_POPPINS_REG, 28)
        bbox = draw2.textbbox((0, 0), handle, font=hf)
        x = (SIZE[0] - (bbox[2] - bbox[0])) // 2
        draw2.text((x, SIZE[1] - 55), handle, font=hf, fill=(255, 255, 255, 160))

    return _save(result)


# ─── Dispatch ─────────────────────────────────────────────────────────────────
RENDERERS = {
    "airy":    style_airy,
    "minimal": style_minimal,
    "book":    style_book,
    "dark":    style_dark,
    "warm":    style_warm,
}


def render_quote(quote: str, style: str, photo_bytes: bytes = None, handle: str = None) -> str:
    renderer = RENDERERS.get(style, style_airy)
    return renderer(quote=quote, photo_bytes=photo_bytes, handle=handle)
