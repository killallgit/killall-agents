"""Plain terminal prompts that need nothing installed and also read from a pipe."""

from __future__ import annotations

import re


class Cancelled(Exception):
    """The user answered with end-of-input or q; nothing has been written yet."""


def read(prompt: str) -> str:
    try:
        answer = input(prompt).strip()
    except EOFError:
        raise Cancelled from None
    if answer.lower() == "q":
        raise Cancelled
    return answer


def ask_one(title: str, options: list[tuple[str, str]], default: str) -> str:
    print(f"\n{title}")
    for number, (key, label) in enumerate(options, 1):
        print(f"  {number}) {label}{'  (default)' if key == default else ''}")
    keys = [key for key, _ in options]
    while True:
        answer = read("Choose one, Enter for the default, q to quit: ")
        if not answer:
            return default
        if answer.isascii() and answer.isdigit() and 1 <= int(answer) <= len(keys):
            return keys[int(answer) - 1]
        print(f"  enter a number from 1 to {len(keys)}")


def ask_many(title: str, options: list[tuple[str, str, str]], selected: set[str]) -> list[str]:
    """Options are (key, label, group). Numbers and ranges toggle; a selects all, n clears, Enter accepts."""
    chosen = set(selected)
    keys = [key for key, _, _ in options]
    while True:
        print(f"\n{title}")
        group = None
        for number, (key, label, heading) in enumerate(options, 1):
            if heading != group:
                group = heading
                print(f"  {heading}")
            print(f"   [{'x' if key in chosen else ' '}] {number:>2}  {label}")
        answer = read("Toggle numbers (1,3-5), a = all, n = none, Enter = accept, q = quit: ")
        if not answer:
            return [key for key in keys if key in chosen]
        picks, bad, reset = set(), [], chosen
        for token in re.split(r"[,\s]+", answer.lower()):
            if token == "a":
                reset = set(keys)
            elif token == "n":
                reset = set()
            elif m := re.fullmatch(r"(\d+)(?:-(\d+))?", token):
                low, high = int(m[1]), int(m[2] or m[1])
                if 1 <= low <= high <= len(keys):
                    picks.update(keys[low - 1 : high])
                else:
                    bad.append(token)
            else:
                bad.append(token)
        if bad:
            print(f"  not understood: {', '.join(bad)}")
            continue
        chosen = reset ^ picks


def confirm(question: str, default: bool = True) -> bool:
    answer = read(f"{question} [{'Y/n' if default else 'y/N'}]: ").lower()
    return default if not answer else answer.startswith("y")


def ask_text(question: str, default: str) -> str:
    return read(f"{question} [{default}]: ") or default
