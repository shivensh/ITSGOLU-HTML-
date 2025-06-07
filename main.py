import os
import requests
import subprocess
import re # Import regex module
from urllib.parse import urlparse # Import urlparse for filename extraction
from pyrogram import Client, filters
from pyrogram.types import Message

# Replace with your API ID, API Hash, and Bot Token
API_ID = "22593658"
API_HASH = "511d0fd8542ada4c0aba4e47bd0892ee"
BOT_TOKEN = "7775228959:AAFOC1UXl5X4cKGpIr3i1Q2eeCHJjkpcM-Q"

# Telegram channel where files will be forwarded
CHANNEL_USERNAME = "https://t.me/Purushottamjangid" # Replace with your channel username

# --- HTML File Username and Password Configuration ---
HTML_FILE_USERNAME = "CERAMIC"  # <--- SET YOUR DESIRED USERNAME HERE
HTML_FILE_PASSWORD = "ITSGOLU"  # <--- SET YOUR DESIRED PASSWORD HERE
# --- END HTML File Username and Password ---

# --- NEW: Output Folder Configuration ---
OUTPUT_HTML_FOLDER = "generated_html" # Define the folder name for generated HTML files
# --- END NEW ---

# Initialize Pyrogram Client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Helper function to get a clean filename from a URL for download attribute
def get_filename_from_url(url, default_name="file"):
    """
    URL से एक स्वच्छ फ़ाइलनाम निकालता है, क्वेरी पैरामीटर और फ़्रैगमेंट को हटाता है।
    यदि कोई उपयुक्त फ़ाइलनाम नहीं मिलता है तो एक डिफ़ॉल्ट नाम प्रदान करता है, और यदि
    URL से पहचानने योग्य हो तो सही एक्सटेंशन का अनुमान लगाने का प्रयास करता है।
    """
    parsed_url = urlparse(url)
    path = parsed_url.path
    filename = os.path.basename(path)
    
    if filename:
        # पहले क्वेरी पैरामीटर और फ़्रैगमेंट हटाएँ
        clean_filename = filename.split('?')[0].split('#')[0]
        
        # यदि क्लीन किए गए फ़ाइलनाम में पहले से ही एक्सटेंशन है, तो उसका उपयोग करें
        if '.' in clean_filename:
            return clean_filename
        
        # यदि कोई एक्सटेंशन नहीं मिलता और URL से अनुमान नहीं लगाया जाता है तो जेनेरिक फ़ॉलबैक
        if '.mp4' in url:
            return f"{clean_filename}.mp4"
        elif '.m3u8' in url:
            return f"{clean_filename}.m3u8" # मैनिफ़ेस्ट के लिए स्पष्ट रूप से .m3u8 सुझाएँ
        elif 'pdf' in url:
            return f"{clean_filename}.pdf"
        elif '.mpd' in url: # मैनिफ़ेस्ट के लिए .mpd सुझाएँ
            return f"{clean_filename}.mpd"
        # अन्य सामान्य वीडियो प्रकार यदि आवश्यक हो तो जोड़ें
        elif '.webm' in url:
            return f"{clean_filename}.webm"
        elif '.avi' in url:
            return f"{clean_filename}.avi"
        elif '.mov' in url:
            return f"{clean_filename}.mov"
        
        return f"{clean_filename}.file" # यदि कोई एक्सटेंशन नहीं मिलता और अनुमान नहीं लगाया जाता है तो जेनेरिक फ़ॉलबैक

    return f"{default_name}.file" # यदि पथ में कोई फ़ाइलनाम नहीं है तो फ़ॉलबैक


# Function to extract names and URLs from the text file (no subject support)
def extract_names_and_urls(file_content):
    """
    प्रदान की गई टेक्स्ट फ़ाइल सामग्री से नाम और URL निकालता है।
    प्रत्येक पंक्ति 'Name: URL' प्रारूप में होने की उम्मीद है।
    """
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        line = line.strip()
        if not line: # खाली लाइनों को छोड़ दें
            continue
        if ":" in line:
            name, url = line.split(":", 1)
            data.append((name.strip(), url.strip()))
    return data

# Function to categorize URLs
def categorize_urls(urls):
    """
    दी गई (नाम, URL) टुपल्स की सूची को URL में पूर्वनिर्धारित पैटर्न के आधार पर
    वीडियो, PDF और अन्य में वर्गीकृत करता है।
    """
    videos = []
    pdfs = []
    others = []

    for name, url in urls:
        new_url = url
        # वीडियो निष्कर्षण के लिए विशिष्ट classplusapp.com या testbook URLs की जाँच करें
        if "media-cdn.classplusapp.com/" in url or "cpvod.testbook" in url:
            new_url = f"https://api.extractor.workers.dev/player?url={url}"
            videos.append((name, new_url))

        # वीडियो निष्कर्षण के लिए अन्य classplusapp.com विविधताओं की जाँच करें
        elif "media-cdn.classplusapp.com/alisg-cdn-a.classplusapp.com/" in url or \
             "media-cdn.classplusapp.com/1681/" in url or \
             "media-cdn.classplusapp.com/tencent/" in url:
            new_url = f"https://dragoapi.vercel.app/video/{url}"
            videos.append((name, new_url))

        # akamaized.net या cdn77.org URLs की जाँच करें
        elif "akamaized.net/" in url or "1942403233.rsc.cdn77.org/" in url:
            new_url = f"https://www.khanglobalstudies.com/player?src={url}"
            videos.append((name, new_url))

        # .mpd (MPEG-DASH) वीडियो URLs की जाँच करें
        elif "/master.mpd" in url:
            vid_id = url.split("/")[-2]
            new_url = f"https://player.muftukmall.site/?id={vid_id}"
            videos.append((name, new_url))

        # .zip फाइलों की जाँच करें (संभावित रूप से वीडियो या अन्य मीडिया युक्त)
        elif ".zip" in url:
            new_url = f"https://video.pablocoder.eu.org/appx-zip?url={url}"
            videos.append((name, new_url))

        # cloudfront.net URLs की जाँच करें (एक टोकन प्लेसहोल्डर की आवश्यकता है)
        elif "d1d34p8vz63oiq.cloudfront.net/" in url:
            # NOTE: 'your_working_token' एक प्लेसहोल्डर है। इस URL को एक वैध टोकन की आवश्यकता है।
            new_url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={{your_working_token}}"
            videos.append((name, new_url))

        # YouTube एम्बेड URLs की जाँच करें
        elif "youtube.com/embed" in url:
            yt_id = url.split("/")[-1]
            new_url = f"https://www.youtube.com/watch?v={yt_id}"
            videos.append((name, new_url))

        # .m3u8 (HLS) या .mp4 वीडियो प्रारूपों की जाँच करें
        elif ".m3u8" in url or ".mp4" in url:
            videos.append((name, url))
        # PDF फाइलों की जाँच करें
        elif "pdf" in url:
            pdfs.append((name, url))
        # अन्य सभी URLs
        else:
            others.append((name, url))

    return videos, pdfs, others

# Function to generate HTML file with Video.js player, theme toggle, and simplified tabs
def generate_html(file_name, videos, pdfs, others):
    """
    एक वीडियो प्लेयर, वर्गीकृत लिंक (कोई विषय नहीं),
    एक थीम टॉगल बटन, और वीडियो, PDF और अन्य के लिए टैब के साथ एक पूर्ण HTML फ़ाइल उत्पन्न करता है।
    """
    file_name_without_extension = os.path.splitext(file_name)[0]

    # वीडियो, PDF और अन्य लिंक के लिए Font Awesome आइकनों के साथ HTML उत्पन्न करें
    # प्रत्येक प्रविष्टि में अब अलग-अलग प्ले/व्यू और डाउनलोड क्रियाएँ शामिल हैं
    video_links_html = ""
    for name, url in videos:
        download_filename = get_filename_from_url(url, name)
        # In this 3:39 PM version, downloadFileDirectly function is NOT used in HTML
        # Downloads will open in new tab or download directly depending on browser.
        video_links_html += f'''
            <div class="flex flex-col sm:flex-row items-center justify-between p-3 bg-gray-200 dark:bg-gray-700 rounded-lg shadow-sm mb-2">
                <span class="flex items-center text-gray-800 dark:text-gray-100 font-medium text-sm sm:text-base text-center sm:text-left mb-2 sm:mb-0 flex-grow break-words pr-2">
                    <i class="fas fa-video w-5 h-5 mr-3 text-red-500 dark:text-red-400 flex-shrink-0"></i>
                    {name}
                </span>
                <div class="flex-shrink-0 flex space-x-2">
                    <button onclick="playVideo('{url}')" class="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full text-sm w-8 h-8 flex items-center justify-center" title="Play Video">
                        <i class="fas fa-play"></i>
                    </button>
                    <a href="{url}" target="_blank" download="{download_filename}" class="bg-green-600 hover:bg-green-700 text-white p-2 rounded-full text-sm w-8 h-8 flex items-center justify-center" title="Download">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
            </div>
        '''

    pdf_links_html = ""
    for name, url in pdfs:
        download_filename = get_filename_from_url(url, name)
        pdf_links_html += f'''
            <div class="flex flex-col sm:flex-row items-center justify-between p-3 bg-gray-200 dark:bg-gray-700 rounded-lg shadow-sm mb-2">
                <span class="flex items-center text-gray-800 dark:text-gray-100 font-medium text-sm sm:text-base text-center sm:text-left mb-2 sm:mb-0 flex-grow break-words pr-2">
                    <i class="fas fa-file-pdf w-5 h-5 mr-3 text-blue-500 dark:text-blue-400 flex-shrink-0"></i>
                    {name}
                </span>
                <div class="flex-shrink-0 flex space-x-2">
                    <a href="{url}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full text-sm w-8 h-8 flex items-center justify-center" title="View PDF">
                        <i class="fas fa-eye"></i>
                    </a>
                    <a href="{url}" target="_blank" download="{download_filename}" class="bg-green-600 hover:bg-green-700 text-white p-2 rounded-full text-sm w-8 h-8 flex items-center justify-center" title="Download">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
            </div>
        '''
    
    other_links_html = ""
    for name, url in others:
        download_filename = get_filename_from_url(url, name)
        other_links_html += f'''
            <div class="flex flex-col sm:flex-row items-center justify-between p-3 bg-gray-200 dark:bg-gray-700 rounded-lg shadow-sm mb-2">
                <span class="flex items-center text-gray-800 dark:text-gray-100 font-medium text-sm sm:text-base text-center sm:text-left mb-2 sm:mb-0 flex-grow break-words pr-2">
                    <i class="fas fa-link w-5 h-5 mr-3 text-green-500 dark:text-green-400 flex-shrink-0"></i>
                    {name}
                </span>
                <div class="flex-shrink-0 flex space-x-2">
                    <a href="{url}" target="_blank" class="bg-blue-600 hover:bg-blue-700 text-white p-2 rounded-full text-sm w-8 h-8 flex items-center justify-center" title="Open Link">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                    <a href="{url}" target="_blank" download="{download_filename}" class="bg-green-600 hover:bg-green-700 text-white p-2 rounded-full text-sm w-8 h-8 flex items-center justify-center" title="Download">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
            </div>
        '''

    html_template = f'''
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
        /* Custom styles for Video.js or specific overrides if needed */
        .video-js {{
            width: 100% !important;
            height: auto !important;
        }}
        /* Ensure Inter font is applied globally */
        body {{
            font-family: 'Inter', sans-serif;
            transition: background-color 0.3s ease, color 0.3s ease; /* Smooth transition for theme change */
        }}
        /* Active states for tabs */
        .active-tab {{
            background-color: #3b82f6; /* blue-500 */
            color: white;
            box-shadow: 0 4px 10px rgba(59, 130, 246, 0.4);
        }}
        .active-content {{
            display: block;
        }}
        /* Styling for the list items with icons */
        .video-list > div, .pdf-list > div, .other-list > div {{
            /* Common styling for the div containing name and buttons */
            margin-bottom: 8px; /* consistent spacing */
        }}
        .video-list a, .pdf-list a, .other-list a {{
            text-decoration: none; /* remove underline from links */
        }}
        /* Theme button specific styles */
        #theme-toggle {{
            background-color: #f3f4f6; /* Light theme button background */
            color: #1f2937; /* Light theme button icon color */
            border-radius: 9999px; /* Full rounded */
            padding: 0.5rem;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            z-index: 10;
        }}

        html.dark #theme-toggle {{
            background-color: #374151; /* Dark theme button background */
            color: #93c5fd; /* Dark theme button icon color */
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        }}

        #theme-toggle:hover {{
            transform: scale(1.1);
        }}

        /* Hamburger button styles */
        #hamburger-button {{
            background-color: #f3f4f6; /* Light theme button background */
            color: #1f2937; /* Light theme button icon color */
            border-radius: 9999px; /* Full rounded */
            padding: 0.5rem;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            z-index: 10;
        }}

        html.dark #hamburger-button {{
            background-color: #374151; /* Dark theme button background */
            color: #93c5fd; /* Dark theme button icon color */
            box-shadow: 0 2px 5px rgba(0,0,0,0.5);
        }}

        #hamburger-button:hover {{
            transform: scale(1.1);
        }}

        /* Sidebar menu transition */
        #sidebar-menu.open {{
            transform: translateX(0);
        }}

        /* Loading Spinner */
        .loader {{
            border: 4px solid #f3f3f3; /* Light grey */
            border-top: 4px solid #3b82f6; /* Blue */
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
        }}

        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
    </style>
</head>
<body class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100 min-h-screen flex flex-col items-center justify-center p-4">

    <div id="password-prompt" class="bg-gray-100 dark:bg-gray-800 p-8 rounded-lg shadow-xl max-w-md w-full text-center">
        <h2 class="text-3xl font-bold text-blue-600 dark:text-blue-500 mb-6">Access Required</h2>
        <input type="text" id="username-input" placeholder="Enter Username" required
               class="w-full p-3 mb-4 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
        <input type="password" id="password-input" placeholder="Enter Password" required
               class="w-full p-3 mb-6 bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100 border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
        <button onclick="checkPassword()"
                class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg transition duration-300 ease-in-out transform hover:scale-105 shadow-lg">
            Access Content
        </button>
        <div class="error-message text-red-600 dark:text-red-400 mt-4 font-semibold"></div>
    </div>

    <div id="protectedContent" class="hidden w-full max-w-4xl mx-auto bg-gray-100 dark:bg-gray-800 rounded-lg shadow-xl p-6 md:p-8 mt-6 relative">
        <!-- Theme Toggle Button -->
        <button id="theme-toggle" class="absolute top-4 right-4">
            <i class="fas fa-moon text-lg"></i> <!-- Default to moon icon for light mode -->
        </button>

        <!-- Hamburger Menu Button (visible on small screens) -->
        <button id="hamburger-button" class="absolute top-4 left-4 p-2 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 block md:hidden transition-all duration-300 hover:scale-110 shadow-md">
            <i class="fas fa-bars text-lg"></i>
        </button>

        <!-- Off-canvas Menu (Sidebar) -->
        <div id="sidebar-menu" class="fixed top-0 left-0 h-full w-64 bg-gray-100 dark:bg-gray-800 p-6 z-50 transform -translate-x-full transition-transform duration-300 ease-in-out shadow-lg">
            <button id="close-sidebar-button" class="absolute top-4 right-4 p-2 rounded-full bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 transition-all duration-300 hover:scale-110">
                <i class="fas fa-times text-lg"></i>
            </button>
            <h3 class="text-xl font-bold text-blue-600 dark:text-blue-400 mb-6 mt-12">Navigation</h3>
            <nav>
                <ul class="space-y-4">
                    <li><a href="#" onclick="showContent('videos', document.querySelector('.tab[data-tab=\\'videos\\']')); closeHamburgerMenu();" class="block p-3 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200 flex items-center"><i class="fas fa-video w-5 h-5 mr-3 text-red-500 dark:text-red-400"></i> Videos</a></li>
                    <li><a href="#" onclick="showContent('pdfs', document.querySelector('.tab[data-tab=\\'pdfs\\']')); closeHamburgerMenu();" class="block p-3 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200 flex items-center"><i class="fas fa-file-pdf w-5 h-5 mr-3 text-blue-500 dark:text-blue-400"></i> PDFs</a></li>
                    <li><a href="#" onclick="showContent('others', document.querySelector('.tab[data-tab=\\'others\\']')); closeHamburgerMenu();" class="block p-3 rounded-md text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors duration-200 flex items-center"><i class="fas fa-external-link-alt w-5 h-5 mr-3 text-green-500 dark:text-green-400"></i> Others</a></li>
                </ul>
            </nav>
        </div>

        <!-- Overlay for Sidebar -->
        <div id="sidebar-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-40 hidden" onclick="closeHamburgerMenu()"></div>

        <div class="bg-gray-200 dark:bg-gray-900 text-gray-900 dark:text-white p-4 rounded-t-lg text-center mb-6">
            <h1 class="text-2xl md:text-3xl font-extrabold">{file_name_without_extension}</h1>
            <p class="text-sm md:text-base text-gray-600 dark:text-gray-400 mt-2">
               <a href="https://t.me/+xKJ02aVap_4xZDk1" target="_blank" class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold transition-colors duration-200">पुरुषोत्तम जांगिड़™</a>
            </p>
        </div>

        <div id="video-player" class="mb-8 bg-gray-200 dark:bg-black rounded-lg overflow-hidden relative">
            <div id="player-status" class="absolute inset-0 flex items-center justify-center bg-gray-800 bg-opacity-75 text-white z-20 hidden">
                <div class="loader mr-3 hidden"></div> <!-- Spinner -->
                <span id="status-message"></span>
            </div>
            <video id="engineer-babu-player" class="video-js vjs-default-skin w-full h-auto" controls preload="auto">
                <p class="vjs-no-js text-gray-900 dark:text-white p-4">
                    To view this video please enable JavaScript, and consider upgrading to a web browser that
                    <a href="https://videojs.com/html5-video-support/" target="_blank" class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300">supports HTML5 video</a>
                </p>
            </video>
        </div>

        <div class="hidden md:flex flex-wrap justify-center mb-6 gap-2">
            <div class="tab flex-1 min-w-[100px] text-center py-3 px-4 bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-md cursor-pointer transition-all duration-300 hover:bg-gray-400 dark:hover:bg-gray-600 active-tab"
                 data-tab="videos" onclick="showContent('videos', this)">Videos</div>
            <div class="tab flex-1 min-w-[100px] text-center py-3 px-4 bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-md cursor-pointer transition-all duration-300 hover:bg-gray-400 dark:hover:bg-gray-600"
                 data-tab="pdfs" onclick="showContent('pdfs', this)">PDFs</div>
            <div class="tab flex-1 min-w-[100px] text-center py-3 px-4 bg-gray-300 dark:bg-gray-700 text-gray-700 dark:text-gray-300 font-semibold rounded-md cursor-pointer transition-all duration-300 hover:bg-gray-400 dark:hover:bg-gray-600"
                 data-tab="others" onclick="showContent('others', this)">Others</div>
        </div>

        <div id="videos" class="content active-content bg-gray-200 dark:bg-gray-700 p-6 rounded-lg shadow-inner">
            <h2 class="text-xl font-bold text-blue-600 dark:text-blue-400 mb-4 border-b border-gray-300 dark:border-gray-600 pb-2">All Video Lectures</h2>
            <div class="video-list space-y-2">
                {video_links_html}
            </div>
        </div>

        <div id="pdfs" class="content hidden bg-gray-200 dark:bg-gray-700 p-6 rounded-lg shadow-inner">
            <h2 class="text-xl font-bold text-blue-600 dark:text-blue-400 mb-4 border-b border-gray-300 dark:border-gray-600 pb-2">All PDFs</h2>
            <div class="pdf-list space-y-2">
                {pdf_links_html}
            </div>
        </div>

        <div id="others" class="content hidden bg-gray-200 dark:bg-gray-700 p-6 rounded-lg shadow-inner">
            <h2 class="text-xl font-bold text-blue-600 dark:text-blue-400 mb-4 border-b border-gray-300 dark:border-gray-600 pb-2">Other Resources</h2>
            <div class="other-list space-y-2">
                {other_links_html}
            </div>
        </div>

        <div class="text-center text-gray-600 dark:text-gray-400 text-sm mt-8 pt-4 border-t border-gray-300 dark:border-gray-700">
            <a href="https://t.me/+xKJ02aVap_4xZDk1" target="_blank" class="text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 font-semibold transition-colors duration-200">पुरुषोत्तम जांगिड़™</a>
        </div>
    </div>

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script>
        // --- HTML Username & Password Logic ---
        const HTML_USERNAME = "{HTML_FILE_USERNAME}";
        const HTML_PASSWORD = "{HTML_FILE_PASSWORD}";
        const protectedContent = document.getElementById('protectedContent');
        const passwordPrompt = document.getElementById('password-prompt');
        const errorMessageDiv = passwordPrompt.querySelector('.error-message');

        function checkPassword() {{
            const enteredUsername = document.getElementById('username-input').value;
            const enteredPassword = document.getElementById('password-input').value;

            if (enteredUsername === HTML_USERNAME && enteredPassword === HTML_PASSWORD) {{
                passwordPrompt.style.display = 'none'; // Hide password prompt
                protectedContent.classList.remove('hidden'); // Show content
                protectedContent.classList.add('flex', 'flex-col'); // Add flex for proper layout

                // Initialize Video.js player
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
                            'progressControl',
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

                // Add error handling for the player
                player.on('error', function() {{
                    const error = player.error();
                    let message = "Could not load video. ";
                    if (error) {{
                        if (error.code === 4) {{ // MEDIA_ERR_SRC_NOT_SUPPORTED
                            message += "The video format might not be supported, or the external extractor service failed to process the link. Try downloading the file.";
                        }} else if (error.code === 2) {{ // MEDIA_ERR_NETWORK
                            message += "Network error: Please check your internet connection. If the issue persists, the video source might be unavailable.";
                        }} else {{
                            message += `An error occurred (Code: ${{error.code}}). Please try again or download the video.`;
                        }}
                    }} else {{
                        message += "An unknown error occurred. Please try again or download the video.";
                    }}
                    showPlayerStatus(message, false);
                    console.error("Video.js Player Error:", error);
                }});

                player.on('loadeddata', function() {{
                    hidePlayerStatus(); // Hide status when video data is loaded and ready to play
                }});
                
                showContent('videos', document.querySelector('.tab[data-tab="videos"]')); // Show the initial video tab
            }} else {{
                errorMessageDiv.textContent = "Incorrect username or password. Access denied.";
            }}
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            passwordPrompt.style.display = 'block';
            applyTheme(); // Apply theme when the page loads
        }});
        // --- END HTML Username & Password ---

        // --- Theme Toggle Logic ---
        const themeToggleBtn = document.getElementById('theme-toggle');
        const htmlElement = document.documentElement; // This is the <html> tag

        function applyTheme() {{
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {{
                htmlElement.classList.add('dark');
                themeToggleBtn.innerHTML = '<i class="fas fa-sun text-lg"></i>'; // Show sun icon for dark mode
            }} else {{
                htmlElement.classList.remove('dark');
                themeToggleBtn.innerHTML = '<i class="fas fa-moon text-lg"></i>'; // Show moon icon for light mode
            }}
        }}

        function toggleTheme() {{
            if (htmlElement.classList.contains('dark')) {{
                htmlElement.classList.remove('dark');
                localStorage.setItem('theme', 'light');
                themeToggleBtn.innerHTML = '<i class="fas fa-moon text-lg"></i>';
            }} else {{
                htmlElement.classList.add('dark');
                localStorage.setItem('theme', 'dark');
                themeToggleBtn.innerHTML = '<i class="fas fa-sun text-lg"></i>';
            }}
        }}

        themeToggleBtn.addEventListener('click', toggleTheme);

        // --- END Theme Toggle Logic ---

        // --- Hamburger Menu Logic ---
        const hamburgerButton = document.getElementById('hamburger-button');
        const closeSidebarButton = document.getElementById('close-sidebar-button');
        const sidebarMenu = document.getElementById('sidebar-menu');
        const sidebarOverlay = document.getElementById('sidebar-overlay');

        function openHamburgerMenu() {{
            sidebarMenu.classList.remove('-translate-x-full');
            sidebarMenu.classList.add('open');
            sidebarOverlay.classList.remove('hidden');
            document.body.classList.add('overflow-hidden'); // Prevent scrolling
        }}

        function closeHamburgerMenu() {{
            sidebarMenu.classList.add('-translate-x-full');
            sidebarMenu.classList.remove('open');
            sidebarOverlay.classList.add('hidden');
            document.body.classList.remove('overflow-hidden');
        }}

        hamburgerButton.addEventListener('click', openHamburgerMenu);
        closeSidebarButton.addEventListener('click', closeHamburgerMenu);
        sidebarOverlay.addEventListener('click', closeHamburgerMenu);
        // --- END Hamburger Menu Logic ---

        // --- Player Status/Loading Logic ---
        const playerStatusDiv = document.getElementById('player-status');
        const statusMessageSpan = document.getElementById('status-message');
        const loaderSpinner = playerStatusDiv.querySelector('.loader');

        function showPlayerStatus(message, showSpinner = true) {{
            statusMessageSpan.textContent = message;
            playerStatusDiv.classList.remove('hidden');
            if (showSpinner) {{
                loaderSpinner.classList.remove('hidden');
            }} else {{
                loaderSpinner.classList.add('hidden');
            }}
        }}

        function hidePlayerStatus() {{
            playerStatusDiv.classList.add('hidden');
            loaderSpinner.classList.add('hidden');
            statusMessageSpan.textContent = '';
        }}

        // --- JavaScript Download Function (for PDFs, MP4s, MPDs) ---
        // Removed from this version as per 3:39 PM request.
        // Files will now download via standard HTML <a> tag behavior.
        
        // --- Play Video Function (Modified for status messages) ---
        function playVideo(url) {{
            const player = videojs('engineer-babu-player');
            hidePlayerStatus(); // Clear any previous status

            // Show loading message
            showPlayerStatus("Loading video...", true);
            
            // Attempt to reset player and load new source
            player.pause();
            player.reset(); // Clear previous errors and sources

            if (url.includes('.m3u8')) {{
                player.src({{ src: url, type: 'application/x-mpegURL' }});
            }} else if (url.includes('.mp4')) {{
                player.src({{ src: url, type: 'video/mp4' }});
            }} else if (url.includes('.mpd')) {{ // Added .mpd specific type
                player.src({{ src: url, type: 'application/dash+xml' }});
            }}
            else {{
                // Fallback for unrecognized video types - will try to play, but might fail.
                // The error event listener will catch and display appropriate message.
                player.src({{ src: url, type: 'video/webm' }}); // Default fallback type
                console.warn("Attempting to play an unrecognized video URL type. Playback may fail:", url);
            }}

            player.load();
            player.play().catch(error => {{
                // This catch handles errors from the play() promise itself (e.g., autoplay blocked)
                if (error.name === 'NotAllowedError') {{
                    showPlayerStatus("Autoplay prevented. Please click play manually.", false);
                }} else {{
                    showPlayerStatus("Could not play video. See console for details.", false);
                }}
                console.error("Video playback promise rejected:", error);
            }});
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
        }}

        document.addEventListener('DOMContentLoaded', () => {{
            passwordPrompt.style.display = 'block';
            applyTheme(); // Apply theme when the page loads
        }});
    </script>
</body>
</html>
'''
    return html_template

# Function to download video using FFmpeg (not used in this HTML generation context)
def download_video(url, output_path):
    command = f"ffmpeg -i {url} -c copy {output_path}"
    subprocess.run(command, shell=True, check=True)

# Command handler for /start
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text("𝐖𝐞𝐥𝐜𝐨𝐦𝐞! 𝐏𝐥𝐞𝐚𝐬𝐞 𝐮𝐩𝐥𝐨𝐚𝐝 𝐚 .𝐭𝐱𝐭 𝐟𝐢𝐥𝐞 𝐜𝐨𝐧𝐭𝐚𝐢𝐧𝐢𝐧𝐠 𝐔𝐑𝐋𝐬.")

# Message handler for file uploads
@app.on_message(filters.document)
async def handle_file(client: Client, message: Message):
    print("Received a document.") # Log step
    # Initialize file_name to an empty string to prevent NameError in except block
    file_name = "" 
    downloaded_file_path = "" # Also initialize this for similar reason
    try:
        # Check if the file is a .txt file
        if not message.document.file_name.endswith(".txt"):
            await message.reply_text("Please upload a .txt file.")
            print("File is not a .txt file.") # Log step
            return

        # Download the file
        file_name = message.document.file_name # Assign file_name here
        print(f"Attempting to download file: {file_name}") # Log step
        downloaded_file_path = await message.download()
        print(f"File downloaded to: {downloaded_file_path}") # Log step

        # Ensure the output HTML folder exists
        os.makedirs(OUTPUT_HTML_FOLDER, exist_ok=True)
        print(f"Ensured output folder exists: {OUTPUT_HTML_FOLDER}") # Log step

        # Read the file content
        print(f"Reading content from {downloaded_file_path}") # Log step
        with open(downloaded_file_path, "r") as f:
            file_content = f.read()
        print("File content read successfully.") # Log step

        # Extract names and URLs (no subjects)
        print("Extracting names and URLs.") # Log step
        urls = extract_names_and_urls(file_content)
        print(f"Extracted {len(urls)} URLs.") # Log step

        # Categorize URLs
        print("Categorizing URLs.") # Log step
        videos, pdfs, others = categorize_urls(urls)
        print(f"Categorized: {len(videos)} videos, {len(pdfs)} PDFs, {len(others)} others.") # Log step

        # Generate HTML
        print("Generating HTML content.") # Log step
        html_content = generate_html(file_name, videos, pdfs, others)
        print("HTML content generated.") # Log step

        # Construct the full path for the new HTML file within the output folder
        html_file_name = file_name.replace(".txt", ".html")
        html_file_path = os.path.join(OUTPUT_HTML_FOLDER, html_file_name)
        print(f"HTML file will be saved to: {html_file_path}") # Log step

        with open(html_file_path, "w") as f:
            f.write(html_content)
        print("HTML file saved successfully.") # Log step

        # Send the HTML file to the user
        print(f"Sending HTML file {html_file_path} to user.") # Log step
        await message.reply_document(document=html_file_path, caption="✅ 𝐒𝐮𝐜𝐜𝐞𝐬𝐬𝐟𝐮𝐥𝐥𝐲 𝐃𝐨𝐧𝐞\n\n पुरुषोत्तम जांगिड़™")
        print("HTML file sent to user.") # Log step

        # Forward the .txt file to the channel
        print(f"Forwarding original .txt file {downloaded_file_path} to channel.") # Log step
        await client.send_document(chat_id=CHANNEL_USERNAME, document=downloaded_file_path)
        print("Original .txt file forwarded.") # Log step

        # Clean up files
        os.remove(downloaded_file_path) # Remove the downloaded .txt file
        print(f"Cleaned up downloaded .txt file: {downloaded_file_path}") # Log step
        # The generated HTML file remains in the 'generated_html' folder
        # If you want to remove it after sending, uncomment the next line:
        # os.remove(html_file_path)

    except Exception as e:
        error_message = f"फ़ाइल '{file_name if file_name else 'unknown file'}' को संसाधित करते समय एक एरर हुई: {e}"
        print(error_message) # कंसोल पर एरर लॉग करें
        await message.reply_text(f"❌ एक एरर हुई: {error_message}। कृपया बाद में पुनः प्रयास करें या सहायता से संपर्क करें।")
        # यदि डाउनलोड हो गया लेकिन प्रसंस्करण विफल हो गया तो सफाई का प्रयास करें
        if downloaded_file_path and os.path.exists(downloaded_file_path):
            os.remove(downloaded_file_path)
            print(f"Cleaned up downloaded .txt file after error: {downloaded_file_path}")

# बॉट चलाएँ
if __name__ == "__main__":
    print("बॉट चल रहा है...")
    app.run()
