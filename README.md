# 📸 Quote Bot — Instagram Quote Card Generator

A Telegram bot that turns photos + quotes into Instagram-ready 1080×1080 images in 5 beautiful styles.

---

## How It Works

1. Send a **photo** → bot asks for your quote → pick a style → get back the finished image
2. Send **just text** → bot creates a template-only card (no photo needed)

### The 5 Styles

| Style | Look | Best for |
|---|---|---|
| 🌊 Airy & Minimal | Bold text directly on photo, clean | Nature photos, landscapes |
| ☁️ Pure Minimal | Textured gray background, elegant serif | Short poetic quotes |
| 📖 Book Page | Warm paper + yellow highlighter | Intimate, literary quotes |
| 🌑 Dark Card | Dark navy/black, bold white + accent | Motivational, bold statements |
| ☀️ Warm Editorial | Photo with bottom gradient fade | Any photo with vibe |

---

## Setup — Step by Step

### Step 1: Create the Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Give it a name (e.g. `Quote Studio`)
4. Give it a username (e.g. `quotestudio_bot`)
5. BotFather will give you a **token** that looks like: `7123456789:AAFxxx...`
6. Copy and save that token

---

### Step 2: Deploy on Railway (Free, Always-On)

Railway gives you free hosting that runs 24/7.

1. Go to [railway.app](https://railway.app) and sign up (use GitHub login)

2. Create a new project:
   - Click **New Project** → **Deploy from GitHub repo**
   - Upload this folder as a GitHub repo (see Step 3 below)

3. Or use Railway CLI (faster):
```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

4. Set the environment variable:
   - In Railway dashboard → your project → **Variables**
   - Add: `TELEGRAM_BOT_TOKEN` = your token from BotFather

5. Railway will auto-deploy. Check **Logs** to see `🤖 Bot is running...`

---

### Step 3: Push to GitHub

```bash
# In this folder:
git init
git add .
git commit -m "Initial quote bot"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/quote-bot.git
git push -u origin main
```

Then connect that repo in Railway.

---

### Step 4: Test Your Bot

1. Open Telegram, search for your bot's username
2. Send `/start`
3. Send a photo
4. Reply with your quote
5. Pick a style
6. 🎉 Get your Instagram card back in seconds

---

## Bot Commands

| Command | What it does |
|---|---|
| `/start` | Welcome message |
| `/cancel` | Cancel current generation |

---

## Tips

- **Two-line quotes**: Use a line break in your message to split into context + main text
  ```
  remember to
  love yourself.
  ```
  The first line becomes small/context, second becomes the bold main text.

- **Dark Card + handle**: After choosing Dark Card style, you can type your Instagram handle (e.g. `@yourname`) and it appears on the image.

- **Surprise me**: The 🎲 option picks a random style each time — good for variety.

---

## File Structure

```
quotebot/
├── bot.py          # Telegram bot logic
├── styler.py       # Image rendering (all 5 styles)
├── requirements.txt
├── Procfile        # Railway deployment
├── nixpacks.toml   # Font installation on Railway
└── README.md
```

---

## Running Locally (optional)

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=your_token_here
python bot.py
```
