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
#       BOT CONFIGURATION - EASY TO FILL
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
DEFAULT_HTML_USERNAME = os.getenv("HTML_FILE_USERNAME", "ITSGOLU")

# 6. DEFAULT HTML FILE PASSWORD (for generated HTML pages)
#    - Environment Variable: HTML_FILE_PASSWORD
#    - Default if not set: "pass"
DEFAULT_HTML_PASSWORD = os.getenv("HTML_FILE_PASSWORD", "ITSGOLU")

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
#      - Environment Variable: SUDO_USERS (comma-separated, e.g., "12345,67890")
#      - Default if not set: []
DEFAULT_SUDO_USERS = [7740514033]
sudo_users_env = os.getenv("SUDO_USERS")
if sudo_users_env:
    try:
        DEFAULT_SUDO_USERS = list(map(int, sudo_users_env.split(',')))
    except ValueError:
        print("Warning: SUDO_USERS environment variable contains non-integer values. Ignoring.")
        DEFAULT_SUDO_USERS = []


# =========================================================
#       DO NOT EDIT BELOW THIS LINE UNLESS YOU KNOW WHAT YOU ARE DOING!
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
    # Modified pdf_links to call openPdf in a new tab
    pdf_links = "".join(f'<a href="#" onclick="openPdf(\'{html.escape(url)}\'); return false;" data-original-url="{url}"><svg class="w-5 h-5 mr-3 text-blue-400" fill="currentColor" viewBox="0 0 20 20"><path fill-rule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.414L16.586 7A2 2 0 0117 8.414V16a2 2 0 01-2 2H5a2 2 0 01-2-2V4zm6 1a1 1 0 100 2h3a1 1 0 100-2h-3zm-3 8a1 1 0 100 2h6a1 1 0 100-2H7z" clip-rule="evenodd"></path></svg>{name}</a>' for name, url in pdfs)
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
                            'progressControl',
                            'fullscreenToggle'
                        ]
                    }}
                }});

                // Check for hash in URL and highlight link
                const hash = window.location.hash.substring(1);
                if (hash) {{
                    const targetLink = document.querySelector(`[data-original-url="${decodeURIComponent(hash)}"]`);
                    if (targetLink) {{
                        targetLink.classList.add('highlight-link');
                        targetLink.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        // Remove highlight after some time
                        setTimeout(() => {{
                            targetLink.classList.remove('highlight-link');
                        }}, 5000);
                    }}
                }}

            }} else {{
                errorMessageDiv.textContent = "Invalid username or password. Please try again.";
                errorMessageDiv.style.color = '#f87171'; // Tailwind red-400
                setTimeout(() => {{
                    errorMessageDiv.textContent = "";
                }}, 3000);
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

        const videoPlayer = videojs('engineer-babu-player');
        const iframePlayer = document.getElementById('iframe-player');
        const playerContainer = document.getElementById('player-container');
        const videoControls = document.getElementById('video-controls');
        // Removed PDF viewer related elements

        function playVideo(url) {{
            const videoPlayer = videojs('engineer-babu-player');
            const iframePlayer = document.getElementById('iframe-player');
            const playerContainer = document.getElementById('player-container');
            const videoControls = document.getElementById('video-controls');

            currentVideoUrl = htmlUnescape(url); // Store the unescaped URL

            videoPlayer.pause();
            videoPlayer.reset();
            iframePlayer.classList.add('hidden');
            videoPlayer.el().classList.add('hidden');
            videoControls.classList.add('hidden');

            if (url.includes("player.muftukmall.site") || url.includes("dragoapi.vercel.app") || url.includes("anonymouspwplayer-b99f57957198.herokuapp.com") || url.includes("khanglobalstudies.com/player") || url.includes("extractor.workers.dev/player")) {{
                // Use iframe for external player URLs
                iframePlayer.src = url;
                iframePlayer.classList.remove('hidden');
                playerContainer.style.paddingTop = '56.25%'; // 16:9 aspect ratio
                videoControls.classList.add('hidden'); // No controls for iframe
            }} else {{
                // Use video.js for direct video URLs
                videoPlayer.src({{ src: url, type: url.includes(".m3u8") ? "application/x-mpegURL" : "video/mp4" }});
                videoPlayer.load();
                videoPlayer.play();
                videoPlayer.el().classList.remove('hidden');
                playerContainer.style.paddingTop = '56.25%'; // 16:9 aspect ratio
                videoControls.classList.remove('hidden'); // Show controls for video.js player
            }}

            window.location.hash = encodeURIComponent(currentVideoUrl); // Update hash for direct video links

            // Hide PDF viewer if it was open
            // Removed code to hide PDF viewer container
        }}

        function openPdf(url) {{
            const unescapedUrl = htmlUnescape(url); // Get the original unescaped URL
            window.open(unescapedUrl, '_blank'); // Open in a new tab
            window.location.hash = encodeURIComponent(unescapedUrl); // Update hash
        }}
        
        function showContent(tabId, clickedTab) {{
            // Hide all content divs
            document.querySelectorAll('.content').forEach(div => {{
                div.classList.add('hidden');
                div.classList.remove('active-content');
            }});

            // Deactivate all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active-tab');
            }});

            // Show the selected content div
            document.getElementById(tabId).classList.remove('hidden');
            document.getElementById(tabId).classList.add('active-content');

            // Activate the clicked tab
            clickedTab.classList.add('active-tab');
        }}

        function filterLinks() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const activeContentId = document.querySelector('.content.active-content').id;
            const listDiv = document.querySelector(`#${activeContentId} .${activeContentId}-list`);
            const links = listDiv.getElementsByTagName('a');

            for (let i = 0; i < links.length; i++) {{
                const text = links[i].textContent || links[i].innerText;
                if (text.toLowerCase().indexOf(filter) > -1) {{
                    links[i].style.display = "";
                }} else {{
                    links[i].style.display = "none";
                }}
            }}
        }}

        function findVideoLocation() {{
            if (currentVideoUrl) {{
                const targetLink = document.querySelector(`[data-original-url="${encodeURIComponent(currentVideoUrl)}"]`);
                if (targetLink) {{
                    // Switch to video tab if not active
                    showContent('videos', document.querySelector('[data-tab="videos"]'));
                    
                    targetLink.classList.add('highlight-link');
                    targetLink.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    setTimeout(() => {{
                        targetLink.classList.remove('highlight-link');
                    }}, 5000); // Remove highlight after 5 seconds
                }} else {{
                    alert("Original video link not found in the list.");
                }}
            }} else {{
                alert("No video is currently playing to locate.");
            }}
        }}
        // Removed findPdfLocation function
        // Removed returnToLists function as PDF viewer is removed

    </script>
</body>
</html>
"""
    os.makedirs(OUTPUT_HTML_FOLDER, exist_ok=True)
    file_path = os.path.join(OUTPUT_HTML_FOLDER, file_name)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_template)
    return file_path

# --- Bot Commands (No changes needed here for UX/Config) ---

@app.on_message(filters.command("start") & filters.private)
async def start_command(client, message: Message):
    keyboard = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Generate HTML 📄")],
            [KeyboardButton("Bot Settings ⚙️")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    await message.reply_text(
        "👋 Welcome! I can help you generate HTML pages from your text files containing names and URLs.\n\n"
        "Send me a `.txt` file with your links in the format `Name: URL` to get started.\n\n"
        "Use the buttons below to navigate.",
        reply_markup=keyboard
    )

@app.on_message(filters.command("help") & filters.private)
async def help_command(client, message: Message):
    help_text = (
        "**Here's how I work:**\n\n"
        "1.  **Send me a `.txt` file:** The file should contain `Name: URL` on each line.\n"
        "    Example:\n"
        "    `Video 1: https://example.com/video1.mp4`\n"
        "    `Lecture Notes: https://example.com/notes.pdf`\n"
        "    `Other Link: https://example.com/resource`\n\n"
        "2.  I will process the file, categorize the links into Videos, PDFs, and Others, "
        "    and then generate an HTML file for you.\n\n"
        "3.  **Bot Settings (Admin/Sudo Only):**\n"
        "    -   `/settings`: View current bot settings.\n"
        "    -   `/setowner <user_id>`: Change owner ID.\n"
        "    -   `/setsudo <user_ids>`: Add/remove sudo users (comma-separated).\n"
        "    -   `/sethtmluser <username>`: Set HTML file username.\n"
        "    -   `/sethtmlpass <password>`: Set HTML file password.\n"
        "    -   `/setdisplayname <name>`: Set your display name for HTML.\n"
        "    -   `/setchannel <link>`: Set your Telegram channel link.\n"
        "    -   `/setcontact <link>`: Set your contact link.\n\n"
        "Remember to use the buttons or send your `.txt` file!"
    )
    await message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("settings") & filters.private)
@authorized_users_only
async def show_settings(client, message: Message):
    settings_text = (
        "**Current Bot Settings:**\n"
        f"**Owner ID:** `{config['OWNER_ID']}`\n"
        f"**Sudo Users:** `{', '.join(map(str, config['SUDO_USERS'])) if config['SUDO_USERS'] else 'None'}`\n"
        f"**HTML Username:** `{config['HTML_FILE_USERNAME']}`\n"
        f"**HTML Password:** `{config['HTML_FILE_PASSWORD']}`\n"
        f"**Display Name:** `{config['YOUR_NAME_FOR_DISPLAY']}`\n"
        f"**Channel Link:** `{config['YOUR_CHANNEL_LINK'] or 'Not Set'}`\n"
        f"**Contact Link:** `{config['CONTACT_LINK'] or 'Not Set'}`\n\n"
        "Use `/set<setting_name> <value>` to change them. (e.g., `/sethtmluser newuser`)"
    )
    await message.reply_text(settings_text, parse_mode=ParseMode.MARKDOWN)

@app.on_message(filters.command("setowner") & filters.private)
@authorized_users_only
async def set_owner_id(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/setowner <user_id>`")
        return
    try:
        new_owner_id = int(message.command[1])
        if new_owner_id <= 0:
            raise ValueError("User ID must be a positive integer.")
        config["OWNER_ID"] = new_owner_id
        save_config_to_file()
        await message.reply_text(f"Owner ID updated to `{new_owner_id}`.")
    except ValueError:
        await message.reply_text("Invalid User ID. Please provide a valid integer.")

@app.on_message(filters.command("setsudo") & filters.private)
@authorized_users_only
async def set_sudo_users(client, message: Message):
    if len(message.command) < 2:
        config["SUDO_USERS"] = []
        save_config_to_file()
        await message.reply_text("Sudo users list cleared.")
        return
    
    user_ids_str = message.command[1]
    try:
        new_sudo_users = []
        for uid_str in user_ids_str.split(','):
            uid = int(uid_str.strip())
            if uid <= 0:
                raise ValueError("User ID must be a positive integer.")
            new_sudo_users.append(uid)
        
        config["SUDO_USERS"] = list(set(new_sudo_users)) # Ensure unique IDs
        save_config_to_file()
        await message.reply_text(f"Sudo users updated to `{', '.join(map(str, config['SUDO_USERS']))}`.")
    except ValueError:
        await message.reply_text("Invalid User ID(s). Please provide comma-separated valid integers.")

@app.on_message(filters.command("sethtmluser") & filters.private)
@authorized_users_only
async def set_html_username(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/sethtmluser <username>`")
        return
    new_username = message.text.split(None, 1)[1].strip()
    config["HTML_FILE_USERNAME"] = new_username
    save_config_to_file()
    await message.reply_text(f"HTML file username updated to `{new_username}`.")

@app.on_message(filters.command("sethtmlpass") & filters.private)
@authorized_users_only
async def set_html_password(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/sethtmlpass <password>`")
        return
    new_password = message.text.split(None, 1)[1].strip()
    config["HTML_FILE_PASSWORD"] = new_password
    save_config_to_file()
    await message.reply_text(f"HTML file password updated to `{new_password}`.")

@app.on_message(filters.command("setdisplayname") & filters.private)
@authorized_users_only
async def set_display_name(client, message: Message):
    if len(message.command) < 2:
        await message.reply_text("Usage: `/setdisplayname <name>`")
        return
    new_name = message.text.split(None, 1)[1].strip()
    config["YOUR_NAME_FOR_DISPLAY"] = new_name
    save_config_to_file()
    await message.reply_text(f"Display name updated to `{new_name}`.")

@app.on_message(filters.command("setchannel") & filters.private)
@authorized_users_only
async def set_channel_link(client, message: Message):
    if len(message.command) < 2:
        config["YOUR_CHANNEL_LINK"] = ""
        save_config_to_file()
        await message.reply_text("Channel link cleared. Using generic link if not set.")
        return
    
    new_link = message.text.split(None, 1)[1].strip()
    if not (new_link.startswith("http://") or new_link.startswith("https://")):
        await message.reply_text("Invalid URL. Please provide a link starting with `http://` or `https://`.")
        return

    config["YOUR_CHANNEL_LINK"] = new_link
    save_config_to_file()
    await message.reply_text(f"Channel link updated to `{new_link}`.")

@app.on_message(filters.command("setcontact") & filters.private)
@authorized_users_only
async def set_contact_link(client, message: Message):
    if len(message.command) < 2:
        config["CONTACT_LINK"] = ""
        save_config_to_file()
        await message.reply_text("Contact link cleared. Using generic link if not set.")
        return
    
    new_link = message.text.split(None, 1)[1].strip()
    if not (new_link.startswith("http://") or new_link.startswith("https://")):
        await message.reply_text("Invalid URL. Please provide a link starting with `http://` or `https://`.")
        return

    config["CONTACT_LINK"] = new_link
    save_config_to_file()
    await message.reply_text(f"Contact link updated to `{new_link}`.")

@app.on_message(filters.regex("Generate HTML 📄") & filters.private)
async def generate_html_button(client, message: Message):
    await message.reply_text(
        "Please send me a `.txt` file containing the names and URLs."
    )

@app.on_message(filters.regex("Bot Settings ⚙️") & filters.private)
@authorized_users_only
async def bot_settings_button(client, message: Message):
    await show_settings(client, message)

@app.on_message(filters.document & filters.private)
async def handle_document(client, message: Message):
    if message.document and message.document.file_name.endswith(".txt"):
        try:
            temp_file_path = await message.download()
            with open(temp_file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            data = extract_names_and_urls(file_content)
            if not data:
                await message.reply_text(
                    "The `.txt` file is empty or does not contain data in the format `Name: URL`."
                )
                os.remove(temp_file_path)
                return

            videos, pdfs, others = categorize_urls(data)

            output_file_name = f"{os.path.splitext(message.document.file_name)[0]}.html"
            html_file_path = generate_html(output_file_name, videos, pdfs, others)

            await message.reply_document(
                document=html_file_path,
                caption=f"Here is your generated HTML file: `{output_file_name}`"
            )
            os.remove(temp_file_path)
            os.remove(html_file_path) # Clean up generated HTML file
        except Exception as e:
            await message.reply_text(f"An error occurred: `{e}`")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    else:
        await message.reply_text(
            "Please send a `.txt` file. Other file types are not supported for HTML generation."
        )

print("Bot is starting...")
app.run()
