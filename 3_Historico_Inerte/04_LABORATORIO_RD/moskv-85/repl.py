# MOSKV-85 SOVEREIGN REPL
# Author: Borja Moskv (borjamoskv)
# Reality Level: C5-REAL
# Version: 2.0.0 (Persistent History & AST Inspector)

import sys
import os
from moskv85 import Moskv85Interpreter

# Try loading readline with persistent history support
HISTORY_FILE = os.path.expanduser("~/.moskv85_history")
try:
    import readline
    if os.path.exists(HISTORY_FILE):
        readline.read_history_file(HISTORY_FILE)
    readline.set_history_length(1000)
except ImportError:
    readline = None

# ANSI colors for C5-REAL Industrial Noir aesthetic
COLOR_PROMPT = "\033[1;34mm85>\033[0m "
COLOR_STACK = "\033[1;30m -> Stack:\033[0m \033[32m{}\033[0m"
COLOR_ERROR = "\033[1;31m[ERROR]\033[0m \033[31m{}\033[0m\n"
COLOR_CLI = "\033[1;36m{}\033[0m"

def print_help():
    sys.stdout.write("\n=== MOSKV-85 REPL COMMANDS ===\n")
    sys.stdout.write("Type code to execute it on the Virtual Machine.\n")
    sys.stdout.write("Special CLI Commands:\n")
    sys.stdout.write(f"  {COLOR_CLI.format('.help')}    Show this command guide\n")
    sys.stdout.write(f"  {COLOR_CLI.format('.stack')}   Dump current stack explicitly\n")
    sys.stdout.write(f"  {COLOR_CLI.format('.memory')}  Dump current memory registers\n")
    sys.stdout.write(f"  {COLOR_CLI.format('.ast')} <code> Inspect AST translation without execution\n")
    sys.stdout.write(f"  {COLOR_CLI.format('.clear')}   Reset stack and memory\n")
    sys.stdout.write(f"  {COLOR_CLI.format('.exit')}    Halt and close REPL\n")
    sys.stdout.write("==============================\n\n")
    sys.stdout.flush()

def main():
    interpreter = Moskv85Interpreter()
    
    sys.stdout.write("==================================================\n")
    sys.stdout.write("  MOSKV-85 SOVEREIGN INTERACTIVE REPL v2.0\n")
    sys.stdout.write("  Creator: Borja Moskv (borjamoskv)\n")
    sys.stdout.write("  Reality level: C5-REAL\n")
    sys.stdout.write("  Type \".help\" for commands. Ctrl+D or \".exit\" to quit.\n")
    sys.stdout.write("==================================================\n\n")
    sys.stdout.flush()

    while interpreter.running:
        try:
            # Read
            try:
                line = input(COLOR_PROMPT)
            except EOFError:
                sys.stdout.write("\nExiting.\n")
                break
                
            stripped = line.strip()
            if not stripped:
                continue

            # Command Routing
            if stripped == ".exit" or stripped == ".quit":
                break
            elif stripped == ".help":
                print_help()
                continue
            elif stripped == ".stack":
                sys.stdout.write(f"Stack: {interpreter.stack}\n")
                sys.stdout.flush()
                continue
            elif stripped == ".memory":
                sys.stdout.write(f"Memory: {interpreter.memory}\n")
                sys.stdout.flush()
                continue
            elif stripped == ".clear":
                interpreter.stack.clear()
                interpreter.memory.clear()
                sys.stdout.write("State cleared.\n")
                sys.stdout.flush()
                continue
            elif stripped.startswith(".ast "):
                code_to_inspect = stripped[5:]
                try:
                    ast_repr = interpreter.compile_aot(code_to_inspect)
                    sys.stdout.write(f"Compiled AST: {ast_repr}\n")
                except Exception as e:
                    sys.stderr.write(COLOR_ERROR.format(str(e)))
                sys.stdout.flush()
                continue

            # Execute
            interpreter.execute_block(line)
            
            # Print state summary
            sys.stdout.write(COLOR_STACK.format(interpreter.stack) + "\n")
            sys.stdout.flush()

        except KeyboardInterrupt:
            sys.stdout.write("\nKeyboardInterrupt. Type \".exit\" to exit.\n")
            sys.stdout.flush()
        except Exception as e:
            sys.stderr.write(COLOR_ERROR.format(str(e)))
            sys.stderr.flush()

    # Save history on exit
    if readline:
        try:
            readline.write_history_file(HISTORY_FILE)
        except Exception:
            pass

if __name__ == "__main__":
    main()
