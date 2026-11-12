# Study Chatbot — Complete Working Structure, Benefits, USP & Viva Defence Notes

Read this before your viva. Everything below is true of the code in this
folder — nothing here is claimed that the program does not actually do.
If an interviewer asks a question not covered here, answer from this
document plus INTERVIEW.md, and say honestly when something is a
limitation (Section 9). That honesty is itself a defence point.

---

## 1. What the project is (the 30-second pitch)

"Most chatbots answer from a model and sometimes invent facts. Mine does
the opposite: it answers only from notes I actually wrote. You ask a
question, it searches my DBMS and DSA notes, and if nothing matches well
enough it says 'Not in your notes' instead of guessing. It runs fully
offline, with only Python's standard library — no API key, no internet,
no model."

One line: **a grounded, offline, retrieval-only study chatbot.**

- **Grounded** = every answer comes from your own files.
- **Retrieval-only** = it selects an answer, it never generates one.
- **Offline** = it works with no internet, no account, no cost.

## 2. Tech stack (and why each choice was made)

| Part | Technology | Why |
|---|---|---|
| Language | Python 3 | Readable, and the standard library is enough |
| Backend | `server.py` + `chatbot.py`, Python standard library only | Zero setup, zero cost, nothing breaks when an API changes |
| Frontend | `web/index.html` — plain HTML/CSS/JS, no framework | No build step, runs in any browser |
| Data | Plain `.txt` / `.md` files in `notes/` | Human-readable, editable in Notepad, no database to install |
| Search | Keyword matching with IDF weighting + title bonus | Explainable, auditable, provably grounded |
| AI model | None | Deliberate — see Section 7, USP 1 |
| Internet | None | Deliberate — privacy, reliability, cost |

Run it with:
```
python server.py          # web version, open http://localhost:8000
python chatbot.py         # terminal version
python chatbot.py --explain "what is a cursor?"   # shows top-3 matches + scores
python demo.py            # 5-question demo for a presentation
```

## 3. Working structure (the whole system)

```
                    ┌─────────────────────────────┐
                    │  notes/  (your own files)   │
                    │  dbms.md, dsa.md, os.md...  │
                    │  one # Heading = one chunk  │
                    └──────────────┬──────────────┘
                                   │ loaded at startup,
                                   │ reloaded on every change
                    ┌──────────────▼──────────────┐
                    │  Backend: chatbot.py        │
                    │  load_notes() → chunks      │
                    │  build_idf()  → IDF table   │
                    │  rank_all()   → scored list │
                    │  answer()     → best or None│
                    └──────────────┬──────────────┘
                                   │ HTTP on localhost only
        ┌──────────────────────────┼──────────────────────────┐
        │                          │                          │
┌───────▼────────┐        ┌────────▼────────┐        ┌────────▼────────┐
│  server.py     │        │  Web frontend   │        │  Terminal       │
│  HTTP server   │        │  index.html     │        │  chatbot.py     │
│  /api/ask      │◄───────│  ask, add, edit │        │  interactive    │
│  /api/notes    │        │  delete, reload │        │  + --explain    │
│  /api/note     │        └─────────────────┘        └─────────────────┘
│  /api/reload   │
└────────────────┘
```

### The three layers, and what each one does

**Layer 1 — Data layer: `notes/`**
- Only plain text files. No database, no binary format.
- A file is split into chunks, one per `#`, `##` or `###` heading.
- Each chunk keeps: source file name, heading (title), body text, and
  a word-count table of its body.
- Example: `dbms.md` contains a "Third Normal Form (3NF)" section, so
  that section is one chunk, citable as `dbms.md : Third Normal Form (3NF)`.

**Layer 2 — Logic layer: `chatbot.py` (the brain)**
- `load_notes()` — reads every `.txt`/`.md` file, splits it into chunks.
- `tokenize()` — lowercases, removes stopwords, stems plurals.
- `expand_query()` — expands abbreviations (BST, DBMS, FIFO, LIFO).
- `build_idf()` — computes how rare each word is across all chunks.
- `rank_all()` — scores every chunk against the question, best first.
- `answer()` — returns the best chunk, or `None` if it is below threshold.

**Layer 3 — Presentation layer: `server.py` + `web/index.html`**
- `server.py` is a small HTTP server on `127.0.0.1:8000` (your machine
  only — nobody else on the network can reach it).
- The frontend does **no searching**. It only collects the question or
  the new note, sends it to the backend, and displays the answer.
- That separation matters in a viva: frontend = input/output,
  backend = all the work. It is the classic frontend/backend split.

## 4. How it works, step by step

### 4.1 Starting up

1. `server.py` starts and calls `reload_index()`.
2. `load_notes()` reads `notes/` and builds the chunk list.
3. `build_idf()` builds the IDF table from those chunks.
4. The server listens at http://localhost:8000.

### 4.2 Asking a question (the search pipeline)

Take the example: **"what is 3NF?"**

1. **Tokenise the question.** Lowercase it, split into words, drop
   stopwords ("what", "is", "a") and one-letter words. Result: `[3nf]`.
2. **Expand abbreviations.** If a token is in the synonym table
   (BST → binary search tree, DBMS → database management system), its
   full form is added to the query. `3nf` has no expansion, so the
   query stays `[3nf]`.
3. **Stem plurals.** `cursors` → `cursor`, `anomalies` → `anomaly`.
   Applied to questions and notes alike, so both sides match.
4. **Score every chunk.** For each chunk:
   - For each query word found in the chunk's body, add its IDF score.
     IDF = `log((total_chunks + 1) / (chunks_containing_word + 1)) + 1`.
     Rare words score more: "normalization" is worth far more than
     "database", because "database" appears in almost every DBMS chunk.
   - For each query word found in the chunk's **heading**, add a title
     bonus of 2.5. This is the fix for the original bug: without it,
     a note that merely *mentions* "linked list" could beat the actual
     Linked List note.
5. **Rank.** Chunks are sorted by score, highest first.
6. **Threshold check.** If the best score is below **4.0 (MIN_SCORE)**,
   the answer is `None` — the bot says "Not in your notes." It does
   not fall back to a weaker answer, and it never invents one.
7. **Return verbatim.** Otherwise the best chunk's text is returned
   exactly as written, with its source file, heading, and match score.

Worked example: for "what is 3NF?", the "Third Normal Form (3NF)"
chunk shares the rare word `3nf` with the question and matches it in
its heading, so its score clears 4.0 and it wins. A chunk that only
mentions 3NF in passing scores far lower and loses.

### 4.3 Adding, editing, deleting notes (while it runs)

- **Add (web form):** title + content + file name → backend appends
  `# Title` + content to that `.md` file, then reloads the index.
- **Edit (web form):** pick a note → Load → change title/content →
  Save changes → backend rewrites only that section in its file, then
  reloads. Other sections in the same file are untouched.
- **Delete (web form):** pick a note → Load → Delete (with a
  confirmation) → backend removes only that section, then reloads.
- **Drop your own file in:** copy any `.txt`/`.md` file into `notes/`
  while the server is running. The backend compares the folder's file
  list, sizes and modification times on every question, and reloads
  automatically if anything changed. There is also a "Reload notes
  from folder" button on the page, and a `POST /api/reload` endpoint.
- In every case: **the next question can already use the change.**
  No restart, no rebuild, no re-upload.

### 4.4 The API (for a technical interviewer)

| Method & path | What it does |
|---|---|
| `GET /api/notes` | Lists files and note titles (auto-reloads first) |
| `GET /api/note?file=X&title=Y` | Returns one note section's full text, for editing |
| `POST /api/ask` | Asks a question, returns chunk + source + score, or refusal |
| `POST /api/notes` | Appends a new note section, reloads index |
| `PUT /api/notes` | Replaces one note section, reloads index |
| `DELETE /api/notes` | Removes one note section, reloads index |
| `POST /api/reload` | Forces a full index reload, returns section/file counts |

## 5. Benefits and advantages

**For a student using it:**
- **No wrong answers disguised as right ones.** A wrong answer you
  trust is worse than no answer. Refusing is a feature, not a failure.
- **Every answer is checkable.** Source file + heading + score are
  shown, so you can open the note and verify it in seconds.
- **Your notes, your syllabus.** It answers from what your teacher
  taught, not from generic internet text.
- **Works anywhere, offline.** No Wi-Fi, no account, no subscription,
  no API key that can expire the night before an exam.
- **Instant updates.** Add a note on a new topic and ask about it
  immediately — including by dropping your own file into `notes/`
  while the server is running.

**For the project itself (engineering advantages):**
- **Zero dependencies.** Standard library only — it runs on any
  machine with Python, with nothing to install.
- **Zero cost.** No API calls, no hosting, no database.
- **Privacy by design.** Notes never leave the computer; there is
  nothing to leak, because there is no server on the internet.
- **Easy to explain and defend.** Every step — split, tokenise,
  score, threshold — is a few lines of readable code. Nothing is a
  black box, so any line can be explained in a viva.
- **Easy to extend.** New topics = new text files. New behaviour =
  one function in `chatbot.py`, not a retrained model.

## 6. Main USP (unique selling point)

**"It cannot hallucinate — by construction, not by promise."**

Other chatbots *try* not to invent facts, using prompts and guardrails
on top of a model that still generates text. This one has **no
generation step at all**. The only output it can ever produce is a
chunk copied from a file you wrote, or the refusal "Not in your notes."

That is the sentence to lead with in a viva, and it is provable on
the spot: ask "what is quantum physics?" and it refuses, because no
note covers it. A model-based chatbot would have answered confidently
— and that confident answer is exactly the problem this project solves.

Secondary USPs, if asked "what else is different?":
- Offline + free + private, all at once (most tools give you one).
- Editable through the frontend while running — it is a study tool
  you grow, not a fixed demo.
- Fully auditable: `--explain` shows the top-3 matches and their
  scores, so the choice of answer is visible, not hidden.

## 7. Points to defend it in the interview (with short answers)

**Q: Why didn't you use an LLM / ChatGPT API?**
A: An LLM cannot prove an answer came from my notes. Retrieval over my
own files can: every answer is a verbatim chunk with a source and a
heading. Adding a model would reintroduce the exact problem — invented
facts — that this project exists to solve. And it would cost money,
need internet, and need an API key.

**Q: How do you stop hallucinations?**
A: There is no generation step to hallucinate in. The bot only selects
a chunk from notes, and refuses below a score threshold. I can prove it
live: ask about anything not in the notes and it refuses.

**Q: What is IDF and why use it?**
A: Inverse document frequency — how rare a word is across notes. Rare
words are more discriminating, so a shared rare word scores more than
a shared common word. Without it, a common word like "database" would
swamp the real topic word.

**Q: Why does a heading match matter so much?**
A: Because "what is X?" should find the note titled X. Without the
title bonus, a note that mentions X in passing could win — that was a
real bug in the first version, fixed by weighting headings and raising
the threshold to 4.0.

**Q: Why standard library only?**
A: Zero setup, zero cost, runs on any laptop, and there is nothing to
break when an API or library version changes. The whole project is
readable by one person in one sitting.

**Q: Why offline?**
A: Privacy and reliability: notes stay on the machine, it works
without internet, and there is no API cost or key to manage.

**Q: What is frontend vs backend here?**
A: The frontend (the web page) only collects the question and the new
note text and displays the answer. The backend does all the work:
loading, splitting, scoring, saving, and reloading. That is the
standard separation, and it means the search logic can be tested
without a browser at all — `python chatbot.py --explain` does that.

**Q: What happens when I add a note?**
A: The backend appends "# Title + content" to the chosen file and
rebuilds the chunk list and IDF table immediately, so the next
question can already find it. Dropping a file into `notes/` while
running works the same way, through change detection plus a Reload
button.

**Q: What is the time complexity of a search?**
A: O(chunks × question words) — it scores every chunk against the
few words in the question. With student-scale notes (tens to hundreds
of chunks) that is instant. Say this honestly: it is not built for
millions of documents.

**Q: How would you scale it to 100x the notes?**
A: First, an inverted index (word → chunks containing it), so only
chunks sharing a query word are scored instead of all of them — the
same idea Google search is built on, and it changes nothing about the
answers. Then BM25 ranking instead of plain IDF overlap, which handles
word frequency and long notes better. Beyond that, embeddings for
same-idea-different-words questions.

**Q: What is BM25, in one line?**
A: The ranking formula modern search engines use: TF-IDF improved with
diminishing returns for repeated words and normalisation for document
length, so long documents don't win just by being long.

## 8. Demo script (2 minutes, in this order)

1. `python server.py`, open http://localhost:8000.
2. Ask "what is 3NF?" → correct answer, with source file, heading, score.
3. Ask "what is BST?" → shows the abbreviation expansion working.
4. Ask "what is quantum physics?" → "Not in your notes." Point out
   this is the feature, not a failure.
5. Add a note in the web form (e.g. Deadlock), then ask about it →
   it answers at once, because the backend reloads on save.
6. Edit that note, ask again → the edited text comes back.
7. Delete it, ask again → "Not in your notes." again.
8. (Terminal, if asked) `python chatbot.py --explain "what is a cursor?"`
   → shows the top-3 matches and scores, so the choice is auditable.

Or run the whole script at once: `python demo.py`

## 9. Limitations — say these BEFORE the interviewer finds them

Saying these first is a strength, not a weakness. It shows you know
what you built and what you didn't.

- **Keyword matching, not meaning.** It will miss a question phrased
  with completely different words for the same idea (no embeddings yet).
- **One best chunk only.** It cannot combine two notes into one answer.
- **No conversation memory.** Each question is independent; it does
  not remember the previous question.
- **Notes are only as good as you write them.** A wrong note gives a
  wrong (but cited) answer — the citation makes the error findable.
- **Scaling.** Fine for hundreds of notes; not built for a web-scale
  corpus. See the inverted-index answer in Section 7 for the fix.
- **Only `.txt` / `.md` notes.** PDFs and Word files must be converted
  to plain text first.

## 10. Future scope (if asked "what next?")

- Inverted index for faster search (same answers, less scanning).
- BM25 ranking for better ordering of close matches.
- Phrase matching ("binary search tree" as one phrase, not 3 words).
- Embeddings / semantic search for same-idea-different-words questions.
- Multi-chunk answers with a citation for each part.
- A small test set of questions with expected sources, run on every
  change, so a future edit can never silently break matching again.

## 11. One-paragraph summary (use this to close, if asked "summarise it")

"A grounded study chatbot that answers only from my own notes. Notes
are split by heading into chunks, a question is cleaned and expanded,
each chunk is scored by rare-word overlap plus a heading bonus, and
anything below a threshold is refused rather than invented. The web
frontend lets me ask, add, edit and delete notes while the server is
running, and the backend reloads its index on every change. It is
offline, free, private, and provably non-hallucinating — because it
never generates text, it only selects text I wrote."
