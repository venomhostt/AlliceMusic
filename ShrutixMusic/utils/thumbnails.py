import os
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch

# ================= CONFIG =================
CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_W, CANVAS_H = 1280, 720

FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
DEFAULT_THUMB = "ShrutixMusic/assets/ShrutiBots.jpg"


async def gen_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"

    # ========== FETCH VIDEO DATA ==========
    try:
        results = VideosSearch(url, limit=1)
        data = await results.next()
        result = data["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "3:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "1M views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        thumb_path = CACHE_DIR / f"{videoid}.jpg"

        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGB")

    except Exception:
        base_img = Image.open(DEFAULT_THUMB).convert("RGB")
        title = "Music Title"
        duration = "3:00"
        views = "1M views"
        channel = "Unknown Channel"
    
    # ========== CREATE THUMBNAIL ==========
    # Resize base image
    base_img = base_img.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    
    # Create canvas
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (0, 0, 0))
    
    # Apply dark overlay
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 150))
    base_img.paste(overlay, (0, 0), overlay)
    
    # Add blurred background
    blurred = base_img.filter(ImageFilter.GaussianBlur(10))
    canvas.paste(blurred, (0, 0))
    
    # Add main image in center
    img_w, img_h = 600, 400
    img_x, img_y = (CANVAS_W - img_w) // 2, (CANVAS_H - img_h) // 2
    
    main_img = base_img.resize((img_w, img_h), Image.Resampling.LANCZOS)
    
    # Create rounded corners
    mask = Image.new("L", (img_w, img_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, img_w, img_h], radius=20, fill=255)
    
    canvas.paste(main_img, (img_x, img_y), mask)
    
    # Add shadow effect
    shadow = Image.new("RGBA", (img_w + 20, img_h + 20), (0, 0, 0, 100))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([0, 0, img_w + 20, img_h + 20], radius=25, fill=(0, 0, 0, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    canvas.paste(shadow, (img_x - 10, img_y - 10), shadow)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 48)
        info_font = ImageFont.truetype(FONT_BOLD_PATH, 32)
    except:
        title_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(canvas)
    
    # Draw title (centered at top)
    title_lines = []
    words = title.split()
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        text_width = bbox[2] - bbox[0]
        
        if text_width < CANVAS_W - 100:
            current_line.append(word)
        else:
            title_lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        title_lines.append(" ".join(current_line))
    
    title_y = 50
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_x = (CANVAS_W - text_width) // 2
        draw.text((text_x, title_y), line, font=title_font, fill="white", stroke_width=2, stroke_fill="black")
        title_y += 60
    
    # Draw info at bottom
    info_text = f"⏱️ {duration} | 👁️ {views} | 📺 {channel}"
    bbox = draw.textbbox((0, 0), info_text, font=info_font)
    text_width = bbox[2] - bbox[0]
    text_x = (CANVAS_W - text_width) // 2
    draw.text((text_x, CANVAS_H - 100), info_text, font=info_font, fill="yellow", stroke_width=1, stroke_fill="black")
    
    # Save thumbnail
    thumb_path = CACHE_DIR / f"{videoid}_thumb.jpg"
    canvas.save(thumb_path, "JPEG", quality=95)
    
    return str(thumb_path)


async def get_thumb(videoid: str):
    """Get thumbnail path for given video ID."""
    thumb_path = CACHE_DIR / f"{videoid}_thumb.jpg"
    
    # If thumbnail doesn't exist, generate it
    if not thumb_path.exists():
        try:
            thumb_path = await gen_thumb(videoid)
        except Exception as e:
            # Return default thumbnail if generation fails
            print(f"Failed to generate thumbnail: {e}")
            return DEFAULT_THUMB
    
    return str(thumb_path)


# Remove the problematic line that was causing the syntax error
# asyncio.run(gen_thumb("dQw4w9WgXcQ"))0, 0, 0, 0))  # <-- This line is the problem            async with session.get(thumburl) as resp:
                async with aiofiles.open(thumb_path, "wb") as f:
                    await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGB")

    except Exception:
        base_img = Image.open(DEFAULT_THUMB).convert("RGB")
        title = "Music Title"
        duration = "3:00"
        views = "1M views"
        channel = "Unknown Channel"
    
    # ========== CREATE THUMBNAIL ==========
    # Resize base image
    base_img = base_img.resize((CANVAS_W, CANVAS_H), Image.Resampling.LANCZOS)
    
    # Create canvas
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), (0, 0, 0))
    
    # Apply dark overlay
    overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 150))
    base_img.paste(overlay, (0, 0), overlay)
    
    # Add blurred background
    blurred = base_img.filter(ImageFilter.GaussianBlur(10))
    canvas.paste(blurred, (0, 0))
    
    # Add main image in center
    img_w, img_h = 600, 400
    img_x, img_y = (CANVAS_W - img_w) // 2, (CANVAS_H - img_h) // 2
    
    main_img = base_img.resize((img_w, img_h), Image.Resampling.LANCZOS)
    
    # Create rounded corners
    mask = Image.new("L", (img_w, img_h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, img_w, img_h], radius=20, fill=255)
    
    canvas.paste(main_img, (img_x, img_y), mask)
    
    # Add shadow effect
    shadow = Image.new("RGBA", (img_w + 20, img_h + 20), (0, 0, 0, 100))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([0, 0, img_w + 20, img_h + 20], radius=25, fill=(0, 0, 0, 100))
    shadow = shadow.filter(ImageFilter.GaussianBlur(15))
    canvas.paste(shadow, (img_x - 10, img_y - 10), shadow)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype(FONT_BOLD_PATH, 48)
        info_font = ImageFont.truetype(FONT_BOLD_PATH, 32)
    except:
        title_font = ImageFont.load_default()
        info_font = ImageFont.load_default()
    
    draw = ImageDraw.Draw(canvas)
    
    # Draw title (centered at top)
    title_lines = []
    words = title.split()
    current_line = []
    
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=title_font)
        text_width = bbox[2] - bbox[0]
        
        if text_width < CANVAS_W - 100:
            current_line.append(word)
        else:
            title_lines.append(" ".join(current_line))
            current_line = [word]
    
    if current_line:
        title_lines.append(" ".join(current_line))
    
    title_y = 50
    for line in title_lines:
        bbox = draw.textbbox((0, 0), line, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_x = (CANVAS_W - text_width) // 2
        draw.text((text_x, title_y), line, font=title_font, fill="white", stroke_width=2, stroke_fill="black")
        title_y += 60
    
    # Draw info at bottom
    info_text = f"⏱️ {duration} | 👁️ {views} | 📺 {channel}"
    bbox = draw.textbbox((0, 0), info_text, font=info_font)
    text_width = bbox[2] - bbox[0]
    text_x = (CANVAS_W - text_width) // 2
    draw.text((text_x, CANVAS_H - 100), info_text, font=info_font, fill="yellow", stroke_width=1, stroke_fill="black")
    
    # Save thumbnail
    thumb_path = CACHE_DIR / f"{videoid}_thumb.jpg"
    canvas.save(thumb_path, "JPEG", quality=95)
    
    return str(thumb_path)


async def get_thumb(videoid: str):
    """Get thumbnail path for given video ID."""
    thumb_path = CACHE_DIR / f"{videoid}_thumb.jpg"
    
    # If thumbnail doesn't exist, generate it
    if not thumb_path.exists():
        try:
            thumb_path = await gen_thumb(videoid)
        except Exception as e:
            # Return default thumbnail if generation fails
            print(f"Failed to generate thumbnail: {e}")
            return DEFAULT_THUMB
    
    return str(thumb_path)


# Remove the problematic line that was causing the syntax error
# asyncio.run(gen_thumb("dQw4w9WgXcQ"))0, 0, 0, 0))  # <-- This line is the problem        views = "1M views"
        channel = "Music Channel"
        thumb_path = None

    try:
        # ========== BACKGROUND ==========
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(30))
        bg = ImageEnhance.Color(bg).enhance(1.3)
        bg = ImageEnhance.Contrast(bg).enhance(1.25)
        bg = ImageEnhance.Brightness(bg).enhance(1.05)

        overlay = Image.new(
            "RGBA",
            (CANVAS_W, CANVAS_H),
            (0, 0, 0, 160)
        )

        canvas = Image.alpha_composite(bg.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(canvas)

        # ========== ALBUM ART ==========
        album_size = 260
        album = base_img.resize((album_size, album_size), Image.LANCZOS)

        mask = Image.new("L", (album_size, album_size), 0)
        ImageDraw.Draw(mask).ellipse(
            (0, 0, album_size, album_size),
            fill=255
        )

        album.putalpha(mask)

        ax = 90
        ay = CANVAS_H // 2 - album_size // 2

        canvas.paste(album, (ax, ay), album)

        # ========== TEXT ==========
        tx = ax + album_size + 60
        ty = ay + 20

        font_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        font_meta = ImageFont.truetype(FONT_BOLD_PATH, 26)
        font_time = ImageFont.truetype(FONT_BOLD_PATH, 22)

        max_width = CANVAS_W - tx - 80
        show_title = title

        while draw.textlength(show_title, font=font_title) > max_width:
            show_title = show_title[:-1]

        if show_title != title:
            show_title += "..."

        draw.text(
            (tx, ty),
            show_title,
            font=font_title,
            fill=(255, 255, 255)
        )

        draw.text(
            (tx, ty + 55),
            f"{channel} | {views}",
            font=font_meta,
            fill=(220, 220, 220)
        )

        # ========== PROGRESS BAR ==========
        bar_y = ty + 120
        bar_w = 420
        progress = int(bar_w * 0.6)

        draw.rounded_rectangle(
            (tx, bar_y, tx + bar_w, bar_y + 7),
            radius=4,
            fill=(160, 160, 160)
        )

        draw.rounded_rectangle(
            (tx, bar_y, tx + progress, bar_y + 7),
            radius=4,
            fill=(30, 215, 96)
        )

        draw.text(
            (tx, bar_y + 14),
            "00:00",
            font=font_time,
            fill=(200, 200, 200)
        )

        draw.text(
            (
                tx + bar_w - draw.textlength(duration, font=font_time),
                bar_y + 14
            ),
            duration,
            font=font_time,
            fill=(200, 200, 200)
        )

        # ========== SAVE ==========
        output = CACHE_DIR / f"{videoid}_final.jpg"
        canvas.convert("RGB").save(output, quality=95)

        if thumb_path and thumb_path.exists():
            os.remove(thumb_path)

        return str(output)

    except Exception as e:
        print("[Thumbnail Error]", e)
        traceback.print_exc()
        return None
