"""Cleanup pipeline + hallucination firewall (.claude/rules/vaicom.md).

Order mirrors WhisperAttack where it matters: NFC → word mappings → fuzzy word
correction → spoken numbers → punctuation strip → whitespace collapse. Output is
what gets executed in the cockpit, so when in doubt this module returns None
(meaning: say nothing) rather than guessing.

Note: VAICOM itself rewrites a leading "to " → "two " — deliberately not done here.
"""

import logging
import os
import re
import threading
import unicodedata

from rapidfuzz import fuzz, process

import config

log = logging.getLogger("cobb.normalize")

# Whisper's favorite inventions on silence/breath noise. Exact-match after cleanup.
_HALLUCINATIONS = {
    "you", "thank you", "thanks", "thank you for watching", "thanks for watching",
    "bye", "goodbye", "okay", "so", "the", "oh", "hmm", "yeah",
}

_NUMBER_WORDS = {
    "zero": "0", "one": "1", "two": "2", "three": "3", "four": "4",
    "five": "5", "six": "6", "seven": "7", "eight": "8", "nine": "9",
    "niner": "9", "ten": "10",
}


def _load_lines(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]


class Normalizer:
    def __init__(self, settings):
        self.threshold = settings["fuzzy_threshold"]
        self._lock = threading.Lock()  # UI teaches words while PTT threads normalize
        # word_mappings.txt: `wrong phrase -> right phrase`, applied first, longest first.
        self.mappings = []
        for line in _load_lines(config.WORD_MAPPINGS_PATH):
            if "->" in line:
                src, dst = (part.strip().lower() for part in line.split("->", 1))
                if src:
                    self.mappings.append((src, dst))
        self.mappings.sort(key=lambda m: len(m[0]), reverse=True)
        # fuzzy_terms.txt: known-good vocabulary; near-miss words snap to these.
        self.terms = [t.lower() for t in _load_lines(config.FUZZY_TERMS_PATH)]
        self.reload_commands()

    def reload_commands(self):
        """(Re)load command/recipient lists — also runs after a live .vap import."""
        # commands.txt (optional): full VAICOM phrases; if present, the final text
        # must fuzzy-match one of them or it is dropped.
        self.commands = [c.lower() for c in _load_lines(config.COMMANDS_PATH)]
        # The user's own VoiceAttack commands (from a .vap export — see custom_vap.py)
        # must pass the firewall too, or "turn on the lights" gets dropped as noise.
        self.custom = [c.lower() for c in _load_lines(config.CUSTOM_COMMANDS_PATH)]
        self.commands += [c for c in self.custom if c not in set(self.commands)]
        # Recipient prefixes ("two", "tower", "texaco"…): VAICOM matches them
        # separately from the command, so commands.txt has no combined phrases.
        # Number words become digits to mirror the pipeline ("two" → "2").
        # Longest first so "springfield 1 1" wins over "springfield".
        self.recipients = sorted(
            {" ".join(_NUMBER_WORDS.get(w, w) for w in r.split())
             for r in _load_lines(config.RECIPIENTS_PATH)},
            key=len, reverse=True)
        # Suggestion pool: every word the profile actually uses — corrections should
        # come from VAICOM's own aviation language, not a generic word list.
        self.vocab = sorted(
            {w for c in self.commands for w in c.split() if w.isalpha() and len(w) > 2}
            | set(self.terms)
        )
        log.info(
            "normalizer: %d mappings, %d fuzzy terms, %d command phrases, %d vocab words",
            len(self.mappings), len(self.terms), len(self.commands), len(self.vocab),
        )

    def suggest(self, word: str, limit: int = 3):
        """Closest profile-vocabulary words — likely intended targets for a mishear."""
        word = word.strip().lower()
        pool = self.vocab or self.terms
        if not word or not pool:
            return []
        matches = process.extract(word, pool, scorer=fuzz.ratio, limit=limit)
        return [m[0] for m in matches if m[1] >= 55 and m[0] != word]

    def add_mapping(self, wrong: str, right: str) -> bool:
        """Teach a correction now and remember it in word_mappings.txt forever."""
        wrong = re.sub(r"\s+", " ", wrong.strip().lower())
        right = re.sub(r"\s+", " ", right.strip().lower())
        if not wrong or not right or wrong == right:
            return False
        with self._lock:
            if (wrong, right) in self.mappings:
                return False
            self.mappings.append((wrong, right))
            self.mappings.sort(key=lambda m: len(m[0]), reverse=True)
        with open(config.WORD_MAPPINGS_PATH, "a", encoding="utf-8") as f:
            f.write(f"{wrong} -> {right}\n")
        log.info("learned: %r -> %r", wrong, right)
        return True

    def remove_mapping(self, wrong: str, right: str):
        """Undo a taught fix: drop it from memory and from word_mappings.txt."""
        wrong = re.sub(r"\s+", " ", wrong.strip().lower())
        right = re.sub(r"\s+", " ", right.strip().lower())
        with self._lock:
            if (wrong, right) not in self.mappings:
                return False
            self.mappings.remove((wrong, right))

        def keeps(line):
            if "->" not in line:
                return True
            src, dst = (p.strip().lower() for p in line.split("->", 1))
            return (src, dst) != (wrong, right)

        try:
            with open(config.WORD_MAPPINGS_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()
            with open(config.WORD_MAPPINGS_PATH, "w", encoding="utf-8") as f:
                f.writelines(ln for ln in lines if keeps(ln))
        except OSError:
            pass
        log.info("unlearned: %r -> %r", wrong, right)
        return True

    def normalize(self, raw: str):
        """Cleaned command text, or None if this should never reach the cockpit."""
        text = unicodedata.normalize("NFC", raw).lower()
        # Whisper marks non-speech as [typing], [BLANK_AUDIO], (wind), *music* —
        # annotations, not words. Remove them before punctuation stripping can
        # launder them into ordinary text.
        text = re.sub(r"\[[^\]]*\]|\([^)]*\)|\*[^*]*\*", " ", text)
        text = re.sub(r"[^\w\s'-]", " ", text)          # punctuation → space
        text = re.sub(r"(?<=\d)-(?=\d)", " ", text)      # 1-1 → 1 1
        text = re.sub(r"\s+", " ", text).strip()

        with self._lock:
            mappings = list(self.mappings)
        for src, dst in mappings:
            text = re.sub(rf"\b{re.escape(src)}\b", dst, text)

        words = []
        for word in text.split():
            if word in _NUMBER_WORDS:
                words.append(_NUMBER_WORDS[word])
                continue
            if self.terms and word not in self.terms and word.isalpha() and len(word) > 2:
                match = process.extractOne(word, self.terms, scorer=fuzz.ratio)
                if match and match[1] >= self.threshold:
                    word = match[0]
            words.append(word)
        text = " ".join(words)

        if not text or text in _HALLUCINATIONS:
            log.info("firewall: dropped %r", raw)
            return None

        if self.commands:
            match = process.extractOne(text, self.commands, scorer=fuzz.token_sort_ratio)
            # "two rejoin": VAICOM wants recipient + command together, but only the
            # command part lives in commands.txt — match them separately and rejoin,
            # otherwise the recipient gets stripped and VAICOM addresses the whole
            # flight instead of one wingman.
            rec = next((r for r in self.recipients if text.startswith(r + " ")), None)
            if rec:
                rest = text[len(rec) + 1:]
                m2 = process.extractOne(rest, self.commands, scorer=fuzz.token_sort_ratio)
                if m2 and m2[1] >= self.threshold and (not match or m2[1] >= match[1]):
                    combined = f"{rec} {m2[0]}"
                    if combined != text:
                        log.info("matched %r → %r (recipient kept)", text, combined)
                    return combined
            if not match or match[1] < self.threshold:
                log.info("firewall: no command match ≥%d for %r", self.threshold, text)
                return None
            if match[0] != text:
                log.info("matched %r → command %r (%.0f)", text, match[0], match[1])
            text = match[0]

        return text
