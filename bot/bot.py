from telebot import TeleBot

from database import *
from utils import *
from config import *

bot = TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Welcome to SearchOnion bot\nUse /help for help")

@bot.message_handler(commands=["help"])
def help(message):
    helps = {
        "start": "Start the chat with bot",
        "help": "Shows this message",
        "crawl_queue": "Show status about our Crawl Queue",
        "crawl_history": "Show status about our Crawl History",
        "add": "Add URL in our Crawl Queue",
    }

    reply_text = "This is for intracting with projcet SearchOnion\n"
    for command, help_text in helps.items():
        reply_text += f"/{command} - {help_text}\n"

    bot.reply_to(message, reply_text)

@bot.message_handler(commands=["crawl_queue"])
def crawl_queue(message):
    size = CrawlQueue.size()
    bot.reply_to(message, f"Currently there are {size} URLs in our Crawel Queue")

@bot.message_handler(commands=["crawl_history"])
def crawl_history(message):
    size = CrawlQueue.size()
    last_history = CrawlHistory.select().order_by(CrawlHistory.id.desc()).first()
    if not last_history:
        bot.reply_to(message, "Our search history is empty")
        return
    bot.reply_to(message, f"We have crawled {last_history.id} URLs till now, and crawling...")

@bot.message_handler(commands=["add"])
def add(message):
    text_splits = message.text.split(" ")
    if len(text_splits) == 1:
        bot.reply_to(message, "Please provide URL with the command")
        return
    url = text_splits[1]
    if not is_valid_url(url):
        bot.reply_to(message, "The URL is provided isn't seem correct, please check your URL")
        return
    added = CrawlQueue.add(url)
    if not added:
        bot.reply_to(message, "amm I think we have already crawled this URL and it's in our Crawl History...")
        return
    bot.reply_to(message, "Your URL is in our CrwelQueeu, it will be crawl soon")
