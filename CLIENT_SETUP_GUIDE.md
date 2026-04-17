# 🚀 Kuldeep Chatbot — Client Setup Guide

**You do NOT need VS Code or any coding knowledge.** Just follow these steps.

---

## 📋 What You Need (One-Time Setup)

### 1. **Install Docker Desktop** (5 minutes)

This is the ONLY software you need to install.

**Windows:**
1. Go to: https://www.docker.com/products/docker-desktop
2. Click **"Download for Windows"**
3. Run the installer (Docker Desktop.exe)
4. Click through the installation wizard (use all default settings)
5. When asked about Hyper-V, click **"Install"** and restart your computer
6. After restart, open **Docker Desktop** from your Start Menu
7. Wait 30-60 seconds for the whale icon to appear in your taskbar

**macOS:**
1. Go to: https://www.docker.com/products/docker-desktop
2. Choose your chip:
   - **Apple Silicon (M1/M2/M3)**: Click the ARM64 link
   - **Intel Mac**: Click the Intel link
3. Open the .dmg file and drag Docker to Applications folder
4. Open Applications → Docker.app
5. Wait for the whale icon to appear in your menu bar

**Linux (Ubuntu):**
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
```

### 2. **Get an OpenAI API Key** (2 minutes)

1. Go to: https://platform.openai.com/api-keys
2. Sign up or log in with your OpenAI account
3. Click **"Create new secret key"**
4. Copy the key (starts with `sk-proj-...`)
5. **Save it in a safe place** — you'll need it in Step 3

---

## 💻 Running the Chatbot (5 minutes)

### Step 1: Open Terminal (or PowerShell on Windows)

You'll use the terminal to clone the repo and run the app.

**Windows:**
- Press `Windows Key + R`
- Type `powershell`
- Press Enter
- A black window will open — this is PowerShell

**macOS:**
- Open Spotlight (Command + Space)
- Type `terminal`
- Press Enter
- A window will open — this is Terminal

**Linux:**
- Ctrl + Alt + T (opens Terminal)

### Step 2: Clone the Repository

Copy and paste this command into your terminal:

```bash
git clone https://github.com/Nahomatnafu/kuldeep-chatbot.git
cd kuldeep-chatbot
```

Press Enter. This downloads the project (takes 1-2 minutes).

**Don't have Git?**
- Windows: Download from https://git-scm.com/download/win (install and restart terminal)
- macOS: Run `xcode-select --install`
- Linux: Run `sudo apt-get install git`

### Step 3: Create the .env File

The `.env` file tells the app your OpenAI API key.

**Windows (PowerShell):**
```powershell
"OPENAI_API_KEY=sk-your-actual-key-here" | Out-File -Encoding utf8 .env
```

Replace `sk-your-actual-key-here` with your actual key from Step 1.

**macOS/Linux (Terminal):**
```bash
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

Replace `sk-your-actual-key-here` with your actual key.

**Alternative (No Coding):**
1. Open a text editor (Notepad, TextEdit, etc.)
2. Type exactly this:
   ```
   OPENAI_API_KEY=sk-your-actual-key-here
   ```
3. Replace with your real key
4. **Save as `.env`** (IMPORTANT: not `.env.txt`) in the `kuldeep-chatbot` folder

### Step 4: Start the Application

Still in your terminal, run:

```bash
docker-compose up
```

This will:
- Download Docker images (first time: 2-3 minutes)
- Start the backend and frontend
- Show you live logs

**Wait for this message:**
```
frontend-1  | ✓ Ready in 1527ms
```

### Step 5: Open in Your Browser

Once you see "Ready" in the logs, open:

**http://localhost:3000**

🎉 The chatbot is now running! You should see the welcome screen.

---

## 📖 How to Use the Chatbot

1. **Click "Documents" button** (top right corner)
2. **Upload your PDFs/documents** (drag & drop or click Upload)
3. **Wait for ingestion** — it will show "✅ Ingested X chunks"
4. **Ask questions in the chat**
5. **See the sources** — where the answer came from

---

## 🛑 When You're Done

**To stop the chatbot:**
- In the terminal, press `CTRL + C` (hold Control, press C)
- Your documents are saved — nothing is deleted

**To run it again later:**
- Open terminal
- Run: `cd kuldeep-chatbot`
- Run: `docker-compose up`
- Open http://localhost:3000

**To delete everything and start fresh:**
- Run: `docker-compose down -v`
- Your data will be deleted
- Run `docker-compose up` to start over

---

## 🔑 Important: Your OpenAI API Key

- **This key is ONLY used locally on your computer**
- **It's NOT sent to our servers**
- **You can see the cost on OpenAI's dashboard**
- **Keep it secret** — don't share it with anyone
- **If you accidentally expose it, regenerate it** on https://platform.openai.com/api-keys

---

## ❓ Troubleshooting

### "Command 'docker' not found"
**Solution:** Docker Desktop isn't running
- Start Docker Desktop from your Start Menu / Applications
- Wait 1 minute
- Try the command again

### "Port 3000 is already in use"
**Solution:** Another app is using port 3000
- Kill the process: `docker-compose down -v`
- Try again: `docker-compose up`

### "OPENAI_API_KEY is not set"
**Solution:** `.env` file is wrong
- Make sure the file is named `.env` (not `.env.txt`)
- Check that it starts with: `OPENAI_API_KEY=sk-`
- Make sure your API key is real (starts with `sk-proj-`)

### "No documents have been uploaded"
**Solution:** Click the Documents button and upload a file
- Wait for the green checkmark
- Then ask a question

### Docker says "Connection refused"
**Solution:** The backend might still be starting
- Wait 10 more seconds
- Refresh your browser (F5)

---

## 📊 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **RAM** | 4 GB | 8 GB |
| **Disk Space** | 5 GB free | 10 GB free |
| **Internet** | Required | Required |
| **Browser** | Chrome, Firefox, Safari | Chrome, Firefox, Safari |

---

## 🎯 That's It!

You now have a fully working AI chatbot running locally on your computer. No coding knowledge required.

**Questions?** Email or message your developer with:
1. The error message you see
2. Your operating system (Windows/Mac/Linux)
3. The output of: `docker --version`

Good luck! 🚀
