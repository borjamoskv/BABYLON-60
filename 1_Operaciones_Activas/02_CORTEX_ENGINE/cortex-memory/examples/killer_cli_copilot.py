#!/usr/bin/env python3
import sys
import os
import argparse

# Add SDK path to sys.path to run without installing
sys.path.append(os.path.join(os.path.dirname(__file__), "../sdk/python"))
from cortex import CortexClient

def main():
    parser = argparse.ArgumentParser(description="Cortex Memory CLI Copilot — Demo Use Case")
    subparsers = parser.add_subparsers(dest="command", help="Subcommand to run")

    # Remember command
    parser_remember = subparsers.add_parser("remember", help="Save a memory fact for the agent")
    parser_remember.add_argument("content", type=str, help="The fact/context to store")
    parser_remember.add_argument("--user", type=str, default="dev_user", help="User ID")
    parser_remember.add_argument("--agent", type=str, default="copilot_v1", help="Agent ID")

    # Query command
    parser_query = subparsers.add_parser("query", help="Query memories using vector search")
    parser_query.add_argument("query", type=str, help="Search query")
    parser_query.add_argument("--user", type=str, default="dev_user", help="User ID")

    args = parser.parse_args()

    client = CortexClient()

    if args.command == "remember":
        print(f"[*] Storing memory for user '{args.user}' / agent '{args.agent}'...")
        try:
            res = client.add(args.user, args.agent, args.content)
            print(f"[+] Stored! Server response: {res}")
        except Exception as e:
            print(f"[!] Error connecting to Cortex server: {e}")
            print("[!] Make sure the docker containers are running (`docker compose -f docker/docker-compose.yml up`)")

    elif args.command == "query":
        print(f"[*] Querying vector memories for user '{args.user}' with query: '{args.query}'...")
        try:
            res = client.query(args.user, args.query)
            results = res.get("results", [])
            if not results:
                print("[-] No matching memories found.")
            else:
                print(f"[+] Found {len(results)} relevant memories:")
                for idx, content in enumerate(results, 1):
                    print(f"  {idx}. {content}")
        except Exception as e:
            print(f"[!] Error connecting to Cortex server: {e}")
            print("[!] Make sure the docker containers are running (`docker compose -f docker/docker-compose.yml up`)")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
