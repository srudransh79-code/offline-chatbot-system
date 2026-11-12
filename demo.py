#!/usr/bin/env python3
"""Live demo script for presenting the study chatbot.

Runs five preset questions that show, in order:
  1. a correct in-notes answer (DBMS topic)
  2. a correct in-notes answer (DSA topic, via abbreviation)
  3. the refusal case — the anti-hallucination feature
  4. a question answered only after a note is added (see demo_note.txt)
  5. a plural/synonym match

Run:  python demo.py
This is for presenting, not for grading — it prints the chatbot's
own output, including its source citations and scores.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import chatbot

QUESTIONS = [
    "what is 3NF?",
    "what is BST?",
    "what is quantum physics?",
    "what is a cursor?",
    "what is a linked list?",
]

def main():
    notes_dir = Path(__file__).parent / "notes"
    chunks = chatbot.load_notes(notes_dir)
    idf = chatbot.build_idf(chunks)
    print(f"Study chatbot demo — {len(chunks)} note sections loaded.\n")
    for q in QUESTIONS:
        print(f"You: {q}")
        chunk, score = chatbot.answer(q, chunks, idf)
        if chunk is None:
            print("Bot: Not in your notes.\n")
        else:
            print(f"Bot (from {chunk['source']} : {chunk['title']}, "
                  f"score {score:.1f}):")
            print(chunk["text"].strip() + "\n")

if __name__ == "__main__":
    main()
