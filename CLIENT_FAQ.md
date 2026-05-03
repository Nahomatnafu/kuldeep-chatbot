# ❓ Client FAQ — Common Questions Answered

## Recurring Usage (After Initial Setup)

### Q: After the first setup, how do I start the chatbot?
**A:** Only 4 simple steps:

1. Open Docker Desktop (click the icon, wait 30 seconds)
2. Open Terminal (copy-paste: `powershell` on Windows, `terminal` on Mac)
3. Navigate to folder: `cd kuldeep-chatbot`
4. Start: `docker-compose up`
5. Open http://localhost:3000 in browser

Then you can use the chatbot. When done, press CTRL+C in Terminal to stop.

**That's it! Same steps every time.**

---

### Q: Do I have to open Terminal every time?
**A:** YES, you need Terminal to start the containers.

**But here's the good news:**
- You only type one command: `docker-compose up`
- Takes 10 seconds
- After that, everything works in your browser
- Once running, you don't touch Terminal again until you stop

**Think of it like this:**
- Opening Docker Desktop = turning on the car engine
- Opening Terminal + `docker-compose up` = starting the engine (1 command)
- Using the chatbot = driving the car (all in browser, no engine commands needed)

---

### Q: Do I just go to Docker and the project will be there?
**A:** Not quite. Here's how Docker works:

1. Docker Desktop is just the engine — it runs in the background
2. The `kuldeep-chatbot` folder stays on your computer (Desktop, Downloads, etc.)
3. You still need to open Terminal to tell Docker to start that folder's containers
4. Then the chatbot appears at http://localhost:3000

**You can't just click Docker and have the chatbot magically start.** Docker needs the Terminal command to know which project to run.

---

### Q: Can I create a shortcut or button to start everything?
**A:** YES! Ask your developer to create a batch file (Windows) or shell script (Mac/Linux) that you can double-click to start everything automatically.

For now, use the Terminal method (it's really just 1 command).

---

### Q: What if I restart my computer?
**A:**
1. Open Docker Desktop
2. Open Terminal
3. `cd kuldeep-chatbot`
4. `docker-compose up`
5. Done

Your documents and chat history are safe. Nothing is deleted when your computer restarts.

---

## Setup Questions

### Q: Do I need to install VS Code or any coding software?
**A:** NO! You don't need any coding tools. You only need:
- Docker Desktop (the only software)
- Terminal (built into every computer)
- A web browser (Chrome, Firefox, Safari, Edge)

---

### Q: Where do I clone the repo and run commands?
**A:** In the **Terminal** (or PowerShell on Windows).

This is a built-in application on every computer:
- **Windows**: Press `Windows Key + R`, type `powershell`, press Enter
- **macOS**: Press `Command + Space`, type `terminal`, press Enter
- **Linux**: Press `Ctrl + Alt + T`

It's just a text window where you copy-paste commands. No coding knowledge needed.

---

### Q: What is the .env file?
**A:** It's a simple text file that holds your OpenAI API key.

Think of it like a password vault — it tells the app:
> "Here's the key to access OpenAI"

You create it by:
1. Opening Notepad or TextEdit
2. Typing: `OPENAI_API_KEY=sk-your-key-here`
3. Saving as `.env` (not `.env.txt`)

That's it. No complex setup.

---

### Q: Where does the cloned repo go?
**A:** Wherever you run the `git clone` command.

Example:
- You run `git clone ...` from your Desktop
- → Repo appears on Desktop as a folder called `kuldeep-chatbot`
- → Navigate into that folder in Terminal
- → Run `docker-compose up` from inside

---

## Running the App

### Q: Does Docker Desktop stay running forever?
**A:** No! You only run it when you want to use the chatbot.

1. **Start**: Open Docker Desktop (wait 1 minute for it to start)
2. **Run**: Open Terminal, navigate to folder, run `docker-compose up`
3. **Use**: Open http://localhost:3000 in browser
4. **Stop**: Press `CTRL + C` in Terminal
5. **Close**: Close Docker Desktop if you want

Docker doesn't use resources unless containers are running.

---

### Q: What's the difference between "docker-compose up" and other commands?
**A:** 

| Command | What It Does |
|---------|-------------|
| `docker-compose up` | Starts everything. You see live logs. |
| `docker-compose up -d` | Starts everything in background (advanced). |
| `docker-compose stop` | Pauses everything. Data is kept. |
| `docker-compose down` | Stops and deletes containers (data kept). |
| `docker-compose down -v` | **WARNING**: Deletes containers AND data. |

For beginners: Just use `docker-compose up`.

---

### Q: Why do I see error messages in the Terminal?
**A:** Usually fine! Log messages include INFO, WARNING, ERROR. As long as you see:
```
✓ Ready in 1527ms
```

The app is working. Ignore warnings.

---

## OpenAI API Key

### Q: How do I know if my API key works?
**A:** Once everything is running, try uploading a document and asking a question.

If it works:
- Answer appears in the chat
- Sources are shown

If it fails:
- You'll see an error: "OPENAI_API_KEY is not set" or "Invalid API key"

---

### Q: What if I lose my API key?
**A:** You can regenerate it:
1. Go to: https://platform.openai.com/api-keys
2. Find the key and click the delete (🗑️) button
3. Click "Create new secret key"
4. Copy the new key
5. Update your `.env` file with the new key

---

### Q: How much will this cost?
**A:** Depends on:
- How many documents you upload
- How many questions you ask
- Document size (larger documents = more tokens = more cost)

Typical usage: $0.10 - $1 per day. Check your balance on:
https://platform.openai.com/account/billing/overview

---

## Troubleshooting

### Q: "Port 3000 is already in use"
**A:** Another app is using port 3000 (maybe from a previous run).

**Windows:**
```powershell
Get-NetTCPConnection -LocalPort 3000 | Stop-Process -Force
```

**macOS/Linux:**
```bash
lsof -ti:3000 | xargs kill -9
```

Then try `docker-compose up` again.

---

### Q: "Connection refused" or "Cannot reach backend"
**A:** The backend is still starting (takes 10-20 seconds).

Wait 30 more seconds and refresh your browser (F5).

---

### Q: "No documents uploaded" error
**A:** Click the **Documents** button and upload a file.

Wait for the message: "✅ Ingested X chunks"

Then try asking a question.

---

### Q: Can I use this on another computer?
**A:** YES!

1. Install Docker Desktop on the other computer
2. Clone the repo
3. Create .env with your API key
4. Run `docker-compose up`

Everything works the same way.

---

## Data & Privacy

### Q: Where are my documents stored?
**A:** On your computer only, in a folder called `chroma_db/`.

They're NOT uploaded to any server.

---

### Q: Who can see my OpenAI API key?
**A:** Nobody. It's in your `.env` file on your computer.

The key is only used to send requests to OpenAI's servers. We never see it.

---

### Q: If I delete the project, are my documents deleted?
**A:** YES. Deleting the project folder deletes everything.

Make backups if you want to keep your documents.

---

## Performance

### Q: Why is it slow to upload large documents?
**A:** Because they're being split into chunks and embedded into a vector database.

- Small PDFs (<5 MB): 10-30 seconds
- Medium PDFs (5-20 MB): 1-3 minutes
- Large PDFs (>20 MB): 5+ minutes

This is normal. Be patient.

---

### Q: Can I upload multiple documents at once?
**A:** Yes! Drag a folder into the upload area.

Docker will ingest all of them (one at a time).

---

## Still Have Questions?

**Before you email:**
1. Check this FAQ
2. Read: **CLIENT_SETUP_GUIDE.md** in the repo
3. Check the error message carefully

**When you email:**
Include:
- What you're trying to do
- What error you see
- Output of: `docker --version`
- Your operating system (Windows/Mac/Linux)

---

**Good luck! The chatbot is simple to use once it's running.** 🚀
