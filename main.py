from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS
import requests
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

# Enable CORS for all domains for development/testing
# For security in production, restrict to your domain (see comment below)
CORS(app)

# Uncomment below for PRODUCTION (only allow your frontend domain)
CORS(app, resources={r"/api/*": {"origins": "http://alldownloader01.free.nf"}})

@app.route('/api/threadster')
def fetch_thread_data():
    input_value = request.args.get('id')

    if not input_value:
        return jsonify({"ok": False, "message": "Please provide 'id' parameter with thread ID or full link."}), 400

    # Extract ID if input is a link
    thread_id = extract_id_from_link(input_value) if input_value.startswith("http") else input_value

    if not thread_id:
        return jsonify({"ok": False, "message": "Invalid link provided. Could not extract thread ID."}), 400

    url = f"https://threadster.app/download/{thread_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return jsonify({"ok": False, "message": "Failed to fetch page content"}), 500

        soup = BeautifulSoup(response.text, "html.parser")
        download_wrapper = soup.find("div", class_="download__wrapper")
        if not download_wrapper:
            return jsonify({"ok": False, "message": "No downloadable content found"}), 404

        download_items_divs = download_wrapper.find_all("div", class_="download_item")
        if not download_items_divs:
            return jsonify({"ok": False, "message": "No download items found"}), 404

        all_links = []
        avatar = ""
        username = ""
        caption = ""

        for index, item_div in enumerate(download_items_divs):
            if index == 0:
                profile_div = item_div.find("div", class_="download__item__profile_pic")
                profile_img_tag = profile_div.find("img") if profile_div else None
                avatar = profile_img_tag["src"] if profile_img_tag else ""
                username_span = profile_div.find("span") if profile_div else None
                username = username_span.text.strip() if username_span else ""

                caption_div = item_div.find("div", class_="download__item__caption__text")
                caption = caption_div.text.strip() if caption_div else ""

            table = item_div.find("table")
            if table:
                link_tags = table.find_all("a", class_="btn download__item__info__actions__button")
                links = [tag["href"] for tag in link_tags if tag.get("href")]
                all_links.extend(links)

        unique_links = list(set(all_links))

        result = {
            "creator": username,
            "ok": True,
            "message": "Hope you guys love my hard work :3",
            "avatar": avatar,
            "caption": caption,
            "url": unique_links,
            "username": username
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "message": f"Error occurred: {str(e)}"}), 500

def extract_id_from_link(link):
    """
    Extracts the Thread ID from a Threads URL.
    Example link: https://www.threads.net/@username/post/DEHwQg6Bl-s?params...
    """
    pattern = r"threads\.net/.+?/post/([A-Za-z0-9_-]+)"
    match = re.search(pattern, link)
    return match.group(1) if match else None

@app.route('/')
def home():
    return '✅ Threadster API is running! Use /api/threadster?id=THREAD_ID_OR_LINK'

if __name__ == '__main__':
    app.run(debug=True)
