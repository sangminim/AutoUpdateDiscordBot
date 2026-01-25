
import json
import os
import discord
from discord.ext import tasks, commands
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from keep_alive import keep_alive  # Import keep_alive module

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
KRCHANNEL_ID = os.getenv("KRCHANNEL_ID")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")
if not CHANNEL_ID or not KRCHANNEL_ID:
    raise RuntimeError("CHANNEL_ID / KRCHANNEL_ID is not set")

# URLs for the update websites 한/영 언디셈버 공식 웹사이트
url = 'https://ud.floor.line.games/us/bbs/notice/notice_us/1'  # English update website 영어 웹사이트
KRurl = 'https://ud.floor.line.games/kr/bbs/notice/notice_kr/1'  # Korean update website 한국 웹사이트

# Discord intents
intents = discord.Intents.default()
intents.message_content = True

# Config files for storing URLs and titles
CONFIG_FILE = 'config.json'  # 공식 웹사이트의 가장 최신 업데이트의 url이 json에 저장 되어 있다, 30분마다 새 업데이트가 올라오면 새업데이트의 url로 변경후 저장 된다
TITLE_FILE = 'Title.json'  # 공식 웹사이트의 가장 최신 업데이트의 제목이 json에 저장 되어 있다, 이하동일
KRCONFIG_FILE = 'configkr.json'  # 한국어 웹사이트의 가장 최신 업데이트의 url이 json에 저장 되어 있다, 이하동일
KRTITLE_FILE = 'Titlekr.json'  # 한국어 웹사이트의 가장 최신 업데이트의 제목이 json에 저장 되어 있다, 이하동일

# Initialize bot
bot = commands.Bot(command_prefix='!', intents=intents)


# Functions for updates
# 가장 최신 업데이트 URL 저장하기 기능
def save_default_value(href_value, config_file):
    with open(config_file, 'w') as file:
        json.dump({'default_href': href_value}, file)


# json에 저장되어 있는 url 가져오기 기능
def load_default_value(config_file):
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            config = json.load(file)
            return config.get('default_href')
    return None


# 가장 최신 업데이트 URL 공식 홈페이지에서 찾는 기능
def current_newUpdateURL(url, title_file):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    boardlist_tag = soup.find('ul', class_='board-list')
    link_tag = boardlist_tag.find('a', class_='all-link bbs-detail-link')
    save_title(link_tag.get('href'), url, title_file)
    return link_tag.get('href')


# 가장 최신 업데이트 웹사이트 안에서 내용 분류해서 그 내용 return(디스코드 채널에 포스팅 할 내용들)
def fetch_updates(url):
    response = requests.get(url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('div', class_='title').find('p', id='title').get_text()
    update_content = f"**{title}** \n\n"
    content_div = soup.find('div', class_='content ql-editor')
    paragraphs = content_div.find_all('p')
    for p in paragraphs[1:]:
        for element in p.children:
            # Skip elements with the specific color
            if element.get('style') and 'color: rgb(216, 216, 216)' in element['style']:
                continue
            if element.name == 'span':
                update_content += element.get_text()
            elif element.name == 'strong':
                update_content += f"**{element.get_text()}** "
            else:
                update_content += element.string if element.string else ""
        update_content += "\n"
    return update_content


# 2000글자 이상 한번에 디스코드에 쓰는 것이 불가능하므로 내용을 2000글자 이하로 나누는 기능
def split_message(message, limit=2000):
    return [message[i:i + limit] for i in range(0, len(message), limit)]


# 가장 최신 업데이트 웹사이트에서 업데이트 제목 저장 기능
def save_title(current_href, url, title_file):
    Website = urljoin(url, current_href)
    response = requests.get(Website)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.content, 'html.parser')
    title = soup.find('div', class_='title').find('p', id='title').get_text()
    with open(title_file, 'w') as file:
        json.dump({'default_title': title}, file)
    return title

# json에 저장된 제목 불러오기 기능능
def load_title(title_file):
    if os.path.exists(title_file):
        with open(title_file, 'r') as file:
            config = json.load(file)
            return config.get('default_title')
    return None


# 주기마다(minutes=30, 30을 원하는 시간주기로 바꿔도 됨) 새 업데이트가 있을 때만 영어 채널에 포스트하는 기능
@tasks.loop(minutes=30)
async def post_en_updates():
    print("Checking for English updates")
    href_changed = False  #새 업데이트가 올라왔는가? FALSE 가 디폴트값
    default_href = load_default_value(CONFIG_FILE)  #json에 저장되어있는 href 불러오기
    current_href = current_newUpdateURL(url, TITLE_FILE)  #공식 웹사이트에서 가장 최신 업데이트 href 불러오기
    title = load_title(TITLE_FILE)  #json에 저장되어있는 웹사이트의 제목 불러오기기
    if current_href:
        if default_href is None:  #이 코드를 처음 돌렸을 때만 해당 됨 default_href에 아무것도 없을 때 current_href를 디폴트값으로 저장
            print(f"Initial default href: {current_href}")
            save_default_value(current_href, CONFIG_FILE)
            href_changed = True
        elif current_href != default_href:  #새 업데이트 발견
            print(f"Detected new EN href: {current_href}")
            save_default_value(current_href,
                               CONFIG_FILE)  # 새 href를 디폴트 href 값으로 변경
            href_changed = True
        else:  #공식 홈페이지에서 새 업데이트가 올라오지 않음
            if save_title(current_href, url, TITLE_FILE) != title:  # 가장 최신 업데이트 제목 저장과 동시에 기존 json의 저장된 제목 비교
                print(
                    "Update has been completed"
                )  #다를 경우 공식 홈페이지에서 새 업데이트를 올린게 아닌 기존에 있던 업데이트안에서 제목과 내용 변경
                href_changed = True
            else:
                print("No new update detected.")
    if href_changed:  #href_changed가 true일때만 새 업데이트 디스코드에 공지
        channel = bot.get_channel(int(CHANNEL_ID))
        update_content = fetch_updates(urljoin(url, current_href))
        if update_content:
            messages = split_message(update_content)
            for message in messages:
                await channel.send(message)


# 주기마다(minutes=30, 30을 원하는 시간주기로 바꿔도 됨) 새 업데이트가 있을 때만 한국 채널에 포스트하는 기능 위에 있는 기능과 똑같음
@tasks.loop(minutes=30)
async def post_kr_updates():
    print("Checking for Korean updates")
    href_changed = False
    default_href = load_default_value(KRCONFIG_FILE)
    current_href = current_newUpdateURL(KRurl, KRTITLE_FILE)
    title = load_title(KRTITLE_FILE)
    if current_href:
        if default_href is None:
            print(f"Initial KR default href: {current_href}")
            save_default_value(current_href, KRCONFIG_FILE)
            href_changed = True
        elif current_href != default_href:
            print(f"Detected new KR href: {current_href}")
            save_default_value(current_href, KRCONFIG_FILE)
            href_changed = True
        else:
            if save_title(current_href, KRurl, KRTITLE_FILE) != title:
                print("KR Update has been completed")
                href_changed = True
            else:
                print("No new update detected.")
    if href_changed==True:
        channel = bot.get_channel(int(KRCHANNEL_ID))
        update_content = fetch_updates(urljoin(KRurl, current_href))
        if update_content:
            messages = split_message(update_content)
            for message in messages:
                await channel.send(message)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    post_en_updates.start()
    post_kr_updates.start()

# Keep bot alive
keep_alive()

# Run the bot
bot.run(TOKEN)
