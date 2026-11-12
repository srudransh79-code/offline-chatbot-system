#!/usr/bin/env python3
"""
Grounded Study Chatbot — answers ONLY from your own notes.

How it works (no LLM, no internet, no guessing):
1. Every .txt / .md file in notes/ is split into chunks (one heading section each).
2. Your question is tokenised (lowercased words, stopwords removed).
3. Each chunk is scored by IDF-weighted word overlap with the question.
4. If the best chunk scores below MIN_SCORE, the bot says
   "Not in your notes." — it never invents an answer.
5. Otherwise it prints the best chunk, verbatim, with its source file.

That is the whole anti-hallucination rule, in code:
    no matching note  ->  no answer, not a made-up answer.

Usage:
    python3 chatbot.py                       # interactive chat, type 'quit' to exit
    python3 chatbot.py "what is 3NF?"       # one-shot question
    python3 chatbot.py --notes notes "question"   # custom notes folder
"""

import math
import re
import sys
from collections import Counter
from pathlib import Path

# A chunk must score at least this high to count as "found in the notes".
# Deliberately high: a chunk that merely *mentions* a word (e.g. "DBMS"
# inside the Cursors note, or "linked list" inside the Hash Table note)
# must NOT win over a real definition — and must lose to "Not in your
# notes" if no real definition exists. Title matches push a real
# definition well over this line (see answer()).
MIN_SCORE = 4.0

# Bonus per query word found in the chunk's heading. A "what is X?"
# question should land on the note *titled* X, not on any note that
# happens to mention X in passing.
TITLE_BONUS = 2.5

STOPWORDS = set("""
a an the and or but if then else when at by for with about against between
into through during before after above below to from up down in out on off
over under again further once here there all any both each few more most
other some such no nor not only own same so than too very can will just
should now is are was were be been being have has had having do does did
doing would could ought i you he she it we they them his her its our their
this that these those am me my we us what which who whom whose why how
""".split())


def stem(word):
    """Very small plural stemmer, so 'cursor' matches 'Cursors' and
    'anomaly' matches 'anomalies'. Applied to questions and notes alike."""
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def tokenize(text):
    """Lowercase words, dropping stopwords and 1-letter tokens."""
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [stem(w) for w in words if w not in STOPWORDS and len(w) > 1]


# Abbreviation -> full form, so "what is BST?" finds the
# "Binary Search Tree" note. Interview point: this is a deliberate,
# explainable lookup, not a hidden model.
SYNONYMS = {
    "bst": ["binary", "search", "tree"],
    "dbms": ["database", "management", "system"],
    "fifo": ["first", "in", "first", "out"],
    "lifo": ["last", "in", "first", "out"],
}


def expand_query(tokens):
    expanded = list(tokens)
    for tok in tokens:
        expanded.extend(SYNONYMS.get(tok, []))
    return expanded


def load_notes(notes_dir):
    """Split every note file into heading sections. Returns list of chunks."""
    chunks = []
    for path in sorted(Path(notes_dir).glob("*")):
        if path.suffix not in (".txt", ".md") or not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        # Split on markdown headings (# ...) or blank-line-separated blocks
        # that start with a Title line. Fall back to whole paragraphs.
        sections = re.split(r"\n(?=#{1,3}\s|\n?[A-Z][^.\n]{2,60}\n=+\n)", text)
        current_title = path.stem
        for section in sections:
            section = section.strip()
            if not section:
                continue
            lines = section.splitlines()
            # First line is the heading if it looks like one
            if lines[0].startswith("#"):
                current_title = lines[0].lstrip("# ").strip()
                body = "\n".join(lines[1:]).strip()
            else:
                body = section
            if len(body) < 20:
                continue
            chunks.append({
                "source": path.name,
                "title": current_title,
                "text": body,
                "tokens": Counter(tokenize(body)),
            })
    return chunks


def build_idf(chunks):
    """IDF = how rare a word is across chunks. Rare words count more."""
    doc_count = len(chunks)
    df = Counter()
    for chunk in chunks:
        for word in chunk["tokens"]:
            df[word] += 1
    return {w: math.log((doc_count + 1) / (c + 1)) + 1.0 for w, c in df.items()}


def rank_all(question, chunks, idf):
    """Score every chunk, best first. Used by answer() and --explain."""
    query = set(expand_query(tokenize(question)))
    if not query:
        return []
    ranked = []
    for chunk in chunks:
        # IDF-weighted overlap: a rare shared word (e.g. 'normalization')
        # is worth far more than a common one (e.g. 'database').
        score = sum(idf.get(w, 1.0) for w in query if w in chunk["tokens"])
        # Heading match counts per word, not just once: "linked list"
        # matching a "Linked List" heading beats a passing mention.
        title_words = set(tokenize(chunk["title"]))
        score += TITLE_BONUS * len(query & title_words)
        ranked.append((chunk, score))
    ranked.sort(key=lambda pair: pair[1], reverse=True)
    return ranked


def answer(question, chunks, idf):
    """Return (chunk, score) for the best match, or (None, score)."""
    ranked = rank_all(question, chunks, idf)
    if not ranked:
        return None, 0.0
    best, best_score = ranked[0]
    if best_score >= MIN_SCORE:
        return best, best_score
    return None, best_score


def main():
    explain = "--explain" in sys.argv
    args = [a for a in sys.argv[1:]
            if not a.startswith("--notes") and a != "--explain"]
    notes_dir = "notes"
    if "--notes" in sys.argv:
        i = sys.argv.index("--notes")
        notes_dir = sys.argv[i + 1]

    notes_path = Path(__file__).parent / notes_dir
    chunks = load_notes(notes_path)
    if not chunks:
        print(f"No notes found in {notes_path}. Add .txt/.md files there first.")
        return
    idf = build_idf(chunks)
    n_files = len({c["source"] for c in chunks})
    print(f"Loaded {len(chunks)} note sections from {n_files} file(s). "
          f"Refusal threshold: score >= {MIN_SCORE}.")

    def ask(question):
        chunk, score = answer(question, chunks, idf)
        if explain:
            print("\n[explain] top matches (score, source : title):")
            for cand, cand_score in rank_all(question, chunks, idf)[:3]:
                mark = " <-- chosen" if cand is chunk else ""
                print(f"  {cand_score:.1f}  {cand['source']} : {cand['title']}{mark}")
            print(f"[explain] threshold: {MIN_SCORE} — "
                  f"{'answered' if chunk else 'refused'}")
        if chunk is None:
            print("\nNot in your notes.\n")
            print("I only answer from the files in notes/. "
                  "Add a note on this topic and ask again.")
        else:
            print(f"\n--- From {chunk['source']} : {chunk['title']} ---")
            print(chunk["text"].strip())
            print(f"\n(match score: {score:.1f})")

    if args:
        ask(" ".join(args))
        return

    print("Study chatbot — grounded in notes/ only.")
    print("Ask a question, or type 'quit'. If it's not in your notes, I'll say so.")
    while True:
        try:
            question = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break
        if question.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break
        if question:
            ask(question)


if __name__ == "__main__":
    main()
