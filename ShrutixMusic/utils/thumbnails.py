# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com
#
# ATLEAST GIVE CREDITS IF YOU STEALING :
# ELSE NO FURTHER PUBLIC THUMBNAIL UPDATES

import os
import aiohttp
import aiofiles
import traceback
import random
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance
from py_yt import VideosSearch

CACHE_DIR = Path("cache")
CACHE_DIR.mkdir(exist_ok=True)

# Canvas size
CANVAS_W, CANVAS_H = 1280, 720

# Modern color palette
PRIMARY_COLOR = (30, 144, 255, 255)    # Dodger Blue
SECONDARY_COLOR = (138, 43, 226, 255)  # Blue Violet
ACCENT_COLOR = (255, 105, 180, 255)    # Hot Pink
NEON_GREEN = (57, 255, 20, 255)        # Neon Green
NEON_BLUE = (0, 191, 255, 255)         # Deep Sky Blue
TEXT_WHITE = (255, 255, 255, 255)
TEXT_LIGHT = (240, 240, 240, 255)
TEXT_GRAY = (200, 200, 200, 255)
GLOW_COLOR = (30, 144, 255, 150)
SHADOW_COLOR = (10, 10, 10, 180)
OVERLAY_COLOR = (0, 0, 0, 150)         # Dark overlay for text readability

# Font paths
FONT_REGULAR_PATH = "ShrutixMusic/assets/font2.ttf"
FONT_BOLD_PATH = "ShrutixMusic/assets/font3.ttf"
FALLBACK_THUMB = "ShrutixMusic/assets/temp_thumb.jpg"

def create_gradient_background(width, height):
    """Create a beautiful gradient background"""
    try:
        # Create gradient from top to bottom
        gradient = Image.new('RGB', (width, height), (20, 20, 40))
        
        # Add gradient overlay
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Draw gradient manually for better control
        for y in range(height):
            # Create gradient from dark blue to purple
            r = int(20 + (y / height) * 100)
            g = int(20 + (y / height) * 50)
            b = int(40 + (y / height) * 100)
            draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
        
        gradient = gradient.convert('RGBA')
        gradient = Image.alpha_composite(gradient, overlay)
        
        return gradient
    except Exception as e:
        print(f"[create_gradient_background Error] {e}")
        return Image.new('RGBA', (width, height), (20, 20, 40, 255))

def apply_blur_overlay(image, blur_radius=15, brightness=0.7, overlay_opacity=120):
    """Apply blur and overlay effect to background"""
    try:
        # Apply blur
        blurred = image.filter(ImageFilter.GaussianBlur(blur_radius))
        
        # Adjust brightness
        enhancer = ImageEnhance.Brightness(blurred)
        blurred = enhancer.enhance(brightness)
        
        # Add dark overlay for better text readability
        overlay = Image.new('RGBA', image.size, (0, 0, 0, overlay_opacity))
        result = Image.alpha_composite(blurred, overlay)
        
        return result
    except Exception as e:
        print(f"[apply_blur_overlay Error] {e}")
        return image

def create_rounded_rectangle(size, radius, color, border_color=None, border_width=0):
    """Create a rounded rectangle with optional border"""
    width, height = size
    image = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Draw rounded rectangle
    draw.rounded_rectangle([0, 0, width, height], radius=radius, fill=color)
    
    # Add border if specified
    if border_color and border_width > 0:
        draw.rounded_rectangle(
            [border_width//2, border_width//2, 
             width - border_width//2, height - border_width//2],
            radius=radius, outline=border_color, width=border_width
        )
    
    return image

def add_glass_effect(image, radius=20, opacity=60):
    """Add glass morphism effect to an element"""
    try:
        glass = image.copy()
        
        # Apply blur for glass effect
        glass = glass.filter(ImageFilter.GaussianBlur(2))
        
        # Create overlay for glass effect
        overlay = Image.new('RGBA', image.size, (255, 255, 255, opacity))
        glass = Image.alpha_composite(glass, overlay)
        
        return glass
    except Exception as e:
        print(f"[add_glass_effect Error] {e}")
        return image

def wrap_text_with_ellipsis(draw, text, font, max_width, max_lines=2):
    """Wrap text and add ellipsis if too long"""
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
                    # Single word too long
                    lines.append(word)
                    break
                
                if len(lines) >= max_lines:
                    # Add ellipsis to last line
                    if len(lines) == max_lines:
                        last_line = lines[-1]
                        while draw.textlength(last_line + "...", font=font) > max_width and len(last_line) > 3:
                            last_line = last_line[:-1]
                        lines[-1] = last_line + "..."
                    break
        
        if current_line and len(lines) < max_lines:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    except Exception as e:
        print(f"[wrap_text_with_ellipsis Error] {e}")
        return text[:50]

def fit_font_to_width(draw, text, max_width, font_path, start_size=36, min_size=24, max_lines=2):
    """Find optimal font size for text within width"""
    try:
        size = start_size
        while size >= min_size:
            try:
                font = ImageFont.truetype(font_path, size)
            except:
                size -= 2
                continue
            
            wrapped = wrap_text_with_ellipsis(draw, text, font, max_width, max_lines)
            lines = wrapped.split('\n')
            
            if len(lines) <= max_lines:
                # Check if all lines fit
                fits = True
                for line in lines:
                    if draw.textlength(line, font=font) > max_width:
                        fits = False
                        break
                if fits:
                    return font, wrapped
            size -= 2
        
        # Fallback to minimum size
        font = ImageFont.truetype(font_path, min_size)
        wrapped = wrap_text_with_ellipsis(draw, text, font, max_width, max_lines)
        return font, wrapped
    except Exception as e:
        print(f"[fit_font_to_width Error] {e}")
        try:
            font = ImageFont.truetype(font_path, min_size)
            return font, text[:40]
        except:
            return ImageFont.load_default(), text[:40]

def add_text_shadow(draw, text, position, font, shadow_color=SHADOW_COLOR, offset=3):
    """Add shadow to text for better readability"""
    x, y = position
    draw.text((x + offset, y + offset), text, fill=shadow_color, font=font)
    return (x, y)

def create_info_badge(text, bg_color, text_color, font_size=24, padding=15):
    """Create a badge for information display"""
    try:
        # Create temporary image to calculate text size
        temp_img = Image.new('RGB', (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        font = ImageFont.truetype(FONT_BOLD_PATH, font_size)
        
        text_width = temp_draw.textlength(text, font=font)
        text_height = font_size
        
        # Create badge
        badge_width = int(text_width) + padding * 2
        badge_height = text_height + padding
        
        badge = create_rounded_rectangle(
            (badge_width, badge_height), 
            badge_height // 2, 
            bg_color
        )
        
        # Add glass effect
        badge = add_glass_effect(badge, radius=badge_height // 2, opacity=30)
        
        # Draw text
        badge_draw = ImageDraw.Draw(badge)
        text_x = padding
        text_y = (badge_height - text_height) // 2
        
        add_text_shadow(badge_draw, text, (text_x, text_y), font, SHADOW_COLOR, 1)
        badge_draw.text((text_x, text_y), text, fill=text_color, font=font)
        
        return badge
    except Exception as e:
        print(f"[create_info_badge Error] {e}")
        return None

def create_progress_bar(width, height, progress=0.3, bg_color=(50, 50, 50), fill_color=NEON_GREEN):
    """Create a modern progress bar"""
    bar = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar)
    
    # Background
    draw.rounded_rectangle([0, 0, width, height], radius=height//2, fill=bg_color)
    
    # Progress fill
    fill_width = int(width * progress)
    if fill_width > 0:
        draw.rounded_rectangle([0, 0, fill_width, height], radius=height//2, fill=fill_color)
    
    # Add inner shadow
    shadow = Image.new('RGBA', (width, height), (0, 0, 0, 30))
    bar = Image.alpha_composite(bar, shadow)
    
    return bar

async def get_thumb(videoid: str, requested_by: str = "User"):
    """Generate thumbnail with blurred YouTube background and all details"""
    url = f"https://www.youtube.com/watch?v={videoid}"
    thumb_path = None
    
    try:
        # Fetch video data
        results = VideosSearch(url, limit=1)
        result = (await results.next())["result"][0]

        title = result.get("title", "Unknown Title")
        duration = result.get("duration", "0:00")
        thumburl = result["thumbnails"][0]["url"].split("?")[0]
        views = result.get("viewCount", {}).get("short", "0 views")
        channel = result.get("channel", {}).get("name", "Unknown Channel")
        
        # Get current time for timestamp
        current_time = datetime.now().strftime("%I:%M %p")
        
        # Format duration properly
        if ":" not in duration and duration.isdigit():
            # Convert seconds to MM:SS
            total_seconds = int(duration)
            minutes = total_seconds // 60
            seconds = total_seconds % 60
            duration = f"{minutes}:{seconds:02d}"

        # Download thumbnail
        async with aiohttp.ClientSession() as session:
            async with session.get(thumburl) as resp:
                if resp.status == 200:
                    thumb_path = CACHE_DIR / f"thumb{videoid}.png"
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())

        base_img = Image.open(thumb_path).convert("RGBA")
        
        # Create canvas with blurred YouTube thumbnail as background
        # First, resize thumbnail to cover canvas
        bg = base_img.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
        
        # Apply blur and overlay effects
        bg = apply_blur_overlay(bg, blur_radius=20, brightness=0.6, overlay_opacity=140)
        
        # Create final canvas
        canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 255))
        canvas.paste(bg, (0, 0))
        
        # Create a content area overlay (glass morphism effect)
        content_overlay = Image.new('RGBA', (CANVAS_W - 100, CANVAS_H - 100), (0, 0, 0, 0))
        content_draw = ImageDraw.Draw(content_overlay)
        
        # Create glass effect rectangle
        content_draw.rounded_rectangle(
            [0, 0, CANVAS_W - 100, CANVAS_H - 100],
            radius=40,
            fill=(255, 255, 255, 40)  # Semi-transparent white for glass effect
        )
        
        # Apply blur for glass effect
        content_overlay = content_overlay.filter(ImageFilter.GaussianBlur(10))
        
        # Place content overlay
        canvas.paste(content_overlay, (50, 50), content_overlay)
        
        draw = ImageDraw.Draw(canvas)
        
        # Add decorative elements
        
        # Top decorative wave
        wave_overlay = Image.new('RGBA', (CANVAS_W, 150), (0, 0, 0, 0))
        wave_draw = ImageDraw.Draw(wave_overlay)
        wave_draw.rectangle([0, 0, CANVAS_W, 150], fill=(30, 144, 255, 30))
        
        # Create wave pattern
        wave_points = []
        for x in range(0, CANVAS_W + 100, 100):
            wave_points.append((x, 150))
        for x in range(CANVAS_W, -100, -100):
            wave_points.append((x, 120))
        
        if len(wave_points) > 1:
            wave_draw.polygon(wave_points, fill=(30, 144, 255, 50))
        
        canvas = Image.alpha_composite(canvas, wave_overlay)
        
        # Main content layout
        
        # YouTube thumbnail preview (clear version)
        thumb_preview_size = 380
        thumb_preview_x = 80
        thumb_preview_y = (CANVAS_H - thumb_preview_size) // 2
        
        # Create thumbnail with rounded corners and border
        thumb_preview = base_img.resize((thumb_preview_size, thumb_preview_size), Image.LANCZOS)
        
        # Add rounded corners
        thumb_mask = Image.new('L', (thumb_preview_size, thumb_preview_size), 0)
        thumb_mask_draw = ImageDraw.Draw(thumb_mask)
        thumb_mask_draw.rounded_rectangle(
            [0, 0, thumb_preview_size, thumb_preview_size],
            radius=20,
            fill=255
        )
        thumb_preview.putalpha(thumb_mask)
        
        # Add border
        border_size = thumb_preview_size + 10
        border = create_rounded_rectangle(
            (border_size, border_size), 
            25, 
            (30, 144, 255, 100),
            border_color=NEON_BLUE,
            border_width=3
        )
        canvas.paste(border, 
                    (thumb_preview_x - 5, thumb_preview_y - 5), 
                    border)
        
        # Place thumbnail
        canvas.paste(thumb_preview, 
                    (thumb_preview_x, thumb_preview_y), 
                    thumb_preview)
        
        # Add play button overlay
        play_size = 70
        play_x = thumb_preview_x + (thumb_preview_size - play_size) // 2
        play_y = thumb_preview_y + (thumb_preview_size - play_size) // 2
        
        play_bg = Image.new('RGBA', (play_size, play_size), (0, 0, 0, 0))
        play_draw = ImageDraw.Draw(play_bg)
        play_draw.ellipse([0, 0, play_size, play_size], fill=ACCENT_COLOR)
        
        # Play triangle
        triangle_points = [
            (play_size * 0.35, play_size * 0.25),
            (play_size * 0.35, play_size * 0.75),
            (play_size * 0.75, play_size * 0.5)
        ]
        play_draw.polygon(triangle_points, fill=TEXT_WHITE)
        
        # Add shadow to play button
        play_shadow = play_bg.filter(ImageFilter.GaussianBlur(3))
        canvas.paste(play_shadow, (play_x, play_y), play_shadow)
        canvas.paste(play_bg, (play_x, play_y), play_bg)
        
        # Content area (right side)
        content_x = thumb_preview_x + thumb_preview_size + 60
        content_width = CANVAS_W - content_x - 80
        
        # Branding/Header
        header_font = ImageFont.truetype(FONT_BOLD_PATH, 40)
        header_text = "🎵 SHRUTIX MUSIC PLAYER"
        header_y = thumb_preview_y - 20
        
        # Draw header with shadow
        header_shadow = add_text_shadow(draw, header_text, (content_x, header_y), header_font)
        draw.text(header_shadow, header_text, fill=NEON_GREEN, font=header_font)
        
        # Now Playing indicator
        np_font = ImageFont.truetype(FONT_BOLD_PATH, 32)
        np_text = "▶ NOW PLAYING"
        np_y = header_y + 60
        
        # Create NOW PLAYING badge
        np_badge = create_info_badge(np_text, (30, 144, 255, 150), TEXT_WHITE, 28, 20)
        if np_badge:
            canvas.paste(np_badge, (content_x, np_y), np_badge)
        
        # Song Title
        title_y = np_y + 80
        title_font, title_wrapped = fit_font_to_width(
            draw, title, content_width, FONT_BOLD_PATH, 
            start_size=42, min_size=32, max_lines=2
        )
        
        # Draw title with shadow
        title_shadow = add_text_shadow(draw, title_wrapped, (content_x, title_y), title_font, offset=2)
        draw.text(title_shadow, title_wrapped, fill=TEXT_WHITE, font=title_font)
        
        # Song Details Section (Glass effect panel)
        details_y = title_y + 120
        details_panel_height = 200
        details_panel = create_rounded_rectangle(
            (content_width, details_panel_height),
            25,
            (255, 255, 255, 30)
        )
        
        # Apply glass effect
        details_panel = add_glass_effect(details_panel, radius=25, opacity=40)
        
        # Place details panel
        canvas.paste(details_panel, (content_x, details_y), details_panel)
        
        # Draw details inside panel
        details_draw = ImageDraw.Draw(canvas)
        details_font = ImageFont.truetype(FONT_REGULAR_PATH, 26)
        icon_font = ImageFont.truetype(FONT_REGULAR_PATH, 28)
        
        # Row 1: Channel and Duration
        row1_y = details_y + 30
        
        # Channel
        channel_icon = "📺"
        channel_text = f" {channel}"
        details_draw.text((content_x + 30, row1_y), channel_icon, fill=NEON_BLUE, font=icon_font)
        add_text_shadow(details_draw, channel_text, (content_x + 70, row1_y), details_font, offset=1)
        details_draw.text((content_x + 70, row1_y), channel_text, fill=TEXT_LIGHT, font=details_font)
        
        # Duration
        duration_icon = "⏱️"
        duration_text = f" {duration}"
        duration_x = content_x + content_width - 200
        details_draw.text((duration_x, row1_y), duration_icon, fill=ACCENT_COLOR, font=icon_font)
        add_text_shadow(details_draw, duration_text, (duration_x + 40, row1_y), details_font, offset=1)
        details_draw.text((duration_x + 40, row1_y), duration_text, fill=TEXT_LIGHT, font=details_font)
        
        # Row 2: Views and Requested By
        row2_y = row1_y + 60
        
        # Views
        views_icon = "👁️"
        views_text = f" {views}"
        details_draw.text((content_x + 30, row2_y), views_icon, fill=NEON_GREEN, font=icon_font)
        add_text_shadow(details_draw, views_text, (content_x + 70, row2_y), details_font, offset=1)
        details_draw.text((content_x + 70, row2_y), views_text, fill=TEXT_LIGHT, font=details_font)
        
        # Requested By
        user_icon = "👤"
        user_text = f" {requested_by}"
        user_x = content_x + content_width - 250
        details_draw.text((user_x, row2_y), user_icon, fill=(255, 215, 0, 255), font=icon_font)
        add_text_shadow(details_draw, user_text, (user_x + 40, row2_y), details_font, offset=1)
        details_draw.text((user_x + 40, row2_y), user_text, fill=TEXT_LIGHT, font=details_font)
        
        # Row 3: Progress Bar and Time
        row3_y = row2_y + 60
        
        # Progress bar
        progress_bar_width = content_width - 60
        progress_bar_height = 10
        progress_bar = create_progress_bar(
            progress_bar_width, 
            progress_bar_height, 
            progress=0.4,  # 40% progress
            bg_color=(60, 60, 60, 200),
            fill_color=NEON_GREEN
        )
        canvas.paste(progress_bar, (content_x + 30, row3_y), progress_bar)
        
        # Time stamps
        time_font = ImageFont.truetype(FONT_REGULAR_PATH, 22)
        draw.text((content_x + 30, row3_y + 20), "0:00", fill=TEXT_GRAY, font=time_font)
        
        # Current time
        time_text = f"🕒 {current_time}"
        time_width = draw.textlength(time_text, font=time_font)
        draw.text((content_x + content_width - time_width - 30, row3_y + 20), 
                 time_text, fill=TEXT_GRAY, font=time_font)
        
        # Bottom decorative elements
        
        # Music visualizer effect
        visualizer_height = 80
        visualizer = Image.new('RGBA', (CANVAS_W, visualizer_height), (0, 0, 0, 0))
        viz_draw = ImageDraw.Draw(visualizer)
        
        # Create animated-looking bars
        bar_count = 20
        bar_width = 20
        spacing = 10
        start_x = (CANVAS_W - (bar_count * (bar_width + spacing))) // 2
        
        colors = [NEON_BLUE, ACCENT_COLOR, NEON_GREEN, (255, 215, 0, 255)]
        
        for i in range(bar_count):
            x = start_x + i * (bar_width + spacing)
            # Random heights for dynamic look
            bar_height = random.randint(20, visualizer_height - 20)
            bar_y = visualizer_height - bar_height
            
            color = colors[i % len(colors)]
            
            # Draw bar with gradient
            for h in range(bar_height):
                alpha = int(255 * (h / bar_height))
                viz_draw.rectangle(
                    [x, bar_y + h, x + bar_width, bar_y + h + 1],
                    fill=(color[0], color[1], color[2], alpha)
                )
        
        canvas.paste(visualizer, (0, CANVAS_H - visualizer_height), visualizer)
        
        # Add decorative corner elements
        
        # Top-left decorative circle
        circle_size = 80
        circle_img = Image.new('RGBA', (circle_size, circle_size), (0, 0, 0, 0))
        circle_draw = ImageDraw.Draw(circle_img)
        circle_draw.ellipse([0, 0, circle_size, circle_size], outline=NEON_BLUE, width=3)
        circle_draw.ellipse([10, 10, circle_size-10, circle_size-10], outline=ACCENT_COLOR, width=2)
        canvas.paste(circle_img, (40, 40), circle_img)
        
        # Bottom-right music note
        music_font = ImageFont.truetype(FONT_BOLD_PATH, 60)
        music_note = "♪"
        music_x = CANVAS_W - 100
        music_y = CANVAS_H - 120
        add_text_shadow(draw, music_note, (music_x, music_y), music_font, offset=3)
        draw.text((music_x, music_y), music_note, fill=ACCENT_COLOR, font=music_font)
        
        # Add subtle floating particles
        for _ in range(30):
            x = random.randint(0, CANVAS_W)
            y = random.randint(0, CANVAS_H)
            size = random.randint(2, 4)
            color = random.choice([NEON_BLUE, ACCENT_COLOR, NEON_GREEN])
            alpha = random.randint(100, 200)
            draw.ellipse([x, y, x + size, y + size], 
                        fill=(color[0], color[1], color[2], alpha))
        
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

# For backward compatibility
async def get_thumb_legacy(videoid: str):
    """Legacy function for backward compatibility"""
    return await get_thumb(videoid, "Listener")
