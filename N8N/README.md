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

## Importing a workflow

1. Open n8n → **Workflows** → **Add workflow**
2. Click the **...** menu → **Import from file**
3. Select the JSON file
4. Reconnect credentials (n8n will prompt for any missing ones)
5. Activate the workflow using the toggle in the top-right corner
