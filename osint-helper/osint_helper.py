#!/usr/bin/env python3
"""OSINT HELPER - a numbered-menu launcher for OSINT tool commands.

Menus are built from tools.json. Lookup order:
  1. ~/.config/osint-helper/tools.json
  2. tools.json next to this script
"""
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

BANNER = r"""

 ░░░░░░░     ░░░     ░░      ░   ░░░  ░      ░░░░░
 ▒▒▒▒▒▒  ▒▒▒  ▒  ▒▒▒▒▒▒▒▒  ▒▒▒    ▒▒  ▒▒▒  ▒▒▒▒▒▒▒
 ▓▓▓▓▓▓  ▓▓▓  ▓▓     ▓▓▓▓  ▓▓▓  ▓  ▓  ▓▓▓  ▓▓▓▓▓▓▓
 ██████  ███  ██████  ███  ███  ██    ███  ███████
 ███████     ███     ██      █  ███   ███  ███████
                                                                                                                    
 ░░░  ░░  ░      ░  ░░░░░      ░░      ░      ░░░░                
 ▒▒▒  ▒▒  ▒  ▒▒▒▒▒  ▒▒▒▒▒  ▒▒▒  ▒  ▒▒▒▒▒  ▒▒▒  ▒▒▒                
 ▓▓▓      ▓      ▓  ▓▓▓▓▓      ▓▓      ▓      ▓▓▓▓  
 ███  ██  █  █████  █████  ██████  █████  ██  ████
 ███  ██  █      █      █  ██████      █  ███  ███

 - Brought to you by the good people at wumwumwum -
----------------------------------------------
A menu-driven terminal launcher for OSINT tools: 
Pick a target type, a Tool, a Command.
OSINT HELPER fills it in & runs it.


"""

USE_COLOR = sys.stdout.isatty()


def c(text, code):
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text


CYAN, GREEN, YELLOW, DIM, RED, BOLD = "36", "32", "33", "2", "31", "1"


def load_config():
    paths = [
        os.path.expanduser("~/.config/osint-helper/tools.json"),
        os.path.join(os.path.dirname(os.path.realpath(__file__)), "tools.json"),
    ]
    for p in paths:
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                sys.exit(f"Error parsing {p}: {e}")
    sys.exit("tools.json not found.")


def clear():
    if USE_COLOR:
        os.system("cls" if os.name == "nt" else "clear")


def header():
    clear()
    print(c(BANNER, CYAN))


def choose(title, options, back_label="Back", crumbs=""):
    """Show a numbered menu. Returns index, or None for back/quit-to-parent."""
    while True:
        header()
        if crumbs:
            print(c(crumbs, DIM) + "\n")
        print(c(title, BOLD) + "\n")
        for i, opt in enumerate(options, 1):
            print(f"  {c(str(i) + '.)', GREEN)} {opt}")
        print()
        print(f"  {c('0.)', YELLOW)} {back_label}    {c('q.) Quit', YELLOW)}")
        sel = input("\n> ").strip().lower()
        if sel in ("q", "quit", "exit"):
            sys.exit(0)
        if sel == "0":
            return None
        if sel.isdigit() and 1 <= int(sel) <= len(options):
            return int(sel) - 1
        input(c("Invalid selection. Press Enter to try again.", RED))


def fill_placeholders(template):
    """Prompt for each {placeholder}; returns (display_cmd, run_cmd)."""
    names = list(dict.fromkeys(re.findall(r"\{(\w+)\}", template)))
    values = {}
    for n in names:
        v = input(f"  Enter {c(n, YELLOW)}: ").strip()
        if not v:
            return None, None
        values[n] = v
    display = template
    run = template
    for n, v in values.items():
        display = display.replace("{" + n + "}", v)
        run = run.replace("{" + n + "}", shlex.quote(v))
    return display, run


def copy_to_clipboard(text):
    for tool in (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["clip"]):
        if shutil.which(tool[0]):
            subprocess.run(tool, input=text.encode(), check=False)
            return True
    return False


def command_screen(tool, entry, crumbs):
    header()
    print(c(crumbs, DIM) + "\n")
    print(c(entry["cmd"], GREEN))
    print(c(entry["desc"], DIM) + "\n")

    if not shutil.which(tool.split()[0]):
        print(c(f"Note: '{tool}' was not found on your PATH.\n", YELLOW))

    display, run = fill_placeholders(entry["cmd"])
    if display is None:
        return

    print("\n" + c(display, BOLD + ";" + GREEN) + "\n")
    while True:
        act = input(f"  {c('[r]', YELLOW)}un  {c('[c]', YELLOW)}opy  {c('[b]', YELLOW)}ack  > ").strip().lower()
        if act in ("r", "run"):
            print()
            try:
                subprocess.run(run, shell=True)
            except KeyboardInterrupt:
                print(c("\nInterrupted.", RED))
            input(c("\nPress Enter to return to the menu...", DIM))
            return
        if act in ("c", "copy"):
            ok = copy_to_clipboard(display)
            print(c("Copied." if ok else "No clipboard tool found (pbcopy/wl-copy/xclip).", GREEN if ok else RED))
        elif act in ("b", "back", ""):
            return


def main():
    cfg = load_config()
    categories = list(cfg.keys())
    while True:
        i = choose("Sup creep. What are we looking for:", categories, back_label="Exit")
        if i is None:
            return
        cat = categories[i]
        tools = list(cfg[cat].keys())
        while True:
            j = choose(f"{cat}: choose a program", tools, crumbs=cat)
            if j is None:
                break
            tool = tools[j]
            entries = cfg[cat][tool]
            while True:
                labels = [f"{e['cmd']}\n      {c(e['desc'], DIM)}" for e in entries]
                k = choose(f"{tool}: choose a command", labels, crumbs=f"{cat} > {tool}")
                if k is None:
                    break
                command_screen(tool, entries[k], f"{cat} > {tool}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
