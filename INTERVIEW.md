# Presenting and defending the Study Chatbot

## The 30-second pitch

"Most chatbots answer from a model and sometimes invent facts. Mine does the
opposite: it answers only from notes I actually wrote. You ask a question,
it searches my DBMS and DSA notes, and if nothing matches well enough it
says 'Not in your notes' instead of guessing. It runs fully offline, with
only Python's standard library — no API key, no internet, no model."

## Architecture (draw this on a board if asked)

```
Browser / terminal  (frontend: ask + add notes)
        |  HTTP / function call, localhost only
Python backend (server.py / chatbot.py)
        |  loads, splits, scores
notes/  (dbms.md, dsa.md, ... — plain text, one heading = one chunk)
```

- Frontend does no searching. It only collects the question and the new
  note text, and displays the answer.
- Backend does all the work: loading notes, tokenising, scoring, saving
  new notes, and reloading its index immediately after a save.
- Nothing leaves the computer. That is a design choice, not a missing
  feature: it is what makes the "no hallucination" claim checkable.

## How matching works (say this, don't just say "keyword search")

1. Notes are split into chunks, one per `#` heading.
2. The question is lowercased, stopwords ("what", "is", "a") are removed,
   and plurals are stemmed ("cursors" → "cursor", "anomalies" → "anomaly").
3. Abbreviations are expanded by a small lookup: BST → binary search tree,
   DBMS → database management system.
4. Each chunk scores by IDF-weighted word overlap: rare words
   (normalization, transitive) count more than common words (database).
   Each word shared with the chunk's heading adds a title bonus of 2.5,
   so "what is linked list?" lands on the Linked List note, not on a note
   that merely mentions linked lists.
5. If the best score is below 4.0, the bot refuses. That threshold is
   deliberate: a passing mention must lose to a refusal.

Complexity: scoring one question is O(chunks × question words). With
student-scale notes that is instant; it is not designed for millions
of documents — say that honestly (see Limitations).

## Demo script (2 minutes, in this order)

1. `python server.py`, open http://localhost:8000
2. Ask "what is 3NF?" → correct answer, with source file, heading, score.
3. Ask "what is BST?" → shows the abbreviation expansion working.
4. Ask "what is quantum physics?" → "Not in your notes." This is the
   feature, not a failure. Point it out.
5. Add a note in the web form (e.g. Deadlock), then ask about it →
   it answers at once, because the backend reloads its index on save.
6. (Terminal, if asked) `python chatbot.py --explain "what is a cursor?"`
   → shows the top 3 matches and scores, so the choice is auditable.

Or run the whole script at once: `python demo.py`

## Design decisions you should be able to defend

- **Why not an LLM?** An LLM cannot prove an answer came from my notes.
  Retrieval over my own files can: every answer is a verbatim chunk with
  a source and a heading.
- **Why standard library only?** Zero setup, zero cost, runs on any
  laptop, and there is nothing to break when an API changes.
- **Why a threshold instead of always answering?** Always answering
  guarantees wrong answers on uncovered topics. Refusing is the honest
  behaviour for a study tool.
- **Why verbatim answers, not rewritten ones?** Rewriting would reintroduce
  invention. The note text is the answer; the bot only selects it.

## Limitations (say these before the interviewer finds them)

- Keyword matching, not meaning: it will miss a question phrased with
  completely different words for the same idea (no embeddings yet).
- One best chunk only: it cannot combine two notes into one answer.
- No conversation memory: each question is independent.
- Notes are only as good as you write them: a wrong note gives a
  wrong (but cited) answer.
- Scaling: fine for hundreds of notes, not built for a web-scale corpus.

## Future scope (if asked "what next?")

- Embeddings / semantic search for same-idea-different-words questions.
- Multi-chunk answers with citations for each part.
- Edit and delete notes from the frontend (added Nov 2026: pick a note, load, save changes, or delete — backend rewrites the section and reloads).
- A small test set of questions with expected sources, run on every change.

## Likely interview questions, short answers

**Q: How do you stop hallucinations?**
A: The bot never generates text. It only selects a chunk from notes, and
refuses below a score threshold. There is no generation step to hallucinate in.

**Q: What is IDF and why use it?**
A: Inverse document frequency — how rare a word is across notes. Rare
words are more discriminating, so a shared rare word scores more than a
shared common word.

**Q: Why does a heading match matter so much?**
A: Because "what is X?" should find the note titled X. Without the title
bonus, a note that mentions X in passing could win — that was a real bug
in the first version, fixed by weighting headings and raising the threshold.

**Q: What happens when I add a note?**
A: The backend appends "# Title + content" to the chosen .md file and
rebuilds its chunk list and IDF table immediately, so the next question
can already find it.

**Q: Why offline?**
A: Privacy and reliability: notes stay on the machine, it works without
internet, and there is no API cost or key to manage.

**Q: What would break if notes grew 100x?**
A: Scoring stays linear in chunks, so it would slow down but still work
for thousands of chunks. Beyond that I would add an inverted index
(word → chunks) instead of scanning every chunk.
