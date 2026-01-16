import os
import aiohttp
import aiofiles
import traceback
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

CANVAS_WIDTH, CANVAS_HEIGHT = 1280, 720

# Font paths - make sure these exist or handle errors
try:
    FONT_REGULAR = ImageFont.truetype("assets/font2.ttf", 32)
except:
    FONT_REGULAR = ImageFont.load_default()
    
try:
    FONT_BOLD = ImageFont.truetype("assets/font3.ttf", 36)
except:
    FONT_BOLD = ImageFont.load_default()

DEFAULT_THUMB = "assets/temp_thumb.jpg"

async def download_thumbnail(videoid: str, url: str) -> str:
    """Download thumbnail from YouTube"""
    thumb_path = CACHE_DIR / f"thumb_{videoid}.jpg"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await response.read())
                    return str(thumb_path)
    except Exception as e:
        print(f"Error downloading thumbnail: {e}")
    
    return None

async def get_thumb(videoid: str):
    """Generate thumbnail for YouTube video"""
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video information
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]
        
        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "3:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "N/A")
        channel = result.get("channel", {}).get("name", "Unknown")
        
        # Download thumbnail
        thumb_path = await download_thumbnail(videoid, thumburl)
        
        if thumb_path and os.path.exists(thumb_path):
            base_image = Image.open(thumb_path).convert("RGB")
        else:
            # Use default if download failed
            base_image = Image.open(DEFAULT_THUMB).convert("RGB")
            title = "Music Title"
            duration = "3:00"
            views = "1M views"
            channel = "Music Channel"
        
    except Exception as e:
        print(f"Error fetching video data: {e}")
        # Try to use default thumbnail
        try:
            base_image = Image.open(DEFAULT_THUMB).convert("RGB")
            title = "Music Title"
            duration = "3:00"
            views = "1M views"
            channel = "Music Channel"
        except Exception:
            print("Default thumbnail not found, creating basic image")
            base_image = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), (30, 30, 40))
            title = "Music Title"
            duration = "3:00"
            views = "1M views"
            channel = "Music Channel"
    
    try:
        # Create background with blur effect
        background = base_image.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.LANCZOS)
        background = background.filter(ImageFilter.GaussianBlur(15))
        
        # Enhance background colors
        background = ImageEnhance.Brightness(background).enhance(0.8)
        background = ImageEnhance.Contrast(background).enhance(1.1)
        
        # Create canvas with overlay
        overlay = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (0, 0, 0, 120))
        canvas = Image.alpha_composite(background.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(canvas)
        
        # Create circular album art
        album_size = 280
        album_img = base_image.resize((album_size, album_size), Image.LANCZOS)
        
        # Create circular mask
        mask = Image.new("L", (album_size, album_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, album_size, album_size), fill=255)
        album_img.putalpha(mask)
        
        # Album position
        album_x = 80
        album_y = (CANVAS_HEIGHT - album_size) // 2
        
        # Add shadow to album
        shadow_size = album_size + 20
        shadow = Image.new("RGBA", (shadow_size, shadow_size), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse((10, 10, album_size + 10, album_size + 10), fill=(0, 0, 0, 100))
        shadow = shadow.filter(ImageFilter.GaussianBlur(10))
        
        canvas.paste(shadow, (album_x - 10, album_y - 10), shadow)
        canvas.paste(album_img, (album_x, album_y), album_img)
        
        # Content area
        content_x = album_x + album_size + 60
        content_y = album_y
        
        # Title
        max_title_width = CANVAS_WIDTH - content_x - 40
        display_title = title
        
        # Truncate title if too long
        while draw.textlength(display_title, font=FONT_BOLD) > max_title_width and len(display_title) > 10:
            display_title = display_title[:-1]
        
        if display_title != title:
            display_title = display_title[:-3] + "..."
        
        draw.text((content_x, content_y), display_title, font=FONT_BOLD, fill=(255, 255, 255))
        
        # Channel and views
        metadata_y = content_y + 50
        metadata_text = f"{channel} • {views}"
        draw.text((content_x, metadata_y), metadata_text, font=FONT_REGULAR, fill=(200, 200, 200))
        
        # Duration
        duration_y = metadata_y + 40
        draw.text((content_x, duration_y), f"Duration: {duration}", font=FONT_REGULAR, fill=(180, 180, 180))
        
        # Progress bar
        bar_y = duration_y + 60
        bar_width = 450
        bar_height = 6
        
        # Background bar
        draw.rounded_rectangle(
            (content_x, bar_y, content_x + bar_width, bar_y + bar_height),
            radius=3,
            fill=(100, 100, 100, 180)
        )
        
        # Progress (60%)
        progress_width = int(bar_width * 0.6)
        draw.rounded_rectangle(
            (content_x, bar_y, content_x + progress_width, bar_y + bar_height),
            radius=3,
            fill=(30, 215, 96)
        )
        
        # Time labels
        time_font = ImageFont.truetype("assets/font2.ttf", 20) if os.path.exists("assets/font2.ttf") else ImageFont.load_default()
        draw.text((content_x, bar_y + 15), "0:00", font=time_font, fill=(150, 150, 150))
        draw.text((content_x + bar_width - 40, bar_y + 15), duration, font=time_font, fill=(150, 150, 150))
        
        # Now Playing badge
        badge_y = bar_y + 60
        draw.rounded_rectangle(
            (content_x, badge_y, content_x + 150, badge_y + 35),
            radius=17,
            fill=(255, 20, 147, 200)
        )
        draw.text((content_x + 15, badge_y + 8), "▶ NOW PLAYING", font=time_font, fill=(255, 255, 255))
        
        # Save final image
        output_path = CACHE_DIR / f"thumb_final_{videoid}.jpg"
        canvas.convert("RGB").save(output_path, "JPEG", quality=95)
        
        # Cleanup
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except:
                pass
        
        return str(output_path)
        
    except Exception as e:
        print(f"Error generating thumbnail: {e}")
        traceback.print_exc()
        
        # Return default if available
        if os.path.exists(DEFAULT_THUMB):
            return DEFAULT_THUMB
        
        return None        return str(output)
        
    except Exception as e:
        print(f"Error generating thumb: {e}")
        return "ShrutixMusic/assets/temp_thumb.jpg"    try:
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            if horizontal:
                alpha = int(255 * y / height)
            else:
                alpha = int(255 * y / height)
            mask_data.extend([alpha] * width)
        
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base.convert('RGBA')
    except Exception as e:
        print(f"[create_gradient Error] {e}")
        return Image.new('RGBA', (width, height), color1)

def add_rounded_corners(image, radius):
    """Add rounded corners to image"""
    try:
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)
        
        result = image.copy()
        result.putalpha(mask)
        return result
    except Exception as e:
        print(f"[add_rounded_corners Error] {e}")
        return image

def add_modern_shadow(image, offset=8, blur_radius=15, shadow_color=(0, 0, 0, 100)):
    """Add modern shadow effect"""
    try:
        shadow = Image.new('RGBA', 
                          (image.size[0] + offset*2, image.size[1] + offset*2), 
                          (0, 0, 0, 0))
        
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [offset, offset, 
             image.size[0] + offset, image.size[1] + offset],
            radius=25,
            fill=shadow_color
        )
        
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
        return shadow
    except Exception as e:
        print(f"[add_modern_shadow Error] {e}")
        return image

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text with ellipsis if too long"""
    try:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = draw.textlength(test_line, font=font)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word too long, truncate
                    lines.append(word[:20] + "...")
                    break
                    
                if len(lines) >= max_lines:
                    # Add ellipsis to last line
                    if len(lines) == max_lines:
                        last_line = lines[-1]
                        while draw.textlength(last_line + " ...", font=font) > max_width and len(last_line) > 3:
                            last_line = last_line[:-1]
                        lines[-1] = last_line + " ..."
                    break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    except Exception as e:
        print(f"[wrap_text Error] {e}")
        return text[:50]

def fit_title_font(draw, text, max_width, font_path, max_lines=2, start_size=42, min_size=32):
    """Find optimal font size for title"""
    try:
        size = start_size
        while size >= min_size:
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                size -= 2
                continue
            
            wrapped = wrap_text(draw, text, font, max_width, max_lines)
            lines = wrapped.split('\n')
            
            if len(lines) <= max_lines and all(draw.textlength(line, font=font) <= max_width for line in lines):
                return font, wrapped
            size -= 2
        
        font = ImageFont.truetype(font_path, min_size)
        return font, wrap_text(draw, text, font, max_width, max_lines)
    except Exception as e:
        print(f"[fit_title_font Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def add_glow_effect(draw, text, position, font, glow_color, iterations=3):
    """Add glow effect to text"""
    x, y = position
    for i in range(iterations, 0, -1):
        offset = i
        alpha = 100 // (i * 2)
        glow_color_with_alpha = (glow_color[0], glow_color[1], glow_color[2], alpha)
        draw.text((x + offset, y + offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x - offset, y + offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x + offset, y - offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x - offset, y - offset), text, fill=glow_color_with_alpha, font=font)

def create_music_visualizer(width, height, count=20):
    """Create decorative music visualizer bars"""
    try:
        visualizer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(visualizer)
        
        bar_width = width // (count * 2)
        spacing = bar_width
        
        colors = [ACCENT_PURPLE, ACCENT_PINK, NEON_BLUE, ACCENT_GREEN, NEON_PINK]
        
        for i in range(count):
            x = i * (bar_width + spacing) + spacing
            # Random height for dynamic look
            bar_height = random.randint(height // 4, height - 50)
            bar_y = height - bar_height
            
            color = colors[i % len(colors)]
            
            # Draw bar with gradient
            for h in range(bar_height):
                alpha = int(255 * (h / bar_height))
                draw.rectangle(
                    [x, bar_y + h, x + bar_width, bar_y + h + 1],
                    fill=(color[0], color[1], color[2], alpha)
                )
        
        return visualizer
    except Exception as e:
        print(f"[create_music_visualizer Error] {e}")
        return Image.new('RGBA', (width, height), (0, 0, 0, 0))

def create_progress_bar(draw, x, y, width, height, progress_percent=60, show_time=True, current_time="00:00", total_time="3:00"):
    """Create a modern progress bar with time indicators"""
    try:
        # Background bar
        draw.rounded_rectangle(
            (x, y, x + width, y + height),
            radius=height//2,
            fill=(100, 100, 100, 180)
        )
        
        # Progress bar
        progress_width = int(width * (progress_percent / 100))
        draw.rounded_rectangle(
            (x, y, x + progress_width, y + height),
            radius=height//2,
            fill=PROGRESS_GREEN
        )
        
        # Progress knob
        knob_size = height + 8
        draw.ellipse(
            (x + progress_width - knob_size//2, y - 4,
             x + progress_width + knob_size//2, y + height + 4),
            fill=PROGRESS_GREEN
        )
        
        if show_time:
            font = ImageFont.truetype(FONT_REGULAR_PATH, 18)
            # Current time (left)
            draw.text(
                (x, y + height + 10),
                current_time,
                font=font,
                fill=(200, 200, 200)
            )
            
            # Total time (right)
            text_width = draw.textlength(total_time, font=font)
            draw.text(
                (x + width - text_width, y + height + 10),
                total_time,
                font=font,
                fill=(200, 200, 200)
            )
            
        return progress_width
    except Exception as e:
        print(f"[create_progress_bar Error] {e}")
        return 0

async def get_thumb(videoid: str):
    """Generate thumbnail for YouTube video"""
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "3:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "1M views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

    except Exception as e:
        print(f"[Data Fetch Error] {e}, using default thumbnail")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "Music Title"
            duration = "3:00"
            views = "1M views"
            channel = "Music Channel"
        except:
            print(f"[Default Thumb Error] Cannot open {DEFAULT_THUMB}")
            return None

    try:
        # ================= ENHANCED BACKGROUND =================
        # Create blurred background from thumbnail
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        
        # Enhance background
        bg = ImageEnhance.Color(bg).enhance(1.2)
        bg = ImageEnhance.Contrast(bg).enhance(1.1)
        bg = ImageEnhance.Brightness(bg).enhance(1.05)
        
        # Add dark overlay
        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 120))
        canvas = Image.alpha_composite(bg.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(canvas)
        
        # ================= CIRCULAR ALBUM ART =================
        album_size = 280
        album = base_img.resize((album_size, album_size), Image.LANCZOS)
        
        # Create circular mask
        mask = Image.new("L", (album_size, album_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, album_size, album_size), fill=255)
        album.putalpha(mask)
        
        # Position album (left side)
        album_x = 80
        album_y = CANVAS_H // 2 - album_size // 2
        
        # Add shadow
        shadow = Image.new("RGBA", (album_size + 30, album_size + 30), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse(
            (15, 15, album_size + 15, album_size + 15),
            fill=(0, 0, 0, 140)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        canvas.paste(shadow, (album_x - 15, album_y - 15), shadow)
        
        # Add colored border
        border_size = album_size + 20
        border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse(
            (0, 0, border_size, border_size),
            outline=ACCENT_PURPLE,
            width=4
        )
        canvas.paste(border, (album_x - 10, album_y - 10), border)
        
        # Place album art
        canvas.paste(album, (album_x, album_y), album)
        
        # Add play button on album
        play_size = 60
        play_x = album_x + album_size // 2 - play_size // 2
        play_y = album_y + album_size // 2 - play_size // 2
        
        play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 0))
        play_draw = ImageDraw.Draw(play_bg)
        play_draw.ellipse([0, 0, play_size, play_size], fill=NEON_PINK)
        
        # Play triangle
        triangle_points = [
            (play_size * 0.35, play_size * 0.25),
            (play_size * 0.35, play_size * 0.75),
            (play_size * 0.75, play_size * 0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        canvas.paste(play_bg, (play_x, play_y), play_bg)
        
        # ================= CONTENT AREA =================
        content_x = album_x + album_size + 60
        content_y = album_y + 20
        content_width = CANVAS_W - content_x - 40
        
        # Branding/Logo
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        brand_text = "🎵 Shrutix Music"
        draw.text((content_x, content_y), brand_text, fill=TEXT_WHITE, font=brand_font)
        
        # "NOW PLAYING" badge
        np_y = content_y + 50
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 26)
        np_text = "▶️ NOW PLAYING"
        np_width = draw.textlength(np_text, font=np_font)
        
        # Create badge background
        badge_padding = 15
        badge_height = 40
        badge_bg = Image.new('RGBA', (int(np_width) + badge_padding * 2, badge_height), (0, 0, 0, 0))
        badge_draw = ImageDraw.Draw(badge_bg)
        badge_draw.rounded_rectangle(
            [0, 0, np_width + badge_padding * 2, badge_height],
            radius=badge_height // 2,
            fill=NEON_PINK
        )
        
        # Add badge to canvas
        badge_pos = (content_x - badge_padding, np_y)
        canvas.paste(badge_bg, badge_pos, badge_bg)
        draw.text((content_x, np_y + badge_height // 2 - 13), np_text, fill=TEXT_WHITE, font=np_font)
        
        # Title section
        title_y = np_y + badge_height + 30
        title_font, title_wrapped = fit_title_font(
            draw, title, content_width - 40, FONT_BOLD_PATH,
            max_lines=2, start_size=36, min_size=30
        )
        
        # Title with shadow
        title_lines = title_wrapped.split('\n')
        for i, line in enumerate(title_lines):
            draw.text((content_x + 2, title_y + i*45 + 2), 
                     line, fill=TEXT_SHADOW, font=title_font)
            draw.text((content_x, title_y + i*45), 
                     line, fill=TEXT_WHITE, font=title_font)
        
        # Metadata section with icons
        meta_start_y = title_y + len(title_lines) * 45 + 25
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 26)
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        
        # Channel info
        channel_icon = "📺"
        channel_text = f"  {channel}"
        draw.text((content_x, meta_start_y), channel_icon, fill=ACCENT_GREEN, font=icon_font)
        draw.text((content_x + 40, meta_start_y), channel_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Views info
        views_icon = "👁️"
        views_text = f"  {views}"
        draw.text((content_x, meta_start_y + 45), views_icon, fill=NEON_BLUE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 45), views_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Duration info
        duration_icon = "⏱️"
        duration_text = f"  {duration}"
        draw.text((content_x, meta_start_y + 90), duration_icon, fill=ACCENT_PURPLE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 90), duration_text, fill=TEXT_LIGHT, font=meta_font)
        
        # ================= PROGRESS BAR =================
        progress_y = meta_start_y + 150
        progress_width = 450
        progress_height = 8
        
        create_progress_bar(
            draw=draw,
            x=content_x,
            y=progress_y,
            width=progress_width,
            height=progress_height,
            progress_percent=60,
            show_time=True,
            current_time="00:00",
            total_time=duration
        )
        
        # ================= DECORATIVE ELEMENTS =================
        # Add music visualizer at bottom
        visualizer_height = 100
        visualizer = create_music_visualizer(CANVAS_W, visualizer_height)
        canvas.paste(visualizer, (0, CANVAS_H - visualizer_height), visualizer)
        
        # Add decorative circles
        circle_size = 100
        circle_x = CANVAS_W - circle_size - 40
        circle_y = 40
        
        circle_img = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle_img)
        circle_draw.ellipse([0, 0, circle_size, circle_size], 
                          outline=ACCENT_PINK, width=3)
        
        # Inner circle
        inner_size = circle_size - 25
        circle_draw.ellipse(
            [(circle_size - inner_size)//2, (circle_size - inner_size)//2,
             (circle_size + inner_size)//2, (circle_size + inner_size)//2],
            outline=NEON_BLUE, width=2
        )
        
        canvas.paste(circle_img, (circle_x, circle_y), circle_img)
        
        # Music note decoration
        music_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        music_note = "♪"
        music_x = CANVAS_W - 80
        music_y = CANVAS_H - 140
        draw.text((music_x, music_y), music_note, fill=ACCENT_PURPLE, font=music_font)
        
        # Add subtle particles/glitter
        for _ in range(40):
            x = random.randint(content_x + progress_width + 50, CANVAS_W - 50)
            y = random.randint(50, CANVAS_H - 200)
            size = random.randint(2, 4)
            color = random.choice([NEON_BLUE, ACCENT_PINK, ACCENT_PURPLE, ACCENT_GREEN])
            draw.ellipse([x, y, x + size, y + size], fill=color)
        
        # ================= SAVE =================
        out = CACHE_DIR / f"{videoid}_styled.png"
        canvas.save(out, quality=95, optimize=True)
        
        # Clean up downloaded thumbnail
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except Exception as cleanup_error:
                print(f"[Cleanup Error] {cleanup_error}")
        
        return str(out)
        
    except Exception as e:
        print(f"[get_thumb Error] {e}")
        traceback.print_exc()
        
        # Fallback to default thumbnail
        try:
            if os.path.exists(DEFAULT_THUMB):
                print(f"[Fallback] Returning default thumbnail: {DEFAULT_THUMB}")
                return DEFAULT_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {DEFAULT_THUMB}")
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
                print(f"[Final Cleanup Error] {cleanup_error}")        ratio = min(max_w / image.size[0], max_h / image.size[1])
        return image.resize((int(image.size[0]*ratio), int(image.size[1]*ratio)), Image.LANCZOS)
    except Exception as e:
        print(f"[change_image_size Error] {e}")
        return image

def create_gradient(width, height, color1, color2, horizontal=False):
    """Create a smooth gradient background"""
    try:
        base = Image.new('RGB', (width, height), color1)
        top = Image.new('RGB', (width, height), color2)
        
        mask = Image.new('L', (width, height))
        mask_data = []
        
        for y in range(height):
            if horizontal:
                alpha = int(255 * y / height)
            else:
                alpha = int(255 * y / height)
            mask_data.extend([alpha] * width)
        
        mask.putdata(mask_data)
        base.paste(top, (0, 0), mask)
        return base.convert('RGBA')
    except Exception as e:
        print(f"[create_gradient Error] {e}")
        return Image.new('RGBA', (width, height), color1)

def add_rounded_corners(image, radius):
    """Add rounded corners to image"""
    try:
        mask = Image.new('L', image.size, 0)
        draw = ImageDraw.Draw(mask)
        draw.rounded_rectangle([0, 0, image.size[0], image.size[1]], radius=radius, fill=255)
        
        result = image.copy()
        result.putalpha(mask)
        return result
    except Exception as e:
        print(f"[add_rounded_corners Error] {e}")
        return image

def add_modern_shadow(image, offset=8, blur_radius=15, shadow_color=(0, 0, 0, 100)):
    """Add modern shadow effect"""
    try:
        shadow = Image.new('RGBA', 
                          (image.size[0] + offset*2, image.size[1] + offset*2), 
                          (0, 0, 0, 0))
        
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.rounded_rectangle(
            [offset, offset, 
             image.size[0] + offset, image.size[1] + offset],
            radius=25,
            fill=shadow_color
        )
        
        shadow = shadow.filter(ImageFilter.GaussianBlur(blur_radius))
        return shadow
    except Exception as e:
        print(f"[add_modern_shadow Error] {e}")
        return image

def wrap_text(draw, text, font, max_width, max_lines=2):
    """Wrap text with ellipsis if too long"""
    try:
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = draw.textlength(test_line, font=font)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    # Single word too long, truncate
                    lines.append(word[:20] + "...")
                    break
                    
                if len(lines) >= max_lines:
                    # Add ellipsis to last line
                    if len(lines) == max_lines:
                        last_line = lines[-1]
                        while draw.textlength(last_line + " ...", font=font) > max_width and len(last_line) > 3:
                            last_line = last_line[:-1]
                        lines[-1] = last_line + " ..."
                    break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    except Exception as e:
        print(f"[wrap_text Error] {e}")
        return text[:50]

def fit_title_font(draw, text, max_width, font_path, max_lines=2, start_size=42, min_size=32):
    """Find optimal font size for title"""
    try:
        size = start_size
        while size >= min_size:
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                size -= 2
                continue
            
            wrapped = wrap_text(draw, text, font, max_width, max_lines)
            lines = wrapped.split('\n')
            
            if len(lines) <= max_lines and all(draw.textlength(line, font=font) <= max_width for line in lines):
                return font, wrapped
            size -= 2
        
        font = ImageFont.truetype(font_path, min_size)
        return font, wrap_text(draw, text, font, max_width, max_lines)
    except Exception as e:
        print(f"[fit_title_font Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def add_glow_effect(draw, text, position, font, glow_color, iterations=3):
    """Add glow effect to text"""
    x, y = position
    for i in range(iterations, 0, -1):
        offset = i
        alpha = 100 // (i * 2)
        glow_color_with_alpha = (glow_color[0], glow_color[1], glow_color[2], alpha)
        draw.text((x + offset, y + offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x - offset, y + offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x + offset, y - offset), text, fill=glow_color_with_alpha, font=font)
        draw.text((x - offset, y - offset), text, fill=glow_color_with_alpha, font=font)

def create_music_visualizer(width, height, count=20):
    """Create decorative music visualizer bars"""
    try:
        visualizer = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(visualizer)
        
        bar_width = width // (count * 2)
        spacing = bar_width
        
        colors = [ACCENT_PURPLE, ACCENT_PINK, NEON_BLUE, ACCENT_GREEN, NEON_PINK]
        
        for i in range(count):
            x = i * (bar_width + spacing) + spacing
            # Random height for dynamic look
            bar_height = random.randint(height // 4, height - 50)
            bar_y = height - bar_height
            
            color = colors[i % len(colors)]
            
            # Draw bar with gradient
            for h in range(bar_height):
                alpha = int(255 * (h / bar_height))
                draw.rectangle(
                    [x, bar_y + h, x + bar_width, bar_y + h + 1],
                    fill=(color[0], color[1], color[2], alpha)
                )
        
        return visualizer
    except Exception as e:
        print(f"[create_music_visualizer Error] {e}")
        return Image.new('RGBA', (width, height), (0, 0, 0, 0))

def create_progress_bar(draw, x, y, width, height, progress_percent=60, show_time=True, current_time="00:00", total_time="3:00"):
    """Create a modern progress bar with time indicators"""
    try:
        # Background bar
        draw.rounded_rectangle(
            (x, y, x + width, y + height),
            radius=height//2,
            fill=(100, 100, 100, 180)
        )
        
        # Progress bar
        progress_width = int(width * (progress_percent / 100))
        draw.rounded_rectangle(
            (x, y, x + progress_width, y + height),
            radius=height//2,
            fill=PROGRESS_GREEN
        )
        
        # Progress knob
        knob_size = height + 8
        draw.ellipse(
            (x + progress_width - knob_size//2, y - 4,
             x + progress_width + knob_size//2, y + height + 4),
            fill=PROGRESS_GREEN
        )
        
        if show_time:
            font = ImageFont.truetype(FONT_REGULAR_PATH, 18)
            # Current time (left)
            draw.text(
                (x, y + height + 10),
                current_time,
                font=font,
                fill=(200, 200, 200)
            )
            
            # Total time (right)
            text_width = draw.textlength(total_time, font=font)
            draw.text(
                (x + width - text_width, y + height + 10),
                total_time,
                font=font,
                fill=(200, 200, 200)
            )
            
        return progress_width
    except Exception as e:
        print(f"[create_progress_bar Error] {e}")
        return 0

async def get_thumb(videoid: str):
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "3:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "1M views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")

    except Exception as e:
        print(f"[Data Fetch Error] {e}, using default thumbnail")
        try:
            base_img = Image.open(DEFAULT_THUMB).convert("RGBA")
            title = "Music Title"
            duration = "3:00"
            views = "1M views"
            channel = "Music Channel"
        except:
            print(f"[Default Thumb Error] Cannot open {DEFAULT_THUMB}")
            return None

    try:
        # ================= ENHANCED BACKGROUND =================
        # Create blurred background from thumbnail
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(25))
        
        # Enhance background
        bg = ImageEnhance.Color(bg).enhance(1.2)
        bg = ImageEnhance.Contrast(bg).enhance(1.1)
        bg = ImageEnhance.Brightness(bg).enhance(1.05)
        
        # Add dark overlay
        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 120))
        canvas = Image.alpha_composite(bg.convert("RGBA"), overlay)
        draw = ImageDraw.Draw(canvas)
        
        # ================= CIRCULAR ALBUM ART =================
        album_size = 280
        album = base_img.resize((album_size, album_size), Image.LANCZOS)
        
        # Create circular mask
        mask = Image.new("L", (album_size, album_size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, album_size, album_size), fill=255)
        album.putalpha(mask)
        
        # Position album (left side)
        album_x = 80
        album_y = CANVAS_H // 2 - album_size // 2
        
        # Add shadow
        shadow = Image.new("RGBA", (album_size + 30, album_size + 30), (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow)
        shadow_draw.ellipse(
            (15, 15, album_size + 15, album_size + 15),
            fill=(0, 0, 0, 140)
        )
        shadow = shadow.filter(ImageFilter.GaussianBlur(20))
        canvas.paste(shadow, (album_x - 15, album_y - 15), shadow)
        
        # Add colored border
        border_size = album_size + 20
        border = Image.new("RGBA", (border_size, border_size), (0, 0, 0, 0))
        border_draw = ImageDraw.Draw(border)
        border_draw.ellipse(
            (0, 0, border_size, border_size),
            outline=ACCENT_PURPLE,
            width=4
        )
        canvas.paste(border, (album_x - 10, album_y - 10), border)
        
        # Place album art
        canvas.paste(album, (album_x, album_y), album)
        
        # Add play button on album
        play_size = 60
        play_x = album_x + album_size // 2 - play_size // 2
        play_y = album_y + album_size // 2 - play_size // 2
        
        play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 0))
        play_draw = ImageDraw.Draw(play_bg)
        play_draw.ellipse([0, 0, play_size, play_size], fill=NEON_PINK)
        
        # Play triangle
        triangle_points = [
            (play_size * 0.35, play_size * 0.25),
            (play_size * 0.35, play_size * 0.75),
            (play_size * 0.75, play_size * 0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        canvas.paste(play_bg, (play_x, play_y), play_bg)
        
        # ================= CONTENT AREA =================
        content_x = album_x + album_size + 60
        content_y = album_y + 20
        content_width = CANVAS_W - content_x - 40
        
        # Branding/Logo
        brand_font = ImageFont.truetype(FONT_BOLD_PATH, 34)
        brand_text = "🎵 Shrutix Music"
        draw.text((content_x, content_y), brand_text, fill=TEXT_WHITE, font=brand_font)
        
        # "NOW PLAYING" badge
        np_y = content_y + 50
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 26)
        np_text = "▶️ NOW PLAYING"
        np_width = draw.textlength(np_text, font=np_font)
        
        # Create badge background
        badge_padding = 15
        badge_height = 40
        badge_bg = Image.new('RGBA', (int(np_width) + badge_padding * 2, badge_height), (0, 0, 0, 0))
        badge_draw = ImageDraw.Draw(badge_bg)
        badge_draw.rounded_rectangle(
            [0, 0, np_width + badge_padding * 2, badge_height],
            radius=badge_height // 2,
            fill=NEON_PINK
        )
        
        # Add badge to canvas
        badge_pos = (content_x - badge_padding, np_y)
        canvas.paste(badge_bg, badge_pos, badge_bg)
        draw.text((content_x, np_y + badge_height // 2 - 13), np_text, fill=TEXT_WHITE, font=np_font)
        
        # Title section
        title_y = np_y + badge_height + 30
        title_font, title_wrapped = fit_title_font(
            draw, title, content_width - 40, FONT_BOLD_PATH,
            max_lines=2, start_size=36, min_size=30
        )
        
        # Title with shadow
        title_lines = title_wrapped.split('\n')
        for i, line in enumerate(title_lines):
            draw.text((content_x + 2, title_y + i*45 + 2), 
                     line, fill=TEXT_SHADOW, font=title_font)
            draw.text((content_x, title_y + i*45), 
                     line, fill=TEXT_WHITE, font=title_font)
        
        # Metadata section with icons
        meta_start_y = title_y + len(title_lines) * 45 + 25
        meta_font = ImageFont.truetype(FONT_REGULAR_PATH, 26)
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        
        # Channel info
        channel_icon = "📺"
        channel_text = f"  {channel}"
        draw.text((content_x, meta_start_y), channel_icon, fill=ACCENT_GREEN, font=icon_font)
        draw.text((content_x + 40, meta_start_y), channel_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Views info
        views_icon = "👁️"
        views_text = f"  {views}"
        draw.text((content_x, meta_start_y + 45), views_icon, fill=NEON_BLUE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 45), views_text, fill=TEXT_LIGHT, font=meta_font)
        
        # Duration info
        duration_icon = "⏱️"
        duration_text = f"  {duration}"
        draw.text((content_x, meta_start_y + 90), duration_icon, fill=ACCENT_PURPLE, font=icon_font)
        draw.text((content_x + 40, meta_start_y + 90), duration_text, fill=TEXT_LIGHT, font=meta_font)
        
        # ================= PROGRESS BAR =================
        progress_y = meta_start_y + 150
        progress_width = 450
        progress_height = 8
        
        create_progress_bar(
            draw=draw,
            x=content_x,
            y=progress_y,
            width=progress_width,
            height=progress_height,
            progress_percent=60,  # You can make this dynamic
            show_time=True,
            current_time="00:00",
            total_time=duration
        )
        
        # ================= DECORATIVE ELEMENTS =================
        # Add music visualizer at bottom
        visualizer_height = 100
        visualizer = create_music_visualizer(CANVAS_W, visualizer_height)
        canvas.paste(visualizer, (0, CANVAS_H - visualizer_height), visualizer)
        
        # Add decorative circles
        circle_size = 100
        circle_x = CANVAS_W - circle_size - 40
        circle_y = 40
        
        circle_img = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle_img)
        circle_draw.ellipse([0, 0, circle_size, circle_size], 
                          outline=ACCENT_PINK, width=3)
        
        # Inner circle
        inner_size = circle_size - 25
        circle_draw.ellipse(
            [(circle_size - inner_size)//2, (circle_size - inner_size)//2,
             (circle_size + inner_size)//2, (circle_size + inner_size)//2],
            outline=NEON_BLUE, width=2
        )
        
        canvas.paste(circle_img, (circle_x, circle_y), circle_img)
        
        # Music note decoration
        music_font = ImageFont.truetype(FONT_BOLD_PATH, 44)
        music_note = "♪"
        music_x = CANVAS_W - 80
        music_y = CANVAS_H - 140
        draw.text((music_x, music_y), music_note, fill=ACCENT_PURPLE, font=music_font)
        
        # Add subtle particles/glitter
        for _ in range(40):
            x = random.randint(content_x + progress_width + 50, CANVAS_W - 50)
            y = random.randint(50, CANVAS_H - 200)
            size = random.randint(2, 4)
            color = random.choice([NEON_BLUE, ACCENT_PINK, ACCENT_PURPLE, ACCENT_GREEN])
            draw.ellipse([x, y, x + size, y + size], fill=color)
        
        # ================= SAVE =================
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
            if os.path.exists(DEFAULT_THUMB):
                print(f"[Fallback] Returning default thumbnail: {DEFAULT_THUMB}")
                return DEFAULT_THUMB
            else:
                print(f"[Fallback Error] Default thumbnail not found at {DEFAULT_THUMB}")
                return None
        except Exception as fallback_error:
            print(f"[Fallback Error] {fallback_error}")
            return None
        
    finally:
        # Clean up any partial downloads
        if thumb_path and os.path.exists(thumb_path):
            try:
                os.remove(thumb_path)
            except            async with session.get(thumburl) as resp:
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
