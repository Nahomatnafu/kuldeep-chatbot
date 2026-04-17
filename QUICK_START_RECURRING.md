# ⚡ Quick Start: How to Use the Chatbot After Setup

**This is what your client will do EVERY TIME after the initial setup.**

---

## 🎯 TL;DR (The Quick Version)

After the one-time setup, every time your client wants to use the chatbot:

```
1. Open Docker Desktop (1 click, wait 30 seconds)
2. Open Terminal
3. Type: cd kuldeep-chatbot
4. Type: docker-compose up
5. Open http://localhost:3000 in browser
6. Use the chatbot!
7. When done, press CTRL+C in Terminal
```

**Total time: 2 minutes**

---

## 📋 Step-by-Step (Recurring, Every Time)

### Step 1: Start Docker Desktop

**Windows:**
- Click Start Menu
- Search for "Docker Desktop"
- Click to open
- Wait 30-60 seconds (look for whale icon in taskbar)

**macOS:**
- Open Applications
- Find "Docker.app"
- Double-click to open
- Wait 30-60 seconds (look for whale icon in menu bar)

**Linux:**
Already running (skip this step).

### Step 2: Open Terminal

**Windows (PowerShell):**
- Press `Windows Key + R`
- Type: `powershell`
- Press Enter

**macOS:**
- Press `Command + Space`
- Type: `terminal`
- Press Enter

**Linux:**
- Press `Ctrl + Alt + T`

### Step 3: Navigate to Project Folder

Type this command and press Enter:

```bash
cd kuldeep-chatbot
```

(Or navigate to wherever you cloned the repo)

### Step 4: Start the Chatbot

Type this command and press Enter:

```bash
docker-compose up
```

**Wait for this message in Terminal:**
```
frontend-1  | ✓ Ready in 1527ms
```

This means everything is running!

### Step 5: Open in Browser

Once you see "Ready", open your browser and go to:

```
http://localhost:3000
```

You should see the Kuldeep Chatbot welcome screen. ✅

### Step 6: Use the Chatbot

Now you can:
- Click "Documents" to upload files
- Ask questions
- View sources
- Everything works in the browser

**You don't need Terminal anymore once it's running.**

### Step 7: Stop When You're Done

In Terminal, press:

```
CTRL + C
```

(Hold down Control, then press C)

The chatbot will stop, but **your documents and chat history are saved.**

---

## 🔄 Comparison: First Time vs. Every Time After

### First Time (One-time setup: ~15 minutes)
```
✓ Install Docker Desktop (5 min)
✓ Get OpenAI API key (2 min)
✓ Clone repo with git (2 min)
✓ Create .env file (1 min)
✓ Run docker-compose up (2 min)
✓ Open browser (1 min)
```

### Every Time After (Recurring: ~2 minutes)
```
✓ Open Docker Desktop (30 sec)
✓ Open Terminal (10 sec)
✓ Run: cd kuldeep-chatbot (5 sec)
✓ Run: docker-compose up (1 min)
✓ Open browser (10 sec)
✓ Done! Use the chatbot
```

---

## 📁 Important: The Folder Never Moves

After you clone the repo once, the `kuldeep-chatbot` folder stays in the same place on your computer.

Example locations:
- C:\Users\[YourName]\Desktop\kuldeep-chatbot (Windows)
- /Users/[YourName]/Downloads/kuldeep-chatbot (macOS)
- /home/[YourName]/kuldeep-chatbot (Linux)

**You navigate TO that folder every time using Terminal.**

---

## ❓ Common Recurring Questions

### Q: Can I move the folder?
**A:** Yes, but then you need to navigate to the new location in Terminal.

Example: If you move it to Desktop:
```bash
cd Desktop\kuldeep-chatbot  (Windows)
cd Desktop/kuldeep-chatbot  (macOS)
```

Then run `docker-compose up` as usual.

---

### Q: Do my documents get deleted when I stop?
**A:** NO! Press CTRL+C to stop the containers, but your documents are safe:
- ✅ Uploaded documents stay in `knowledge_base/`
- ✅ Chat history stays in the database
- ✅ Everything is saved locally on your computer

When you run `docker-compose up` again, everything is still there.

---

### Q: What if I restart my computer?
**A:** Same workflow:
1. Open Docker Desktop
2. Open Terminal
3. `cd kuldeep-chatbot`
4. `docker-compose up`
5. http://localhost:3000

Your documents and data are still there (they're saved on your disk).

---

### Q: Can I run it on another computer?
**A:** Yes! But you need:
1. Docker Desktop installed on that computer
2. Clone the repo again
3. Create a new .env with the API key
4. Run `docker-compose up`

Each computer has its own separate copy of the project and data.

---

### Q: What if I delete the folder?
**A:** Everything is deleted:
- ✅ The chatbot project
- ✅ All uploaded documents
- ✅ All chat history

**Don't do this unless you want a completely fresh start.**

---

## 📋 Checklist: Recurring Usage

Every time before using the chatbot:

- [ ] Docker Desktop is running (check taskbar/menu bar)
- [ ] Terminal is open
- [ ] I've navigated to `kuldeep-chatbot` folder
- [ ] I've run `docker-compose up`
- [ ] I see "Ready in XXXms" message
- [ ] I've opened http://localhost:3000

If all checkboxes are checked, you're ready to use the chatbot! ✅

---

## 🎓 Understanding the Workflow

Think of it like using any other app:

```
Slack, Zoom, Chrome, etc.:
- Desktop icon → Click → App opens

Kuldeep Chatbot:
- Docker icon → Open
- Terminal → 1 command → Browser → App opens
```

It's just one extra step (the Terminal command), but after that it's like any other app.

---

## ✨ Advanced: Simplify This (Optional)

If you don't want to open Terminal every time, ask your developer to create:

**Windows:** A `.bat` file (batch file) you can double-click
```batch
cd /d C:\Users\YourName\Desktop\kuldeep-chatbot
docker-compose up
pause
```

**macOS/Linux:** A `.sh` file (shell script) you can double-click
```bash
cd /Users/YourName/Desktop/kuldeep-chatbot
docker-compose up
```

Then you'd just:
1. Open Docker Desktop
2. Double-click the batch/shell file
3. Open http://localhost:3000

But for now, the Terminal method is fine and works perfectly!

---

**That's all you need to know. You're set!** 🚀
