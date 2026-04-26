# n8n Workflows

Four workflows built on the n8n instance at `https://n8n.mllearninghub.com`.
Each workflow is exported as a JSON file and can be imported directly into any n8n instance.

> Part of the [Agentic AI course projects](../README.md).

---

## Workflows

### 1. HR Agent with RAG — Email Auto-Reply

**File:** `HR Agent with RAG - Email Auto-Reply.json`
**Workflow ID:** `lM1Sb9q9X9W7jhJH`

An AI-powered HR assistant that reads incoming employee emails and replies automatically using a knowledge base of HR policies stored in Pinecone.

#### How it works

Two independent paths share the same Pinecone index (`hr-policies`, namespace `hr-knowledge-base`):

| Path | Trigger | Purpose |
|------|---------|---------|
| Seed | Manual Trigger | Chunks and embeds HR policy text into Pinecone |
| Reply | Gmail Trigger (new email) | Reads the email, queries Pinecone, drafts and sends a reply |

#### Architecture

```
[Manual Trigger] → [HR Policies Data (Set)] → [Insert into Pinecone]
                                               ↑ Embeddings (OpenAI, 1024-dim)

[Gmail Trigger] → [Prepare Email Data] → [HR Agent (GPT-4o Mini)]
                   (maps threadId            ↑ Thread Memory (per email thread)
                    to sessionId)            ↑ HR Knowledge Base (Pinecone tool)
                                        → [Reply to Employee (Gmail)]
```

#### Key configuration

| Setting | Value |
|---------|-------|
| Pinecone index | `hr-policies` |
| Namespace | `hr-knowledge-base` |
| Embedding model | `text-embedding-3-small` (1024 dims) |
| Chat model | `gpt-4o-mini` |
| Gmail filter | All incoming mail to the connected account |

#### Setup steps

1. Connect a Gmail OAuth2 credential (the account that receives HR emails)
2. Connect an OpenAI API credential
3. Connect a Pinecone API credential (index must be created with **1024 dimensions**)
4. Run the **Manual Trigger** path once to seed HR policies into Pinecone
5. Activate the workflow — the Gmail Trigger will poll for new emails

---

### 2. Market Research Agent — Finance & Stocks

**File:** `Market Research Agent - Finance & Stocks.json`
**Workflow ID:** `m6YiUJTJN0RFRv6l`

A research agent that produces a formatted HTML email report covering top stocks, analyst picks, and market outlook. Runs automatically every weekday morning or on demand by sending an email.

#### How it works

Two triggers fan into the same pipeline:

| Trigger | Condition |
|---------|-----------|
| Schedule | Mon–Fri at 7:00 AM |
| Gmail Trigger | Email with subject containing "market research" |

```
[Schedule (Mon-Fri 7AM)] ─┐
                           ├→ [Set Report Config] → [Market Research Agent] → [Send Report (Gmail)]
[Gmail Trigger]           ─┘   (sets recipient email)  ↑ GPT-4o
                                                        ↑ SerpAPI (live search)
                                                        ↑ Think Tool (reasoning)
```

#### Report content

The agent researches and formats an HTML email with:
- Top-performing stocks of the day
- Analyst picks and upgrades/downgrades
- S&P 500, Dow Jones, and Nasdaq outlook
- Investment opportunities and stocks to avoid

#### Key configuration

| Setting | Value |
|---------|-------|
| Schedule | Weekly, Mon–Fri, 07:00 |
| Chat model | `gpt-4o` |
| Search tool | SerpAPI |
| Email recipient | Set in the **Set Report Config** node (`toEmail` field) |

#### Setup steps

1. Connect a Gmail OAuth2 credential
2. Connect an OpenAI API credential
3. Connect a SerpAPI credential
4. Open the **Set Report Config** node and update `toEmail` to your address
5. Activate the workflow

---

### 3. RAG — Text + File Ingest + Chat Query (Pinecone)

**File:** *(export from workflow ID `YOOkSfmwWMm5gw93`)*
**Workflow ID:** `YOOkSfmwWMm5gw93`

A Retrieval-Augmented Generation (RAG) system backed by Pinecone. Supports ingesting plain text via webhook, uploading PDF/HTML/TXT files via a second webhook, and querying via an interactive chat widget.

#### How it works

Three independent paths share the same Pinecone index (`company-records`):

| Path | Entry point | What it does |
|------|-------------|--------------|
| Text ingest | `POST /webhook/rag-ingest` | Accepts JSON body, chunks and embeds text into Pinecone |
| File ingest | `POST /webhook/rag-ingest-file` | Accepts PDF, HTML, or TXT file upload, auto-detects format |
| Chat query | Chat Trigger (public widget) | Answers questions using retrieved passages from Pinecone |

#### Architecture

```
[POST /rag-ingest]      → [Insert Into Vector Store] → [Ingest OK]
  body: { text, source }   ↑ Embeddings + Text Loader + Splitter

[POST /rag-ingest-file] → [Insert File Into Vector Store] → [File Ingest OK]
  multipart file upload    ↑ Embeddings + Binary Loader (auto) + Splitter

[Chat Trigger] → [RAG Agent (GPT, temp 0.2)]
                  ↑ Chat Memory (session-based)
                  ↑ Document Knowledge Base (Pinecone retrieve-as-tool)
```

#### Ingest API reference

**Text ingest:**
```bash
curl -X POST https://n8n.mllearninghub.com/webhook/rag-ingest \
  -H "Content-Type: application/json" \
  -d '{ "text": "Your document content here", "source": "optional-label" }'
```

**File ingest (PDF, HTML, TXT):**
```bash
curl -X POST https://n8n.mllearninghub.com/webhook/rag-ingest-file \
  -F "file=@/path/to/document.pdf"
```

Both endpoints return `{ "ok": true, "chunks": N }` on success.

#### Key configuration

| Setting | Value |
|---------|-------|
| Pinecone index | `company-records` |
| Embedding model | `text-embedding-3-small` (1024 dims) |
| Chat model | `gpt-5-mini` (temp 0.2) |
| Chunk overlap | 200 tokens |
| Supported file types | PDF, HTML, TXT (auto-detected) |

#### Setup steps

1. Connect an OpenAI API credential
2. Connect a Pinecone API credential (index must be created with **1024 dimensions**)
3. Enable **MCP Access** in the workflow settings (Settings → MCP)
4. Activate the workflow
5. Ingest documents using the webhooks above
6. Open the public chat URL from the Chat Trigger node to start querying

---

### 4. n8n Basics Playground

**File:** `n8n Basics Playground-2.json`
**Workflow ID:** `K1fDdJVa7ZCtMYo6`

A learning workflow that demonstrates the core n8n building blocks on a single canvas. Built for developers new to n8n to explore concepts hands-on.

#### Concepts covered

| Concept | Node used | Where |
|---------|-----------|-------|
| Chat Trigger | `@n8n/n8n-nodes-langchain.chatTrigger` | Path A entry |
| Variables | `Set` (manual mode) | `1. Variables` node |
| Switch (multi-branch routing) | `Switch` (rules mode) | `2. Switch` node |
| HTTP Request (web tool) | `HTTP Request` | `3. HTTP Request` nodes |
| IF Condition | `IF` | `4. IF Condition` nodes |
| For Loop | `Split in Batches` | `6. For Loop` node |
| Manual Trigger | `manualTrigger` | Path B entry |

#### Path A — Chat Playground

Uses the public chat widget. Type a command to trigger different branches:

| Command | What happens |
|---------|-------------|
| `joke` | Fetches a random joke from `official-joke-api.appspot.com` |
| `fact` | Fetches a random fact from `uselessfacts.jsph.pl` |
| anything else | Returns a help message |

Each branch demonstrates: Variables → Switch → HTTP Request → IF Condition → formatted response.

#### Path B — For Loop Demo

Click **Run Loop Demo** (manual trigger). The workflow:

1. Creates items numbered 1–10 using `$itemIndex` in a Set node
2. Loops over them one at a time (Split in Batches, `batchSize: 1`)
3. Tests each number: `number % 2 == 0`
4. Adds a `label` (even/odd) and `squared` field to each item
5. Outputs a completion status when all items are processed

#### Setup steps

No credentials required. Both HTTP endpoints used are public APIs.

1. Import the JSON into n8n
2. Activate the workflow
3. Open the chat widget URL from the Chat Trigger node for Path A
4. Click **Run Loop Demo** for Path B

---

## Shared infrastructure

All AI workflows use the same credential accounts:

| Service | Used by |
|---------|---------|
| OpenAI API | HR Agent, Market Research Agent, RAG Workflow |
| Pinecone API | HR Agent (`hr-policies`), RAG Workflow (`company-records`) |
| Gmail OAuth2 | HR Agent, Market Research Agent |
| SerpAPI | Market Research Agent |

### Pinecone index requirements

Both Pinecone indexes must be created with **1024 dimensions** to match the `text-embedding-3-small` embedding model configured in n8n.

| Index name | Used by | Namespace |
|------------|---------|-----------|
| `hr-policies` | HR Agent | `hr-knowledge-base` |
| `company-records` | RAG Workflow | *(default)* |

---

## Running n8n locally with ngrok

When running n8n on your own machine, external services (Gmail OAuth, webhook triggers, chat widgets) cannot reach `localhost`. ngrok creates a public HTTPS tunnel to your local n8n instance so everything works end-to-end.

### 1. Install ngrok

```bash
# macOS
brew install ngrok

# or download from https://ngrok.com/download and unzip to your PATH
```

Create a free account at [ngrok.com](https://ngrok.com) and add your auth token:

```bash
ngrok config add-authtoken <YOUR_AUTH_TOKEN>
```

### 2. Start n8n

```bash
# Default port is 5678
npx n8n
# or if installed globally
n8n start
```

### 3. Start the ngrok tunnel

Open a second terminal and run:

```bash
ngrok http 5678
```

ngrok prints output like:

```
Forwarding  https://a1b2-203-0-113-42.ngrok-free.app -> http://localhost:5678
```

Copy the `https://...ngrok-free.app` URL — this is your public n8n address.

### 4. Tell n8n about its public URL

**Use the `.env` file — this is the only approach that reliably works across all platforms and n8n versions.**

n8n stores a config cache at `~/.n8n/config` (macOS/Linux) or `%USERPROFILE%\.n8n\config` (Windows). Shell environment variables are often overridden by this cache, which is why the UI keeps showing `localhost` even after setting `WEBHOOK_URL` in the terminal.

---

#### Step-by-step (.env file — recommended for all platforms)

**1. Find the directory where you run n8n from** (the folder you `cd` into before running `npx n8n`).

**2. Create a `.env` file in that directory:**

```env
WEBHOOK_URL=https://a1b2-203-0-113-42.ngrok-free.app
N8N_EDITOR_BASE_URL=https://a1b2-203-0-113-42.ngrok-free.app
```

**3. Clear the n8n config cache** so old `localhost` values don't override the `.env`:

macOS / Linux:
```bash
rm -f ~/.n8n/config
```

Windows (Command Prompt):
```cmd
del "%USERPROFILE%\.n8n\config"
```

Windows (PowerShell):
```powershell
Remove-Item "$env:USERPROFILE\.n8n\config" -ErrorAction SilentlyContinue
```

**4. Start ngrok first, then n8n:**

```bash
# terminal 1
ngrok http 5678

# terminal 2 — from the same folder that contains your .env
npx n8n
```

**5. Verify** — open a webhook node in the canvas. The URL shown should now start with `https://...ngrok-free.app`, not `localhost`.

---

#### Why environment variables alone don't work

| Method | Why it fails |
|--------|-------------|
| `set VAR=x && npx n8n` (CMD) | n8n config cache at `%USERPROFILE%\.n8n\config` overrides it |
| `export VAR=x` then `npx n8n` (bash) | Same cache issue |
| System environment variables (GUI) | Same cache issue |

The `.env` file is read by n8n's own config loader, which applies **after** the cache is merged — so it wins. Deleting the cache file ensures no stale `localhost` values survive.

---

#### macOS / Linux — inline alternative (only works when cache is absent)

If you have already deleted `~/.n8n/config`, the inline method works:

```bash
WEBHOOK_URL=https://a1b2-203-0-113-42.ngrok-free.app \
N8N_EDITOR_BASE_URL=https://a1b2-203-0-113-42.ngrok-free.app \
npx n8n
```

#### Windows — inline alternative (only works when cache is absent)

Command Prompt:
```cmd
set WEBHOOK_URL=https://a1b2-203-0-113-42.ngrok-free.app && set N8N_EDITOR_BASE_URL=https://a1b2-203-0-113-42.ngrok-free.app && npx n8n
```

PowerShell:
```powershell
$env:WEBHOOK_URL = "https://a1b2-203-0-113-42.ngrok-free.app"; $env:N8N_EDITOR_BASE_URL = "https://a1b2-203-0-113-42.ngrok-free.app"; npx n8n
```

---

> The ngrok URL changes every time you restart the tunnel on the free tier. Update the `.env` file each session, or use a [static ngrok domain](#persistent-domain-optional) to avoid this.

### 5. Configure Gmail OAuth redirect URI

When connecting a Gmail credential in n8n, Google needs to allow the ngrok URL as a redirect target.

1. Go to [Google Cloud Console](https://console.cloud.google.com) → **APIs & Services** → **Credentials**
2. Open your OAuth 2.0 Client ID
3. Under **Authorised redirect URIs**, add:
   ```
   https://a1b2-203-0-113-42.ngrok-free.app/rest/oauth2-credential/callback
   ```
4. Save, then reconnect the Gmail credential inside n8n

### 6. Test webhook endpoints

Once ngrok is running, your local webhook URLs are reachable from anywhere:

```bash
# Test the RAG text ingest webhook
curl -X POST https://a1b2-203-0-113-42.ngrok-free.app/webhook/rag-ingest \
  -H "Content-Type: application/json" \
  -d '{ "text": "Hello from outside localhost", "source": "test" }'
```

### Persistent domain (optional)

The free ngrok tier assigns a random URL on every restart. To keep a fixed URL across sessions, use a paid ngrok static domain:

```bash
ngrok http --domain=your-name.ngrok-free.app 5678
```

Set `N8N_EDITOR_BASE_URL` and `WEBHOOK_URL` to the static domain once (using any method from step 4 above) and you never need to change them again.

### Quick-start checklist

| Step | Command / Action |
|------|-----------------|
| Start n8n | `npx n8n` |
| Start tunnel | `ngrok http 5678` |
| Copy ngrok URL | e.g. `https://xxxx.ngrok-free.app` |
| Set env vars | `N8N_EDITOR_BASE_URL` and `WEBHOOK_URL` → ngrok URL |
| Gmail OAuth | Add ngrok URL to Google OAuth redirect URIs |
| Restart n8n | Apply the new env vars |
| Activate workflows | Toggle on in n8n UI |

---

## Importing a workflow

1. Open n8n → **Workflows** → **Add workflow**
2. Click the **...** menu → **Import from file**
3. Select the JSON file
4. Reconnect credentials (n8n will prompt for any missing ones)
5. Activate the workflow using the toggle in the top-right corner
