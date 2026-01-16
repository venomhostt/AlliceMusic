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
