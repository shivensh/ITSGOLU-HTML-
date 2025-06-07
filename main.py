import os
import re
import urllib.parse
import html
import json
from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    CallbackQuery,
    ReplyKeyboardRemove # To remove the reply keyboard when not needed
)
from pyrogram.enums import ParseMode

# =========================================================
#             BOT CONFIGURATION - EASY TO FILL
# =========================================================

# 1. API ID (Get from my.telegram.org)
#    - Environment Variable: API_ID
#    - Default if not set: 0 (Bot won't run without it)
API_ID = os.getenv("API_ID", 22593658)

# 2. API HASH (Get from my.telegram.org)
#    - Environment Variable: API_HASH
#    - Default if not set: "" (Bot won't run without it)
API_HASH = os.getenv("API_HASH", "511d0fd8542ada4c0aba4e47bd0892ee")

# 3. BOT TOKEN (Get from @BotFather)
#    - Environment Variable: BOT_TOKEN
#    - Default if not set: "" (Bot won't run without it)
BOT_TOKEN = os.getenv("BOT_TOKEN", "7775228959:AAFOC1UXl5X4cKGpIr3i1Q2eeCHJjkpcM-Q")

# 4. OWNER ID (Your Telegram User ID - Get from @userinfobot or @GetMyID_bot)
#    - Environment Variable: OWNER_ID
#    - Default if not set: 0 (Crucial for admin access)
OWNER_ID = int(os.getenv("OWNER_ID", 7740514033))

# --- OPTIONAL DEFAULTS (Can be changed via bot commands later) ---

# 5. DEFAULT HTML FILE USERNAME (for generated HTML pages)
#    - Environment Variable: HTML_FILE_USERNAME
#    - Default if not set: "user"
DEFAULT_HTML_USERNAME = os.getenv("HTML_FILE_USERNAME", "user")

# 6. DEFAULT HTML FILE PASSWORD (for generated HTML pages)
#    - Environment Variable: HTML_FILE_PASSWORD
#    - Default if not set: "pass"
DEFAULT_HTML_PASSWORD = os.getenv("HTML_FILE_PASSWORD", "pass")

# 7. YOUR DISPLAY NAME (shown in generated HTML pages)
#    - Environment Variable: YOUR_NAME_FOR_DISPLAY
#    - Default if not set: "Engineer Babu"
DEFAULT_DISPLAY_NAME = os.getenv("YOUR_NAME_FOR_DISPLAY", "धन्देरवाल")

# 8. YOUR TELEGRAM CHANNEL LINK (e.g., https://t.me/your_channel)
#    - Environment Variable: YOUR_CHANNEL_LINK
#    - Default if not set: "" (will use a generic Telegram link if invalid)
DEFAULT_CHANNEL_LINK = os.getenv("YOUR_CHANNEL_LINK", "https://t.me/+G2PAXJs-fUM1OWFl")

# 9. YOUR CONTACT LINK (e.g., https://t.me/your_username or a group link)
#    - Environment Variable: CONTACT_LINK
#    - Default if not set: "" (will use a generic Telegram link if invalid)
DEFAULT_CONTACT_LINK = os.getenv("CONTACT_LINK", "https://t.me/+G2PAXJs-fUM1OWFl")

# 10. SUDO USERS (list of Telegram User IDs who can also use admin commands)
#     - Environment Variable: SUDO_USERS (comma-separated, e.g., "12345,67890")
#     - Default if not set: []
DEFAULT_SUDO_USERS = [7740514033]
sudo_users_env = os.getenv("SUDO_USERS")
if sudo_users_env:
    try:
        DEFAULT_SUDO_USERS = list(map(int, sudo_users_env.split(',')))
    except ValueError:
        print("Warning: SUDO_USERS environment variable contains non-integer values. Ignoring.")
        DEFAULT_SUDO_USERS = []


# =========================================================
#     DO NOT EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING!
# =========================================================

# Filename for persistent configuration (managed by the bot)
CONFIG_FILE = "config.json"
OUTPUT_HTML_FOLDER = "generated_html"

# Global config dictionary, loaded at bot startup
config = {}

def load_config():
    """Loads configuration from config.json or environment variables."""
    global config
    
    # Initialize with default values
    config.update({
        "API_ID": API_ID,
        "API_HASH": API_HASH,
        "BOT_TOKEN": BOT_TOKEN,
        "OWNER_ID": OWNER_ID,
        "HTML_FILE_USERNAME": DEFAULT_HTML_USERNAME,
        "HTML_FILE_PASSWORD": DEFAULT_HTML_PASSWORD,
        "YOUR_NAME_FOR_DISPLAY": DEFAULT_DISPLAY_NAME,
        "YOUR_CHANNEL_LINK": DEFAULT_CHANNEL_LINK,
        "CONTACT_LINK": DEFAULT_CONTACT_LINK,
        "SUDO_USERS": DEFAULT_SUDO_USERS
    })

    # Load from config.json if it exists (overrides defaults and env vars for modifiable settings)
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                loaded_json_config = json.load(f)
                # Only update the settings that can be modified by bot commands
                for key in ["OWNER_ID", "SUDO_USERS", "HTML_FILE_USERNAME", 
                            "HTML_FILE_PASSWORD", "YOUR_NAME_FOR_DISPLAY", 
                            "YOUR_CHANNEL_LINK", "CONTACT_LINK"]:
                    if key in loaded_json_config:
                        if key == "OWNER_ID" and isinstance(loaded_json_config[key], (int, str)):
                            config[key] = int(loaded_json_config[key])
                        elif key == "SUDO_USERS" and isinstance(loaded_json_config[key], list):
                             config[key] = [int(uid) for uid in loaded_json_config[key] if isinstance(uid, (int, str)) and str(uid).isdigit()]
                        else:
                            config[key] = loaded_json_config[key]
            print("Configuration loaded from config.json")
        except json.JSONDecodeError:
            print("Error reading config.json, using environment variables or hardcoded defaults.")
    else:
        print("config.json not found, using environment variables or hardcoded defaults.")

    # Validate URLs after loading all configs
    if not (config["YOUR_CHANNEL_LINK"].startswith("http://") or config["YOUR_CHANNEL_LINK"].startswith("https://")):
        config["YOUR_CHANNEL_LINK"] = "" # Invalid URL, treat as empty

    if not (config["CONTACT_LINK"].startswith("http://") or config["CONTACT_LINK"].startswith("https://")):
        config["CONTACT_LINK"] = "" # Invalid URL, treat as empty

# Load initial config
load_config()

def save_config_to_file():
    """Saves the current global config to config.json."""
    global config
    try:
        # Only save the non-sensitive and modifiable parts to config.json
        saveable_config = {
            "OWNER_ID": config["OWNER_ID"],
            "SUDO_USERS": config["SUDO_USERS"],
            "HTML_FILE_USERNAME": config["HTML_FILE_USERNAME"],
            "HTML_FILE_PASSWORD": config["HTML_FILE_PASSWORD"],
            "YOUR_NAME_FOR_DISPLAY": config["YOUR_NAME_FOR_DISPLAY"],
            "YOUR_CHANNEL_LINK": config["YOUR_CHANNEL_LINK"],
            "CONTACT_LINK": config["CONTACT_LINK"]
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(saveable_config, f, indent=4)
        print("Configuration saved to config.json")
    except Exception as e:
        print(f"Error saving config to config.json: {e}")

# Initialize Pyrogram Client
app = Client(
    "my_bot",
    api_id=config["API_ID"],
    api_hash=config["API_HASH"],
    bot_token=config["BOT_TOKEN"]
)

# Decorator to check if user is owner or sudo
def authorized_users_only(func):
    async def wrapper(client, update):
        user_id = update.from_user.id
        if user_id == config["OWNER_ID"] or user_id in config["SUDO_USERS"]:
            await func(client, update)
        else:
            unauth_message = "🚫 You are not authorized to use this command."
            if isinstance(update, Message):
                await update.reply_text(unauth_message, reply_markup=ReplyKeyboardRemove())
            elif isinstance(update, CallbackQuery):
                await update.answer(unauth_message, show_alert=True) # Show as a pop-up alert
    return wrapper

# --- Helper Functions (No changes needed here for UX/Config) ---
def extract_names_and_urls(file_content):
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

def categorize_urls(urls):
    videos = []
    pdfs = []
    others = []

    for name, url in urls:
        new_url = url
        
        drive_file_id_match = re.search(r'drive\.google\.com/file/d/([a-zA-Z0-9_-]+)(/view)?', url)
        if drive_file_id_match:
            file_id = drive_file_id_match.group(1)
            new_url = f"https://drive.google.com/file/d/{file_id}/preview"
            pdfs.append((name, new_url))
            continue

        elif "cdn-wl-assets.classplus.co" in url and ".pdf" in url:
            encoded_url = urllib.parse.quote_plus(url)
            new_url = f"https://docs.google.com/viewer?url={encoded_url}&embedded=true"
            pdfs.append((name, new_url))
            continue
        
        elif "onedrive.live.com/" in url or "1drv.ms/" in url:
            encoded_url = urllib.parse.quote_plus(url)
            new_url = f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
            pdfs.append((name, new_url))
            continue

        elif "media-cdn.classplusapp.com/" in url or "cpvod.testbook" in url:
            new_url = f"https://api.extractor.workers.dev/player?url={url}"
            videos.append((name, new_url))

        elif "media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/" in url or "media-cdn.classplusapp.com/1681/" in url or "media-cdn.classplusapp.com/tencent/" in url:
            new_url = f"https://dragoapi.vercel.app/video/{url}"
            videos.append((name, new_url))

        elif "akamaized.net/" in url or "1942403233.rsc.cdn77.org/" in url:
            new_url = f"https://www.khanglobalstudies.com/player?src={url}"
            videos.append((name, new_url))

        elif "/master.mpd" in url:
            vid_id = url.split("/")[-2]
            new_url = f"https://player.muftukmall.site/?id={vid_id}"
            videos.append((name, new_url))

        elif ".zip" in url:
            new_url = f"https://video.pablocoder.eu.org/appx-zip?url={url}"
            videos.append((name, new_url))

        elif "d1d34p8vz63oiq.cloudfront.net/" in url:
            new_url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={None}"
            videos.append((name, new_url))

        elif "youtube.com/embed" in url:
            yt_id = url.split("/")[-1]
            new_url = f"https://www.youtube.com/watch?v={yt_id}"
            videos.append((name, new_url))

        elif ".m3u8" in url:
            videos.append((name, url))
        elif ".mp4" in url:
            videos.append((name, url))
        
        elif "mega.nz/" in url:
            others.append((name, url))
            continue

        elif "pdf" in url:
            pdfs.append((name, url))
        else:
            others.append((name, url))

    return videos, pdfs, others

def generate_html(file_name, videos, pdfs, others):
    file_name_without_extension = os.path.splitext(file_name)[0]

    video_links = "".join(f'<a href="#" onclick="playVideo(\'{url}\')" data-original-url="{url}"><svg class="w-5 h-5 mr-3 text-red-400" fill="currentColor" viewBox="0 0 20 20"><path d="M2 6a2 2 0 012-2h12a2 2 0 012 2v8a2 2 0 01-2 2H4a2 2 0 01-2-2V6zm3.455 1.636A.5.5 0 015.8 7h8.4a.5.5 0 01.345.864L10 12.416 5.455 7.636z"></path></svg>{name}</a>' for name, url in videos)
    pdf_links = "".join(f'<a href="#" onclick="openPdf(\'{html.escape(url)}\', \'{html.escape(name)}\'); return false;" data-original-url="{url}"><svg class="w-5 h-5 mr-3 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.414L16.586 7A2 2 0 0117 8.414V16a2 2 0 01-2 2H5a2 2 0 01-2-2V4zm6 1a1 1 0 100 2h3a1 1 0 100-2h-3zm-3 8a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path></svg>{name}</a>' for name, url in pdfs)
    other_links = "".join(f'<a href="{url}" target="_blank"><svg class="w-5 h-5 mr-3 text-green-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M9.293 2.293a1 1 0 011.414 0l7 7A1 1 0 0117 11h-1v6a1 2 0 01-1 1h-2a1 1 0 01-1-1v-3a1 2 0 00-1-1H9a1 1 0 00-1 1v3a1 2 0 01-1 1H5a1 1 0 01-1-1v-6H3a1 1 0 01-.707-1.707l7-7z" clip-rule="evenodd"></path></svg>{name}</a>' for name, url in others)

    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name_without_extension}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .video-js {{
            width: 100% !important;
            height: auto !important;
        }}
        body {{
            font-family: 'Inter', sans-serif;
            transition: background-color 0.3s ease, color 0.3s ease;
        }}
        .active-tab {{
            background-color: #3b82f6;
            color: white;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.4);
        }}
        .active-content {{
            display: block;
        }}
        .video-list a, .pdf-list a, .other-list a {{
            display: flex;
            align-items: center;
            padding: 12px 15px;
            margin: 8px 0;
            border-radius: 0.5rem;
            text-decoration: none;
            font-weight: 500;
            transition: all 0.3s ease;
            border: 1px solid;
        }}
        html.dark .bg-main {{ background-color: #1a202c; }}
        html.dark .text-main {{ color: #e2e8f0; }}
        html.dark .card-bg {{ background-color: #2d3748; }}
        html.dark .header-bg {{ background-color: #1a202c; color: white; }}
        html.dark .tab-bg {{ background-color: #374151; color: #9ca3af; }}
        html.dark .tab-hover:hover {{ background-color: #4a5568; }}
        html.dark .content-bg {{ background-color: #374151; }}
        html.dark .border-main {{ border-color: #4a5568; }}
        html.dark .footer-border {{ border-color: #2d3748; }}
        html.dark .footer-text {{ color: #a0aec0; }}
        html.dark .input-field {{ background-color: #374151; color: #e2e8f0; border-color: #4a5568; }}
        html.dark .error-text {{ color: #f87171; }}
        html.dark .blue-link {{ color: #93c5fd; }}
        html.dark .blue-link:hover {{ color: #bfdbfe; }}
        html.dark .btn-blue {{ background-color: #2563eb; color: white; }}
        html.dark .btn-blue:hover {{ background-color: #1d4ed8; }}
        html.dark .video-list a, html.dark .pdf-list a, html.dark .other-list a {{
            background: #374151;
            color: #93c5fd;
            border-color: #4b5563;
        }}
        html.dark .video-list a:hover, html.dark .pdf-list a:hover, html.dark .other-list a:hover {{
            background: #4b5563;
            color: #bfdbfe;
        }}

        html.light .bg-main {{ background-color: #f7fafc; }}
        html.light .text-main {{ color: #2d3748; }}
        html.light .card-bg {{ background-color: #ffffff; }}
        html.light .header-bg {{ background-color: #edf2f7; color: #2d3748; }}
        html.light .tab-bg {{ background-color: #edf2f7; color: #4a5568; }}
        html.light .tab-hover:hover {{ background-color: #e2e8f0; }}
        html.light .content-bg {{ background-color: #edf2f7; }}
        html.light .border-main {{ border-color: #cbd5e0; }}
        html.light .footer-border {{ border-color: #e2e8f0; }}
        html.light .footer-text {{ color: #718096; }}
        html.light .input-field {{ background-color: #ffffff; color: #2d3748; border-color: #cbd5e0; }}
        html.light .error-text {{ color: #e53e3e; }}
        html.light .blue-link {{ color: #3182ce; }}
        html.light .blue-link:hover {{ color: #2b6cb0; }}
        html.light .btn-blue {{ background-color: #4299e1; color: white; }}
        html.light .btn-blue:hover {{ background-color: #3182ce; }}
        html.light .video-list a, html.light .pdf-list a, html.light .other-list a {{
            background: #ffffff;
            color: #2c5282;
            border-color: #e2e8f0;
        }}
        html.light .video-list a:hover, html.light .pdf-list a:hover, html.light .other-list a:hover {{
            background: #edf2f7;
            color: #2b6cb0;
        }}

        .theme-toggle-btn {{
            background-color: #f3f4f6;
            color: #1f2937;
            border-radius: 9999px;
            padding: 0.5rem;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            z-index: 10;
        }}

        html.dark .theme-toggle-btn {{
            background-color: #374151;
            color: #93c5fd;
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        }}

        .theme-toggle-btn:hover {{
            transform: scale(1.1);
        }}

        .loader {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3b82f6;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}

        .pdf-dropdown-menu {{
            position: relative;
            background-color: #374151;
            border-radius: 0.5rem;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
            padding: 0.5rem;
            min-width: 60px;
            text-align: center;
        }}
        html.light .pdf-dropdown-menu {{
            background-color: #edf2f7;
        }}
        .pdf-dropdown-menu button {{
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 0.5rem;
            margin: 0;
            border-radius: 0.375rem;
            font-size: 0.875rem;
            transition: background-color 0.2s ease;
        }}
        html.dark .pdf-dropdown-menu button {{
            background-color: #4b5563;
            color: white;
        }}
        html.light .pdf-dropdown-menu button {{
            background-color: #d1d5db;
            color: #1f2937;
        }}
        html.dark .pdf-dropdown-menu button:hover {{
            background-color: #6b7280;
        }}
        html.light .pdf-dropdown-menu button:hover {{
            background-color: #e5e7eb;
        }}
        .highlight-link {{
            border: 2px solid;
            animation: highlight-pulse 1s infinite alternate;
        }}

        @keyframes highlight-pulse {{
            from {{ transform: scale(1); opacity: 1; }}
            to {{ transform: scale(1.02); opacity: 0.9; }}
        }}

    </style>
</head>
<body class="min-h-screen flex flex-col items-center justify-center p-4 bg-main text-main">

    <div id="password-prompt" class="card-bg p-8 rounded-lg shadow-xl max-w-md w-full text-center relative">
        <h2 class="text-3xl font-bold text-blue-500 mb-6">Access Required</h2>
        <button id="password-theme-toggle" class="theme-toggle-btn absolute top-4 right-4">
            <i class="fas fa-moon"></i> </button>
        <input type="text" id="username-input" placeholder="Enter Username" required
               class="w-full p-3 mb-4 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 input-field">
        
        <div class="relative mb-6">
            <input type="password" id="password-input" placeholder="Enter Password" required
                   class="w-full p-3 pr-10 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 input-field">
            <span class="absolute inset-y-0 right-0 pr-3 flex items-center cursor-pointer" onclick="togglePasswordVisibility()">
                <i id="toggle-password-icon" class="fas fa-eye"></i> </i>
            </span>
        </div>

        <button onclick="checkPassword()"
                class="font-bold py-3 px-8 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-lg btn-blue">
            Access Content
        </button>
        <div class="error-message mt-4 font-semibold error-text"></div>
        
        <div class="text-center text-sm mt-4 pt-2 border-t footer-border footer-text">
            <a href="{config['YOUR_CHANNEL_LINK'] or 'about:blank'}" target="_blank" class="font-semibold transition-colors duration-200 blue-link hover:blue-link">{config['YOUR_NAME_FOR_DISPLAY']}</a>
        </div>
    </div>

    <div id="protectedContent" class="hidden w-full max-w-4xl mx-auto card-bg rounded-lg shadow-xl p-6 md:p-8 mt-6 relative">
        <button id="main-theme-toggle" class="theme-toggle-btn absolute top-4 right-4">
            <i class="fas fa-sun"></i> </button>

        <div class="header-bg p-4 rounded-t-lg text-center mb-6">
            <h1 class="text-2xl md:text-3xl font-extrabold">{file_name_without_extension}</h1>
            <p class="text-sm md:text-base text-gray-400 mt-2">
                <a href="{config['YOUR_CHANNEL_LINK'] or 'about:blank'}" target="_blank" class="font-semibold transition-colors duration-200 blue-link hover:blue-link">{config['YOUR_NAME_FOR_DISPLAY']}</a>
            </p>
        </div>

        <div id="player-container" class="mb-8 bg-black rounded-lg overflow-hidden relative" style="padding-top: 56.25%;">
            <video id="engineer-babu-player" class="video-js vjs-default-skin absolute top-0 left-0 w-full h-full" controls preload="auto">
                <p class="vjs-no-js text-white p-4">
                    To view this video please enable JavaScript, and consider upgrading to a web browser that
                    <a href="https://videojs.com/html5-video-support/" target="_blank" class="blue-link hover:blue-link">supports HTML5 video</a>
                </p>
            </video>
            <iframe id="iframe-player" class="hidden absolute top-0 left-0 w-full h-full" allowfullscreen allow="encrypted-media"></iframe>
            <div id="video-controls" class="absolute top-4 right-4 flex flex-col gap-2 z-10 hidden">
                <button id="video-location-btn" onclick="findVideoLocation()"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg">
                    <i class="fas fa-map-marker-alt"></i>
                </button>
            </div>
        </div>

        <div id="pdf-viewer-container" class="hidden mb-8 bg-gray-800 rounded-lg overflow-hidden relative" style="height: 85vh;">
            <iframe id="pdf-iframe-viewer" class="absolute top-0 left-0 w-full h-full" allowfullscreen></iframe>
            <div class="absolute top-4 right-4 flex flex-col gap-2">
                <button id="pdf-menu-toggle-btn"
                        class="bg-gray-600 hover:bg-gray-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg z-10 hidden">
                    <i class="fas fa-bars"></i>
                </button>
                <div id="pdf-dropdown-menu"
                     class="hidden flex-col gap-2 bg-gray-700 p-2 rounded-lg shadow-md z-20">
                    <button id="download-pdf-btn" onclick="triggerPdfDownload()"
                            class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg">
                        <i class="fas fa-download"></i>
                    </button>
                    <button id="share-pdf-btn"
                            class="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg">
                        <i class="fas fa-share-alt"></i>
                    </button>
                </div>
                <button id="fullscreen-pdf-btn" onclick="togglePdfFullscreen()"
                        class="bg-purple-600 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg z-10 hidden">
                    <i class="fas fa-expand"></i>
                </button>
                <button id="pdf-location-btn" onclick="findPdfLocation()"
                        class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg z-10 hidden">
                    <i class="fas fa-map-marker-alt"></i>
                </button>
                <button id="close-pdf-btn" onclick="returnToLists()"
                        class="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-full text-sm shadow-lg z-10">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        </div>

        <div class="flex flex-wrap justify-center mb-6 gap-2">
            <div class="tab flex-1 min-w-[100px] text-center py-3 px-4 font-semibold rounded-md cursor-pointer transition-all duration-300 tab-bg tab-hover active-tab"
                 data-tab="videos" onclick="showContent('videos', this)">Videos</div>
            <div class="tab flex-1 min-w-[100px] text-center py-3 px-4 font-semibold rounded-md cursor-pointer transition-all duration-300 tab-bg tab-hover"
                 data-tab="pdfs" onclick="showContent('pdfs', this)">PDFs</div>
            <div class="tab flex-1 min-w-[100px] text-center py-3 px-4 font-semibold rounded-md cursor-pointer transition-all duration-300 tab-bg tab-hover"
                 data-tab="others" onclick="showContent('others', this)">Others</div>
        </div>

        <div class="mb-6 flex gap-2">
            <input type="text" id="searchInput" onkeyup="filterLinks()" placeholder="Search links..."
                   class="flex-1 p-3 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 input-field">
            <button onclick="filterLinks()"
                    class="btn-blue py-3 px-6 rounded-md font-semibold transition-all duration-300">
                <i class="fas fa-search"></i>
            </button>
        </div>

        <div id="videos" class="content active-content p-6 rounded-lg shadow-inner content-bg">
            <h2 class="text-xl font-bold blue-link mb-4 border-b pb-2 border-main">All Video Lectures</h2>
            <div class="video-list">
                {video_links}
            </div>
        </div>

        <div id="pdfs" class="content hidden p-6 rounded-lg shadow-inner content-bg">
            <h2 class="text-xl font-bold blue-link mb-4 border-b pb-2 border-main">All PDFs</h2>
            <div class="pdf-list">
                {pdf_links}
            </div>
        </div>

        <div id="others" class="content hidden p-6 rounded-lg shadow-inner content-bg">
            <h2 class="text-xl font-bold blue-link mb-4 border-b pb-2 border-main">Other Resources</h2>
            <div class="other-list">
                {other_links}
            </div>
        </div>

        <div class="text-center text-sm mt-8 pt-4 footer-border footer-text">
            <a href="{config['YOUR_CHANNEL_LINK'] or 'about:blank'}" target="_blank" class="font-semibold transition-colors duration-200 blue-link hover:blue-link">{config['YOUR_NAME_FOR_DISPLAY']}</a>
        </div>
    </div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script>
        const HTML_USERNAME = "{config['HTML_FILE_USERNAME']}";
        const HTML_PASSWORD = "{config['HTML_FILE_PASSWORD']}";
        const protectedContent = document.getElementById('protectedContent');
        const passwordPrompt = document.getElementById('password-prompt');
        const errorMessageDiv = passwordPrompt.querySelector('.error-message');
        const htmlElement = document.documentElement;

        // Global variables for currently active media
        let currentPdfUrl = ''; // Stores unescaped PDF URL
        let currentPdfName = '';
        let currentVideoUrl = ''; // Stores unescaped Video URL

        // Helper function to unescape HTML entities
        function htmlUnescape(str) {{
            var el = document.createElement('textarea');
            el.innerHTML = str;
            return el.textContent;
        }}

        function applyTheme(theme) {{
            const passwordThemeToggleBtn = document.getElementById('password-theme-toggle');
            const mainThemeToggleBtn = document.getElementById('main-theme-toggle');

            if (passwordThemeToggleBtn && mainThemeToggleBtn) {{
                if (theme === 'dark') {{
                    htmlElement.classList.add('dark');
                    htmlElement.classList.remove('light');
                    localStorage.setItem('theme', 'dark');
                    passwordThemeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
                    mainThemeToggleBtn.innerHTML = '<i class="fas fa-sun"></i>';
                }} else {{
                    htmlElement.classList.add('light');
                    htmlElement.classList.remove('dark');
                    localStorage.setItem('theme', 'light');
                    passwordThemeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
                    mainThemeToggleBtn.innerHTML = '<i class="fas fa-moon"></i>';
                }}
            }}
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme) {{
                applyTheme(savedTheme);
            }} else {{
                applyTheme("dark");
            }}

            const passwordThemeToggleBtn = document.getElementById('password-theme-toggle');
            if (passwordThemeToggleBtn) {{
                passwordThemeToggleBtn.addEventListener('click', () => {{
                    const currentTheme = htmlElement.classList.contains('dark') ? 'dark' : 'light';
                    applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
                }});
            }}

            const mainThemeToggleBtn = document.getElementById('main-theme-toggle');
            if (mainThemeToggleBtn) {{
                mainThemeToggleBtn.addEventListener('click', () => {{
                    const currentTheme = htmlElement.classList.contains('dark') ? 'dark' : 'light';
                    applyTheme(currentTheme === 'dark' ? 'light' : 'dark');
                }});
            }}

            const pdfMenuToggleButton = document.getElementById('pdf-menu-toggle-btn');
            const pdfDropdownMenu = document.getElementById('pdf-dropdown-menu');

            if (pdfMenuToggleButton) {{
                pdfMenuToggleButton.addEventListener('click', (event) => {{
                    pdfDropdownMenu.classList.toggle('hidden');
                    event.stopPropagation();
                }});
            }}

            document.addEventListener('click', (event) => {{
                if (pdfDropdownMenu && !pdfDropdownMenu.contains(event.target) && pdfMenuToggleButton && !pdfMenuToggleButton.contains(event.target)) {{
                    pdfDropdownMenu.classList.add('hidden');
                }}
            }});
        }});

        function checkPassword() {{
            const enteredUsername = document.getElementById('username-input').value;
            const enteredPassword = document.getElementById('password-input').value;

            if (enteredUsername === HTML_USERNAME && enteredPassword === HTML_PASSWORD) {{
                passwordPrompt.style.display = 'none';
                protectedContent.classList.remove('hidden');
                protectedContent.classList.add('flex', 'flex-col');

                const player = videojs('engineer-babu-player', {{
                    controls: true,
                    autoplay: false,
                    preload: 'auto',
                    fluid: true,
                    controlBar: {{
                        children: [
                            'playToggle',
                            'volumePanel',
                            'currentTimeDisplay',
                            'timeDivider',
                            'durationDisplay',
                            'liveDisplay',
                            'remainingTimeDisplay',
                            'customControlSpacer',
                            'playbackRateMenuButton',
                            'chaptersButton',
                            'descriptionsButton',
                            'subsCapsButton',
                            'audioTrackButton',
                            'fullscreenToggle'
                        ]
                    }}
                }});
                document.getElementById('engineer-babu-player').classList.remove('hidden');
                document.getElementById('iframe-player').classList.add('hidden');
                
                document.getElementById('pdf-viewer-container').classList.add('hidden');
                // Video controls are hidden by default and shown if a video is loaded by playVideo
                document.getElementById('video-controls').classList.add('hidden'); 

                showContent('videos', document.querySelector('.tab[data-tab="videos"]'));
            }} else {{
                errorMessageDiv.textContent = "Incorrect username or password. Access denied.";
            }}
        }}

        function togglePasswordVisibility() {{
            const passwordInput = document.getElementById('password-input');
            const toggleIcon = document.getElementById('toggle-password-icon');

            if (passwordInput.type === 'password') {{
                passwordInput.type = 'text';
                toggleIcon.classList.remove('fa-eye');
                toggleIcon.classList.add('fa-eye-slash');
            }} else {{
                passwordInput.type = 'password';
                toggleIcon.classList.remove('fa-eye-slash');
                toggleIcon.classList.add('fa-eye');
            }}
        }}

        async function copyToClipboard(text) {{
            try {{
                await navigator.clipboard.writeText(text);
                alert('Link copied to clipboard!');
            }} catch (err) {{
                console.error('Failed to copy text using Clipboard API:', err);
                const textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    alert('Link copied to clipboard!');
                }} catch (err) {{
                    console.error('Fallback: Oops, unable to copy', err);
                    prompt("Copy this link manually:", text);
                }}
                document.body.removeChild(textArea);
            }}
        }}

        function playVideo(url) {{
            console.log("Attempting to play video:", url);
            const videoPlayer = videojs('engineer-babu-player');
            const iframePlayer = document.getElementById('iframe-player');
            const videoElement = document.getElementById('engineer-babu-player');
            const videoPlayerContainer = document.getElementById('player-container');
            const videoControls = document.getElementById('video-controls');
            
            const pdfViewer = document.getElementById('pdf-viewer-container');
            const pdfIframe = document.getElementById('pdf-iframe-viewer');
            const closePdfBtn = document.getElementById('close-pdf-btn');
            const fullscreenPdfBtn = document.getElementById('fullscreen-pdf-btn');
            const pdfMenuToggleButton = document.getElementById('pdf-menu-toggle-btn');
            const pdfDropdownMenu = document.getElementById('pdf-dropdown-menu');
            const pdfLocationBtn = document.getElementById('pdf-location-btn');

            // Clear PDF state
            pdfViewer.classList.add('hidden');
            if (pdfIframe) {{ pdfIframe.src = ""; }}
            closePdfBtn.classList.add('hidden');
            fullscreenPdfBtn.classList.add('hidden');
            pdfMenuToggleButton.classList.add('hidden');
            pdfDropdownMenu.classList.add('hidden');
            pdfLocationBtn.classList.add('hidden');

            // Set Video state
            videoPlayerContainer.classList.remove('hidden');
            videoControls.classList.remove('hidden'); // Show video controls
            document.querySelector('.flex.flex-wrap.justify-center.mb-6.gap-2').classList.remove('hidden'); // Ensure tabs are visible

            currentVideoUrl = url; // Store the unescaped URL

            const isIframeUrl = url.includes('api.extractor.workers.dev') ||
                                url.includes('dragoapi.vercel.app') ||
                                url.includes('anonymouspwplayer-b99f57957198.herokuapp.com') ||
                                url.includes('player.muftukmall.site') ||
                                url.includes('video.pablocoder.eu.org/appx-zip');

            if (isIframeUrl) {{
                console.log("Using iframe for URL:", url);
                videoPlayer.pause();
                videoPlayer.src({{ src: "", type: "video/mp4" }}); // Clear video.js source
                videoElement.classList.add('hidden');
                iframePlayer.classList.remove('hidden');
                iframePlayer.src = url;
            }} else if (url.includes('.m3u8')) {{
                console.log("Using video.js for m3u8:", url);
                iframePlayer.src = "";
                iframePlayer.classList.add('hidden');
                videoElement.classList.remove('hidden');
                videoPlayer.src({{ src: url, type: 'application/x-mpegURL' }});
                videoPlayer.load();
                videoPlayer.play().catch(error => {{
                    console.error("Video playback failed (m3u8, direct link, or HLS issue):", error);
                    window.open(url, '_blank');
                }});
            }} else if (url.includes('.mp4')) {{
                console.log("Using video.js for mp4:", url);
                iframePlayer.src = "";
                iframePlayer.classList.add('hidden');
                videoElement.classList.remove('hidden');
                videoPlayer.src({{ src: url, type: 'video/mp4' }});
                videoPlayer.load();
                videoPlayer.play().catch(error => {{
                    console.error("Video playback failed (mp4, direct link):", error);
                    window.open(url, '_blank');
                }});
            }} else {{
                console.log("Opening URL in new tab (unhandled type):", url);
                window.open(url, '_blank');
                return;
            }}
        }}

        function openPdf(url, name) {{
            const videoPlayerContainer = document.getElementById('player-container');
            const videoControls = document.getElementById('video-controls'); // Get video controls
            const pdfViewer = document.getElementById('pdf-viewer-container');
            const pdfIframe = document.getElementById('pdf-iframe-viewer');
            const closePdfBtn = document.getElementById('close-pdf-btn');
            const fullscreenPdfBtn = document.getElementById('fullscreen-pdf-btn'); 
            const contentSections = document.querySelectorAll('.content'); 
            const tabControls = document.querySelector('.flex.flex-wrap.justify-center.mb-6.gap-2'); 
            const tabs = document.querySelectorAll('.tab'); 
            const videoJsPlayer = videojs('engineer-babu-player');
            const pdfMenuToggleButton = document.getElementById('pdf-menu-toggle-btn'); 
            const pdfDropdownMenu = document.getElementById('pdf-dropdown-menu'); 
            const downloadPdfBtn = document.getElementById('download-pdf-btn'); 
            const sharePdfBtn = document.getElementById('share-pdf-btn'); 
            const pdfLocationBtn = document.getElementById('pdf-location-btn'); 

            currentPdfUrl = htmlUnescape(url); // Store the unescaped version for comparison
            currentPdfName = htmlUnescape(name); // Store the unescaped version

            // Clear Video state
            videoJsPlayer.pause();
            videoJsPlayer.src({{ src: "", type: "video/mp4" }});
            document.getElementById('iframe-player').src = "";
            videoPlayerContainer.classList.add('hidden');
            videoControls.classList.add('hidden'); // Hide video controls

            contentSections.forEach(section => section.classList.add('hidden'));
            tabs.forEach(tab => {{ 
                tab.classList.add('hidden');
            }});
            tabControls.classList.add('hidden');

            // Set PDF state
            pdfIframe.src = url; // The 'url' passed here is already HTML-escaped by Python for direct iframe use
            pdfViewer.classList.remove('hidden');
            closePdfBtn.classList.remove('hidden');
            fullscreenPdfBtn.classList.remove('hidden'); 
            pdfMenuToggleButton.classList.remove('hidden'); 
            pdfLocationBtn.classList.remove('hidden'); 

            sharePdfBtn.onclick = async () => {{ 
                const shareText = `Check out this PDF: ${{currentPdfName}}\\n${{currentPdfUrl}}`; // Use unescaped stored URLs
                if (navigator.share) {{
                    try {{
                        await navigator.share({{
                            title: `PDF: ${{currentPdfName}}`,
                            text: `Check out this PDF: ${{currentPdfName}}`,
                            url: currentPdfUrl // Use unescaped stored URL
                        }});
                        console.log('PDF shared successfully');
                    }} catch (error) {{
                        console.error('Error sharing PDF:', error);
                        copyToClipboard(shareText);
                    }}
                }} else {{
                    copyToClipboard(shareText);
                }}
                pdfDropdownMenu.classList.add('hidden');
            }};
            downloadPdfBtn.onclick = () => {{
                triggerPdfDownload();
                pdfDropdownMenu.classList.add('hidden');
            }};
        }}

        function triggerPdfDownload() {{
            if (currentPdfUrl) {{
                const link = document.createElement('a');
                link.href = currentPdfUrl; // Use the unescaped URL
                const suggestedFileName = (currentPdfName ? currentPdfName.replace(/[^\w\s.-]/g, '') : 'document') + '.pdf';
                link.download = suggestedFileName;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }}
        }}

        function togglePdfFullscreen() {{
            const pdfIframe = document.getElementById('pdf-iframe-viewer');
            if (pdfIframe.requestFullscreen) {{
                pdfIframe.requestFullscreen();
            }} else if (pdfIframe.mozRequestFullScreen) {{
                pdfIframe.mozRequestFullScreen();
            }} else if (pdfIframe.webkitRequestFullscreen) {{
                pdfIframe.webkitRequestFullscreen();
            }} else if (pdfIframe.msRequestFullscreen) {{
                pdfIframe.msRequestFullscreen();
            }}
        }}

        function findPdfLocation() {{
            if (!currentPdfUrl) return;
            console.log("Attempting to find PDF location for:", currentPdfUrl);

            returnToLists(true); // Switch to PDF tab and show lists

            const pdfList = document.querySelector('#pdfs .pdf-list');
            const links = pdfList.querySelectorAll('a[data-original-url]'); // Select links with data-original-url

            let foundLink = null;
            links.forEach(link => {{
                const linkOriginalUrl = link.getAttribute('data-original-url');
                console.log("Comparing current PDF URL:", currentPdfUrl, "with link URL:", linkOriginalUrl);
                if (linkOriginalUrl === currentPdfUrl) {{
                    foundLink = link;
                }}
            }});

            if (foundLink) {{
                document.querySelectorAll('.highlight-link').forEach(el => {{
                    el.classList.remove('highlight-link');
                    el.style.backgroundColor = '';
                    el.style.borderColor = '';
                }});

                foundLink.classList.add('highlight-link');
                foundLink.style.backgroundColor = 'rgba(59, 130, 246, 0.3)';
                foundLink.style.borderColor = '#3b82f6';

                foundLink.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                setTimeout(() => {{
                    foundLink.classList.remove('highlight-link');
                    foundLink.style.backgroundColor = '';
                    foundLink.style.borderColor = '';
                }}, 3000);
            }} else {{
                alert('Could not find the PDF link in the list.');
            }}
        }}

        function findVideoLocation() {{
            if (!currentVideoUrl) return;
            console.log("Attempting to find Video location for:", currentVideoUrl);

            returnToLists(false); // Switch to Video tab and show lists

            const videoList = document.querySelector('#videos .video-list');
            const links = videoList.querySelectorAll('a[data-original-url]'); // Select links with data-original-url

            let foundLink = null;
            links.forEach(link => {{
                const linkOriginalUrl = link.getAttribute('data-original-url');
                console.log("Comparing current Video URL:", currentVideoUrl, "with link URL:", linkOriginalUrl);
                if (linkOriginalUrl === currentVideoUrl) {{
                    foundLink = link;
                }}
            }});

            if (foundLink) {{
                document.querySelectorAll('.highlight-link').forEach(el => {{
                    el.classList.remove('highlight-link');
                    el.style.backgroundColor = '';
                    el.style.borderColor = '';
                }});

                foundLink.classList.add('highlight-link');
                foundLink.style.backgroundColor = 'rgba(59, 130, 246, 0.3)';
                foundLink.style.borderColor = '#3b82f6';

                foundLink.scrollIntoView({{ behavior: 'smooth', block: 'center' }});

                setTimeout(() => {{
                    foundLink.classList.remove('highlight-link');
                    foundLink.style.backgroundColor = '';
                    foundLink.style.borderColor = '';
                }}, 3000);
            }} else {{
                alert('Could not find the Video link in the list.');
            }}
        }}


        function returnToLists(keepPdfTabActive = false) {{
            const videoPlayerContainer = document.getElementById('player-container');
            const videoControls = document.getElementById('video-controls');
            const pdfViewer = document.getElementById('pdf-viewer-container');
            const pdfIframe = document.getElementById('pdf-iframe-viewer');
            const closePdfBtn = document.getElementById('close-pdf-btn');
            const fullscreenPdfBtn = document.getElementById('fullscreen-pdf-btn'); 
            const contentSections = document.querySelectorAll('.content'); 
            const tabControls = document.querySelector('.flex.flex-wrap.justify-center.mb-6.gap-2'); 
            const tabs = document.querySelectorAll('.tab'); 
            const pdfMenuToggleButton = document.getElementById('pdf-menu-toggle-btn'); 
            const pdfDropdownMenu = document.getElementById('pdf-dropdown-menu'); 
            const pdfLocationBtn = document.getElementById('pdf-location-btn'); 

            // Hide PDF viewer elements
            pdfViewer.classList.add('hidden');
            if (pdfIframe) {{ pdfIframe.src = ""; }} // Clear PDF iframe source
            closePdfBtn.classList.add('hidden'); 
            fullscreenPdfBtn.classList.add('hidden'); 
            pdfMenuToggleButton.classList.add('hidden'); 
            pdfDropdownMenu.classList.add('hidden'); 
            pdfLocationBtn.classList.add('hidden'); 
            currentPdfUrl = '';
            currentPdfName = '';

            // Hide video controls
            videoControls.classList.add('hidden');
            // Do NOT hide videoPlayerContainer here if we want to show lists.
            // It will be managed by showContent, or remain visible if it's the current player.

            // Show general UI elements
            tabControls.classList.remove('hidden');
            tabs.forEach(tab => {{
                tab.classList.remove('hidden');
            }});
            contentSections.forEach(section => section.classList.add('hidden')); // Hide all content sections initially

            if (keepPdfTabActive) {{
                showContent('pdfs', document.querySelector('.tab[data-tab="pdfs"]'));
            }} else {{
                showContent('videos', document.querySelector('.tab[data-tab="videos"]'));
            }}
        }}

        function showContent(tabName, clickedTab) {{
            const contents = document.querySelectorAll('.content');
            contents.forEach(content => {{
                content.classList.add('hidden');
                content.classList.remove('active-content');
            }});
            const tabs = document.querySelectorAll('.tab');
            tabs.forEach(tab => {{
                tab.classList.remove('active-tab');
            }});
            const selectedContent = document.getElementById(tabName);
            if (selectedContent) {{
                selectedContent.classList.remove('hidden');
                selectedContent.classList.add('active-content');
            }}

            if (clickedTab) {{
                clickedTab.classList.add('active-tab');
            }}
            filterLinks();
            
            // Manage player visibility when switching tabs
            const videoPlayerContainer = document.getElementById('player-container');
            const pdfViewerContainer = document.getElementById('pdf-viewer-container');
            const videoControls = document.getElementById('video-controls');

            if (tabName === 'videos') {{
                videoPlayerContainer.classList.remove('hidden');
                if (currentVideoUrl) {{ // Only show video controls if a video is loaded
                     videoControls.classList.remove('hidden'); // Initially hide, playVideo will show
                }} else {{
                    videoControls.classList.add('hidden');
                }}
                pdfViewerContainer.classList.add('hidden'); // Ensure PDF viewer is hidden
            }} else if (tabName === 'pdfs') {{
                pdfViewerContainer.classList.remove('hidden');
                videoPlayerContainer.classList.add('hidden'); // Ensure video player is hidden
                videoControls.classList.add('hidden'); // Hide video controls
            }} else {{ // Others tab
                videoPlayerContainer.classList.add('hidden');
                pdfViewerContainer.classList.add('hidden');
                videoControls.classList.add('hidden'); // Hide video controls
            }}
        }}

        function filterLinks() {{
            const searchInput = document.getElementById('searchInput');
            const filter = searchInput.value.toLowerCase();
            
            const activeContentDiv = document.querySelector('.content.active-content');
            if (!activeContentDiv) return;

            const links = activeContentDiv.querySelectorAll('a');

            links.forEach(link => {{
                let textContent = link.textContent || link.innerText;
                textContent = textContent.toLowerCase();

                if (textContent.indexOf(filter) > -1) {{
                    link.style.display = "";
                }} else {{
                    link.style.display = "none";
                }}
            }});
        }}
    </script>
</body>
</html>
    """
    return html_template

def convert_html_to_txt(html_file_path):
    extracted_data = []
    
    try:
        with open(html_file_path, "r", encoding='utf-8') as f:
            html_content = f.read()

        video_block_match = re.search(r'<div id="videos" class="content[^>]*?">(.*?)</div>', html_content, re.DOTALL)
        pdf_block_match = re.search(r'<div id="pdfs" class="content[^>]*?">(.*?)</div>', html_content, re.DOTALL)
        other_block_match = re.search(r'<div id="others" class="content[^>]*?">(.*?)</div>', html_content, re.DOTALL)

        video_link_pattern = r'<a[^>]*?(?:data-original-url="([^"]+)"|onclick="playVideo\(\'([^\']+)\'\)")?[^>]*?>(.*?)</a'
        pdf_link_pattern = r'<a[^>]*?(?:data-original-url="([^"]+)"|onclick="openPdf\(\'([^\']+)\'(?:,\s*\'[^\']+\')?\)")?[^>]*?>(.*?)</a'
        other_link_pattern = r'<a[^>]*?href="([^"]+)" target="_blank"[^>]*?>(.*?)</a'

        def clean_name_from_html(raw_html_content):
            clean_text = re.sub(r'<[^>]+>', '', raw_html_content).strip()
            return html.unescape(clean_text)

        if video_block_match:
            video_content = video_block_match.group(1)
            video_matches = re.findall(video_link_pattern, video_content, re.DOTALL)
            for match in video_matches:
                url = match[0] or match[1] # Prioritize data-original-url, then onclick URL
                raw_name = match[2]
                name = clean_name_from_html(raw_name)
                if url:
                    extracted_data.append(f"{name}: {html.unescape(url)}")

        if pdf_block_match:
            pdf_content = pdf_block_match.group(1)
            pdf_matches = re.findall(pdf_link_pattern, pdf_content, re.DOTALL)
            for match in pdf_matches:
                url = match[0] or match[1] # Prioritize data-original-url, then onclick URL
                raw_name = match[2]
                name = clean_name_from_html(raw_name)
                if url:
                    extracted_data.append(f"{name}: {html.unescape(url)}")

        if other_block_match:
            other_content = other_block_match.group(1)
            other_matches = re.findall(other_link_pattern, other_content, re.DOTALL)
            for url, raw_name in other_matches:
                name = clean_name_from_html(raw_name)
                extracted_data.append(f"{name}: {html.unescape(url)}")

    except Exception as e:
        print(f"Error converting HTML to TXT with regex: {e}")
        return None

    return "\n".join(extracted_data)

# --- Telegram Bot Handlers ---

@app.on_message(filters.command("start") & filters.private)
async def start(client: Client, message: Message):
    user_id = message.from_user.id
    is_authorized = (user_id == config["OWNER_ID"] or user_id in config["SUDO_USERS"])

    # Provide a fallback URL if config values are invalid/empty
    # Using 'about:blank' is a safe fallback that doesn't break URL buttons
    channel_link = config['YOUR_CHANNEL_LINK'] if config['YOUR_CHANNEL_LINK'].startswith(('http://', 'https://')) else 'https://t.me/telegram'
    contact_link = config['CONTACT_LINK'] if config['CONTACT_LINK'].startswith(('http://', 'https://')) else 'https://t.me/telegram'

    # --- Inline Keyboard (for administrative/external links) ---
    inline_buttons = [
        [InlineKeyboardButton("📞 Contact Us", url=contact_link)]
    ]
    
    if is_authorized:
        inline_buttons.insert(0, [InlineKeyboardButton("⚙️ Admin Settings", callback_data="admin_settings_menu")])
        inline_buttons.insert(1, [InlineKeyboardButton(f"📡 {config['YOUR_NAME_FOR_DISPLAY']}'s Channel", url=channel_link)])
    
    inline_keyboard = InlineKeyboardMarkup(inline_buttons)

    # --- Reply Keyboard (for common actions) ---
    reply_keyboard_buttons = [
        [KeyboardButton("📤 Generate HTML from TXT"), KeyboardButton("📥 Convert HTML to TXT")]
    ]
    # Add a "Help" button if more commands are needed
    if is_authorized:
        reply_keyboard_buttons.append([KeyboardButton("❓ Help")]) # For authorized users, provide context-specific help
    else:
        reply_keyboard_buttons.append([KeyboardButton("❔ Info")]) # For unauthorized, just general info
    
    reply_keyboard = ReplyKeyboardMarkup(
        reply_keyboard_buttons,
        resize_keyboard=True,
        one_time_keyboard=False # Keep the keyboard visible
    )

    if is_authorized:
        welcome_text = (
            "🎉 **Welcome to the HTML Link Generator Bot!** 🎉\n\n"
            "This bot helps you convert `.txt` files containing Name:URL pairs into beautiful, "
            "password-protected HTML pages, and also convert `.html` pages back to `.txt`.\n\n"
            "**How to use:**\n"
            "1.  **Generate HTML:** Tap `📤 Generate HTML from TXT` or just upload your `.txt` file.\n"
            "2.  **Convert to TXT:** Tap `📥 Convert HTML to TXT` or just upload your `.html` file.\n\n"
            "**Admin Panel:** Use the **'⚙️ Admin Settings'** button below to manage bot configurations (HTML credentials, display info, sudo users)."
        )
    else:
        welcome_text = (
            "👋 **Welcome to the HTML Link Generator Bot!**\n\n"
            "This bot helps convert `.txt` files (Name:URL) to beautiful, password-protected HTML pages, "
            "and `.html` files back to `.txt`.\n\n"
            "Please upload your `.txt` or `.html` file directly to the chat.\n\n"
            "If you're looking for more info or assistance, use the buttons below."
        )

    await message.reply_text(
        welcome_text,
        reply_markup=reply_keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    # Also send the inline keyboard separately if desired, or combine if it makes sense.
    # For admin settings, a separate inline keyboard is better.
    if is_authorized:
         await message.reply_text(
            "Quick access to admin settings:",
            reply_markup=inline_keyboard,
            parse_mode=ParseMode.MARKDOWN # Ensures proper rendering if any markdown is used
        )
    else:
        # For unauthorized users, just send the inline buttons with the contact link if desired
        await message.reply_text(
            "Reach out to us:",
            reply_markup=inline_keyboard,
            parse_mode=ParseMode.MARKDOWN
        )


# --- Handle Reply Keyboard Buttons ---
@app.on_message(filters.regex("📤 Generate HTML from TXT") & filters.private)
@authorized_users_only
async def reply_generate_html(client: Client, message: Message):
    await message.reply_text(
        "Alright! Please **upload your `.txt` file** containing links in `Name: URL` format. "
        "I will convert it into a password-protected HTML file for you.",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.regex("📥 Convert HTML to TXT") & filters.private)
@authorized_users_only
async def reply_convert_txt(client: Client, message: Message):
    await message.reply_text(
        "Okay! Please **upload your `.html` file**. "
        "I will extract the links and convert them back into a `.txt` file for you.",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.regex("❓ Help") & filters.private)
@authorized_users_only
async def reply_help_authorized(client: Client, message: Message):
    await message.reply_text(
        "Here are the commands you can use:\n\n"
        "**File Handling:**\n"
        "- Just **upload a `.txt` file** (Name:URL format) to generate HTML.\n"
        "- Just **upload a `.html` file** to convert it back to `.txt`.\n\n"
        "**Admin Commands:**\n"
        "- `/sethtmlusername <new_username>`: Set username for HTML access.\n"
        "- `/sethtmlpassword <new_password>`: Set password for HTML access.\n"
        "- `/setdisplayname <Your Name Here>`: Set your name displayed in HTML.\n"
        "- `/setchannellink <https://t.me/your_channel_link>`: Set channel link in HTML.\n"
        "- `/setcontactlink <https://t.me/your_contact_link>`: Set contact link.\n"
        "- `/addsudo <user_id>`: Add a user to the sudo list (Owner only).\n"
        "- `/removesudo <user_id>`: Remove a user from the sudo list (Owner only).\n"
        "- `/listsudo`: View current sudo users.\n\n"
        "You can always use `/start` to see the main menu again.",
        parse_mode=ParseMode.MARKDOWN
    )

@app.on_message(filters.regex("❔ Info") & filters.private)
async def reply_info_unauthorized(client: Client, message: Message):
    await message.reply_text(
        "This bot is designed to convert `.txt` files (Name:URL format) into "
        "password-protected HTML pages, and `.html` files back into `.txt`.\n\n"
        "If you are looking for specific functionality or support, please use the '📞 Contact Us' button.",
        parse_mode=ParseMode.MARKDOWN
    )


# --- Handle Document Uploads ---
@app.on_message(filters.document & filters.private)
@authorized_users_only # Apply the authorization decorator to document handling
async def handle_document(client: Client, message: Message):
    if not message.document:
        await message.reply_text("Please upload a `.txt` or `.html` file.")
        return

    file_name = message.document.file_name
    
    # Send a "processing" message
    processing_message = await message.reply_text(
        f"Processing your file: `{file_name}`... Please wait.",
        parse_mode=ParseMode.MARKDOWN
    )

    # Download the file
    downloaded_file_path = await message.download()

    try:
        if file_name.endswith(".txt"):
            # Handle TXT to HTML conversion
            with open(downloaded_file_path, "r", encoding='utf-8') as f:
                file_content = f.read()

            names_and_urls = extract_names_and_urls(file_content)
            if not names_and_urls:
                await processing_message.edit_text(
                    "❌ No valid `Name: URL` pairs found in your `.txt` file. "
                    "Please ensure each link is on a new line and in the format `Name: URL`."
                )
                return

            videos, pdfs, others = categorize_urls(names_and_urls)

            html_content = generate_html(file_name, videos, pdfs, others)
            html_file_name = file_name.replace(".txt", ".html")
            html_file_path = os.path.join(OUTPUT_HTML_FOLDER, html_file_name)

            os.makedirs(OUTPUT_HTML_FOLDER, exist_ok=True)
            with open(html_file_path, "w", encoding='utf-8') as f:
                f.write(html_content)

            await message.reply_document(
                document=html_file_path, 
                caption="✅ **Successfully Generated HTML!**\n\n"
                        "Your HTML file is ready. Please share it with your audience.",
                parse_mode=ParseMode.MARKDOWN
            )
            os.remove(html_file_path) # Clean up generated HTML file

        elif file_name.endswith(".html"):
            # Handle HTML to TXT conversion
            txt_content = convert_html_to_txt(downloaded_file_path)
            if txt_content:
                txt_file_name = file_name.replace(".html", ".txt")
                txt_file_path = os.path.join(OUTPUT_HTML_FOLDER, txt_file_name) # Temporarily store in output folder
                
                os.makedirs(OUTPUT_HTML_FOLDER, exist_ok=True)
                with open(txt_file_path, "w", encoding='utf-8') as f:
                    f.write(txt_content)
                
                await message.reply_document(
                    document=txt_file_path, 
                    caption="✅ **Successfully Converted HTML to TXT!**\n\n"
                            "Your extracted links are in the `.txt` file.",
                    parse_mode=ParseMode.MARKDOWN
                )
                os.remove(txt_file_path) # Clean up generated TXT file
            else:
                await processing_message.edit_text(
                    "❌ Failed to convert HTML to TXT. The HTML structure might be unexpected or invalid. "
                    "Ensure it's a file previously generated by this bot or follows a similar structure."
                )
        else:
            await processing_message.edit_text("🚫 Unsupported file type. Please upload a `.txt` or `.html` file.")
    except Exception as e:
        print(f"Error handling document: {e}")
        await processing_message.edit_text(f"❌ An error occurred while processing your file: `{e}`")
    finally:
        # Clean up the downloaded file after processing
        if os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)


# --- Callback Query Handlers (for Inline Keyboard buttons) ---
@app.on_callback_query(filters.regex("^admin_settings_menu$"))
@authorized_users_only
async def admin_settings_menu_callback(client: Client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 HTML Access Credentials", callback_data="edit_creds_button")],
        [InlineKeyboardButton("✍️ HTML Display Settings", callback_data="edit_html_display_button")],
        [InlineKeyboardButton("👥 Manage Sudo Users", callback_data="manage_sudo_button")],
        [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="start_menu")]
    ])
    await callback_query.message.edit_text(
        "**⚙️ Admin Settings Menu:**\n\n"
        "Choose an option to manage bot configurations:",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex("^edit_creds_button$"))
@authorized_users_only
async def edit_creds_callback(client: Client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Admin Settings", callback_data="admin_settings_menu")]
    ])
    await callback_query.message.edit_text(
        "**🔗 HTML Access Credentials:**\n\n"
        "To change the username and password for your generated HTML files, use:\n"
        "- `/sethtmlusername <new_username>`\n"
        "- `/sethtmlpassword <new_password>`\n\n"
        f"Current Username: `{config['HTML_FILE_USERNAME']}`\n"
        f"Current Password: `{config['HTML_FILE_PASSWORD']}`\n\n"
        "**Example:** `/sethtmlusername mysecretuser`",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex("^manage_sudo_button$"))
@authorized_users_only
async def manage_sudo_callback(client: Client, callback_query: CallbackQuery):
    sudo_list_str = "\n".join([f"- `{uid}`" for uid in config["SUDO_USERS"]]) if config["SUDO_USERS"] else "None"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Admin Settings", callback_data="admin_settings_menu")]
    ])
    await callback_query.message.edit_text(
        "**👥 Manage Sudo Users:**\n\n"
        "Sudo users can use most admin commands.\n"
        "**Note:** Only the bot owner can add/remove sudo users.\n\n"
        "Your OWNER_ID (The Main Admin): `{owner_id}`\n"
        "Current Sudo Users:\n{sudo_users}\n\n"
        "Use these commands:\n"
        "- `/addsudo <user_id>`\n"
        "- `/removesudo <user_id>`\n"
        "- `/listsudo`\n\n"
        "**Example:** `/addsudo 123456789`",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex("^edit_html_display_button$"))
@authorized_users_only
async def edit_html_display_callback(client: Client, callback_query: CallbackQuery):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Admin Settings", callback_data="admin_settings_menu")]
    ])
    # Validate URLs for display in the message
    display_channel_link = config['YOUR_CHANNEL_LINK'] if config['YOUR_CHANNEL_LINK'].startswith(('http://', 'https://')) else "Not set or invalid"
    display_contact_link = config['CONTACT_LINK'] if config['CONTACT_LINK'].startswith(('http://', 'https://')) else "Not set or invalid"

    await callback_query.message.edit_text(
        "**✍️ HTML Display Settings:**\n\n"
        "These settings control what is displayed on your generated HTML pages:\n"
        "- `/setdisplayname <Your Name Here>`: Sets the name shown as the author/creator.\n"
        "- `/setchannellink <https://t.me/your_channel>`: Sets the channel link below the name.\n"
        "- `/setcontactlink <https://t.me/your_contact>`: Sets the contact link for the 'Contact Us' button.\n\n"
        f"Current Display Name: `{config['YOUR_NAME_FOR_DISPLAY']}`\n"
        f"Current Channel Link: `{display_channel_link}`\n"
        f"Current Contact Link: `{display_contact_link}`\n\n"
        "**Example:** `/setdisplayname Engineer Babu`",
        reply_markup=keyboard,
        parse_mode=ParseMode.MARKDOWN
    )
    await callback_query.answer()

@app.on_callback_query(filters.regex("^start_menu$"))
@authorized_users_only
async def back_to_start_menu(client: Client, callback_query: CallbackQuery):
    # Re-trigger the start command logic to show main menu
    await callback_query.message.delete() # Delete the old message to clean up
    await start(client, callback_query.message) # Use the message object from callback_query
    await callback_query.answer()


# --- Direct Command Handlers ---

@app.on_message(filters.command("sethtmlusername") & filters.private)
@authorized_users_only
async def set_html_username(client: Client, message: Message):
    if len(message.command) > 1:
        new_username = message.command[1]
        config["HTML_FILE_USERNAME"] = new_username
        save_config_to_file()
        await message.reply_text(f"✅ HTML file username set to: `{new_username}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/sethtmlusername <new_username>`\n\n"
                                 "Current Username: `{}`".format(config['HTML_FILE_USERNAME']),
                                 parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("sethtmlpassword") & filters.private)
@authorized_users_only
async def set_html_password(client: Client, message: Message):
    if len(message.command) > 1:
        new_password = message.command[1]
        config["HTML_FILE_PASSWORD"] = new_password
        save_config_to_file()
        await message.reply_text(f"✅ HTML file password set to: `{new_password}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/sethtmlpassword <new_password>`\n\n"
                                 "Current Password: `{}`".format(config['HTML_FILE_PASSWORD']),
                                 parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setdisplayname") & filters.private)
@authorized_users_only
async def set_display_name(client: Client, message: Message):
    if len(message.command) > 1:
        new_name = " ".join(message.command[1:])
        config["YOUR_NAME_FOR_DISPLAY"] = new_name
        save_config_to_file()
        await message.reply_text(f"✅ Display name set to: `{new_name}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/setdisplayname <Your Name Here>`\n\n"
                                 "Current Display Name: `{}`".format(config['YOUR_NAME_FOR_DISPLAY']),
                                 parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setchannellink") & filters.private)
@authorized_users_only
async def set_channel_link(client: Client, message: Message):
    if len(message.command) > 1:
        new_link = message.command[1]
        if new_link.startswith("http://") or new_link.startswith("https://"):
            config["YOUR_CHANNEL_LINK"] = new_link
            save_config_to_file()
            await message.reply_text(f"✅ Channel link set to: `{new_link}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text("❌ Please provide a valid URL starting with `http://` or `https://`.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/setchannellink <https://t.me/your_channel_link>`\n\n"
                                 "Current Channel Link: `{}`".format(config['YOUR_CHANNEL_LINK'] or "Not set"),
                                 parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setcontactlink") & filters.private)
@authorized_users_only
async def set_contact_link(client: Client, message: Message):
    if len(message.command) > 1:
        new_link = message.command[1]
        if new_link.startswith("http://") or new_link.startswith("https://"):
            config["CONTACT_LINK"] = new_link
            save_config_to_file()
            await message.reply_text(f"✅ Contact link set to: `{new_link}`", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text("❌ Please provide a valid URL starting with `http://` or `https://`.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/setcontactlink <https://t.me/your_contact_channel_or_user>`\n\n"
                                 "Current Contact Link: `{}`".format(config['CONTACT_LINK'] or "Not set"),
                                 parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("addsudo") & filters.private)
@authorized_users_only # Only owner can add sudo
async def add_sudo(client: Client, message: Message):
    if message.from_user.id != config["OWNER_ID"]:
        await message.reply_text("❌ Only the bot owner can add sudo users.", parse_mode=ParseMode.MARKDOWN)
        return

    if len(message.command) > 1 and message.command[1].isdigit():
        user_id = int(message.command[1])
        if user_id == config["OWNER_ID"]:
            await message.reply_text(f"❌ User `{user_id}` is the owner and doesn't need to be added to sudo.", parse_mode=ParseMode.MARKDOWN)
            return
        if user_id not in config["SUDO_USERS"]:
            config["SUDO_USERS"].append(user_id)
            save_config_to_file()
            await message.reply_text(f"✅ User `{user_id}` added to sudo list.", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text(f"ℹ️ User `{user_id}` is already in the sudo list.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/addsudo <user_id>`\n\n"
                                 "Get user ID from @userinfobot or @GetMyID_bot.",
                                 parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("removesudo") & filters.private)
@authorized_users_only # Only owner can remove sudo
async def remove_sudo(client: Client, message: Message):
    if message.from_user.id != config["OWNER_ID"]:
        await message.reply_text("❌ Only the bot owner can remove sudo users.", parse_mode=ParseMode.MARKDOWN)
        return

    if len(message.command) > 1 and message.command[1].isdigit():
        user_id = int(message.command[1])
        if user_id == config["OWNER_ID"]:
            await message.reply_text(f"❌ You cannot remove the owner (`{user_id}`) from the sudo list.", parse_mode=ParseMode.MARKDOWN)
            return
        if user_id in config["SUDO_USERS"]:
            config["SUDO_USERS"].remove(user_id)
            save_config_to_file()
            await message.reply_text(f"✅ User `{user_id}` removed from sudo list.", parse_mode=ParseMode.MARKDOWN)
        else:
            await message.reply_text(f"ℹ️ User `{user_id}` is not in the sudo list.", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("Usage: `/removesudo <user_id>`", parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("listsudo") & filters.private)
@authorized_users_only
async def list_sudo(client: Client, message: Message):
    if config["SUDO_USERS"]:
        sudo_list_str = "\n".join([f"- `{uid}`" for uid in config["SUDO_USERS"]])
        await message.reply_text(f"**Current Sudo Users:**\n{sudo_list_str}", parse_mode=ParseMode.MARKDOWN)
    else:
        await message.reply_text("No sudo users currently configured.", parse_mode=ParseMode.MARKDOWN)

# Ensure the OUTPUT_HTML_FOLDER exists when the bot starts
os.makedirs(OUTPUT_HTML_FOLDER, exist_ok=True)

# Run the bot
app.run()
