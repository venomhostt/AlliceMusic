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
        result = (await results.next())["result"][0]

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

        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 160))
        canvas = Image.alpha_composite(bg.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(canvas)

        # ========== ALBUM ART ==========
        album_size = 260
        album = base_img.resize((album_size, album_size), Image.LANCZOS)

        mask = Image.new("L", (album_size, album_size), 0)
        ImageDraw.Draw(mask).ellipse((0, 0, album_size, album_size), fill=255)
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
        while draw.textlength(show_title, font_title) > max_width:
            show_title = show_title[:-1]
        if show_title != title:
            show_title += "..."

        draw.text((tx, ty), show_title, font=font_title, fill=(255, 255, 255))
        draw.text((tx, ty + 55), f"{channel} | {views}", font=font_meta, fill=(220, 220, 220))

        # ========== PROGRESS ==========
        bar_y = ty + 120
        bar_w = 420
        progress = int(bar_w * 0.6)

        draw.rounded_rectangle((tx, bar_y, tx + bar_w, bar_y + 7), 4, fill=(160, 160, 160))
        draw.rounded_rectangle((tx, bar_y, tx + progress, bar_y + 7), 4, fill=(30, 215, 96))

        draw.text((tx, bar_y + 14), "00:00", font=font_time, fill=(200, 200, 200))
        draw.text((tx + bar_w - draw.textlength(duration, font_time), bar_y + 14),
                  duration, font=font_time, fill=(200, 200, 200))

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
        font_title = ImageFont.truetype(FONT_BOLD_PATH, 42)
        font_meta = ImageFont.truetype(FONT_BOLD_PATH, 26)
        font_time = ImageFont.truetype(FONT_BOLD_PATH, 22)

        max_width = CANVAS_W - text_x - 80
        show_title = title
        while draw.textlength(show_title, font_title) > max_width and len(show_title) > 5:
            show_title = show_title[:-1]
        if show_title != title:
            show_title += "..."

        draw.text((text_x, text_y), show_title, font=font_title, fill=(255, 255, 255))
        draw.text(
            (text_x, text_y + 55),
            f"{channel}  |  {views}",
            font=font_meta,
            fill=(220, 220, 220)
        )

        # ================= PROGRESS BAR =================
        bar_y = text_y + 120
        bar_w = 420
        bar_h = 7
        progress = int(bar_w * 0.6)

        draw.rounded_rectangle(
            (text_x, bar_y, text_x + bar_w, bar_y + bar_h),
            radius=4, fill=(160, 160, 160, 180)
        )
        draw.rounded_rectangle(
            (text_x, bar_y, text_x + progress, bar_y + bar_h),
            radius=4, fill=(30, 215, 96)
        )

        draw.ellipse(
            (text_x + progress - 6, bar_y - 4,
             text_x + progress + 6, bar_y + bar_h + 4),
            fill=(30, 215, 96)
        )

        draw.text((text_x, bar_y + 14), "00:00", font=font_time, fill=(200, 200, 200))
        draw.text(
            (text_x + bar_w - draw.textlength(duration, font_time),
             bar_y + 14),
            duration, font=font_time, fill=(200, 200, 200)
        )

        # ================= SAVE =================
        output = CACHE_DIR / f"{videoid}_final.jpg"
        canvas.convert("RGB").save(output, quality=95)

        try:
            if thumb_path and thumb_path.exists():
                os.remove(thumb_path)
        except:
            pass

        return str(output)

    except Exception as e:
        print("[Thumbnail Error]", e)
        traceback.print_exc()
        return None


if __name__ == "__main__":
    import asyncio
    asyncio.run(gen_thumb("dQw4w9WgXcQ"))0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        
        # Create curved shape for design
        curve_points = [
            (0, CANVAS_H),
            (CANVAS_W, CANVAS_H),
            (CANVAS_W, CANVAS_H - 150),
            (CANVAS_W // 2 + 200, CANVAS_H - 250),
            (CANVAS_W // 2 - 200, CANVAS_H - 250),
            (0, CANVAS_H - 150)
        ]
        overlay_draw.polygon(curve_points, fill=(0, 0, 0, 50))
        
        # Add second smaller curve
        curve_points2 = [
            (0, CANVAS_H),
            (CANVAS_W, CANVAS_H),
            (CANVAS_W, CANVAS_H - 100),
            (CANVAS_W // 2 + 150, CANVAS_H - 180),
            (CANVAS_W // 2 - 150, CANVAS_H - 180),
            (0, CANVAS_H - 100)
        ]
        overlay_draw.polygon(curve_points2, fill=(0, 0, 0, 30))
        
        canvas = Image.alpha_composite(canvas, overlay)
        
        # Prepare thumbnail (square with rounded corners)
        thumb_size = 400
        thumb_padding = 60
        thumb_x = thumb_padding
        thumb_y = (CANVAS_H - thumb_size) // 2
        
        # Resize and crop thumbnail to square
        thumb = base_img.resize((thumb_size, thumb_size), Image.LANCZOS)
        
        # Add rounded corners to thumbnail
        thumb = add_rounded_corners(thumb, 30)
        
        # Add modern shadow
        shadow = add_modern_shadow(thumb, offset=12, blur_radius=20)
        shadow_x = thumb_x - 12
        shadow_y = thumb_y - 12
        canvas.paste(shadow, (shadow_x, shadow_y), shadow)
        
        # Place thumbnail with decorative border
        border_size = thumb_size + 10
        border = Image.new('RGBA', (border_size, border_size), ACCENT_PURPLE)
        border = add_rounded_corners(border, 35)
        canvas.paste(border, (thumb_x - 5, thumb_y - 5), border)
        
        # Place thumbnail
        canvas.paste(thumb, (thumb_x, thumb_y), thumb)
        
        # Add play button overlay
        play_size = 80
        play_x = thumb_x + (thumb_size - play_size) // 2
        play_y = thumb_y + (thumb_size - play_size) // 2
        
        play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 150))
        play_draw = ImageDraw.Draw(play_bg)
        play_draw.ellipse([0, 0, play_size, play_size], fill=NEON_PINK)
        
        # Play triangle
        triangle_points = [
            (play_size * 0.35, play_size * 0.25),
            (play_size * 0.35, play_size * 0.75),
            (play_size * 0.75, play_size * 0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        
        play_bg = play_bg.filter(ImageFilter.GaussianBlur(2))
        canvas.paste(play_bg, (play_x, play_y), play_bg)
        
        # Content area (right side)
        content_x = thumb_x + thumb_size + 80
        content_width = CANVAS_W - content_x - 60
        
        # Branding/Logo
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 36)
        brand_text = "🎵 Shrutix Music"
        brand_y = thumb_y - 10
        
        # Add glow effect to branding
        add_glow_effect(draw, brand_text, (content_x, brand_y), brand_font, NEON_BLUE)
        draw.text((content_x, brand_y), brand_text, fill=TEXT_WHITE, font=brand_font)
        
        # "NOW PLAYING" badge
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 28)
        np_text = "▶️ NOW PLAYING"
        np_width = draw.textlength(np_text, font=np_font)
        np_x = content_x
        np_y = brand_y + 60
        
        # Badge background
        badge_padding = 20
        badge_height = 45
        badge_bg = Image.new('RGBA', (int(np_width) + badge_padding * 2, badge_height), (0, 0, 0, 0))
        badge_draw = ImageDraw.Draw(badge_bg)
        badge_draw.rounded_rectangle(
            [0, 0, np_width + badge_padding * 2, badge_height],
            radius=badge_height // 2,
            fill=NEON_PINK
        )
        
        # Add badge to canvas
        badge_pos = (np_x - badge_padding, np_y)
        canvas.paste(badge_bg, badge_pos, badge_bg)
        draw.text((np_x, np_y + badge_height // 2 - 12), np_text, fill=TEXT_WHITE, font=np_font)
        
        # Title section
        title_y = np_y + badge_height + 40
        title_font, title_wrapped = fit_title_font(
            draw, title, content_width - 40, FONT_BOLD_PATH,
            max_lines=2, start_size=38, min_size=32
        )
        
        # Title with shadow
        draw.multiline_text((content_x + 3, title_y + 3), 
                          title_wrapped, fill=TEXT_SHADOW,
                          font=title_font, spacing=8, align='left')
        draw.multiline_text((content_x, title_y), 
                          title_wrapped, fill=TEXT_WHITE,
                          font=title_font, spacing=8, align='left')
        
        # Metadata section with icons
        meta_start_y = title_y + 120
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 30)
        
        # Channel info
        channel_icon = "📺"
        channel_text = f"  {channel}"
        draw.text((content_x, meta_start_y), channel_icon, fill=ACCENT_GREEN, font=icon_font)
        draw.text((content_x + 40, meta_start_y), channel_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Views info
        views_icon = "👁️"
        views_text = f"  {views}"
        draw.text((content_x, meta_start_y + 50), views_icon, fill=NEON_BLUE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 50), views_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Duration info
        duration_icon = "⏱️"
        duration_text = f"  {duration}"
        draw.text((content_x, meta_start_y + 100), duration_icon, fill=ACCENT_PURPLE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 100), duration_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Add decorative elements
        
        # Top right decorative circle
        circle_size = 120
        circle_x = CANVAS_W - circle_size - 40
        circle_y = 40
        circle_img = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle_img)
        circle_draw.ellipse([0, 0, circle_size, circle_size], 
                          outline=ACCENT_PINK, width=4)
        
        # Add smaller inner circle
        inner_circle_size = circle_size - 30
        circle_draw.ellipse(
            [(circle_size - inner_circle_size) // 2, 
             (circle_size - inner_circle_size) // 2,
             (circle_size + inner_circle_size) // 2,
             (circle_size + inner_circle_size) // 2],
            outline=NEON_BLUE, width=2
        )
        
        canvas.paste(circle_img, (circle_x, circle_y), circle_img)
        
        # Bottom right music note
        music_font = ImageFont.truetype(FONT_BOLD_PATH, 48)
        music_note = "♪"
        music_x = CANVAS_W - 80
        music_y = CANVAS_H - 120
        add_glow_effect(draw, music_note, (music_x, music_y), music_font, NEON_PINK, iterations=5)
        draw.text((music_x, music_y), music_note, fill=ACCENT_PURPLE, font=music_font)
        
        # Add subtle particles/glitter
        for _ in range(50):
            x = random.randint(0, CANVAS_W)
            y = random.randint(0, CANVAS_H // 2)
            size = random.randint(1, 3)
            color = random.choice([NEON_BLUE, ACCENT_PINK, ACCENT_PURPLE, ACCENT_GREEN])
            draw.ellipse([x, y, x + size, y + size], fill=color)
        
        # Save final thumbnail
        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95, optimize=True)
        
        # Clean up downloaded thumbnail
        try:
            if thumb_path and os.path.exists(thumb_path):
                os.remove(thumb_path)
        except Exception as cleanup_error:
            print(f"[Cleanup Error] {cleanup_error}")
        
        return str(out)
        
    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback to default thumbnail
        try:
            if os.path.exists(FALLBACK_THUMB):
                print(f"[Fallback] Returning default thumbnail: {FALLBACK_THUMB}")
                return FALLBACK_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {FALLBACK_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        
    finally:
        # Clean up any partial downloads
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception as cleanup_error:
                print(f"[Final Cleanup Error] {cleanup_error}")
