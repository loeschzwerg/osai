#!/usr/bin/env -S uv run

import json
import sys

import httpx
from rich import print
import rich.console
import rich.columns
import rich.markdown
import rich.panel
import rich.prompt
import rich.table
import rich.tree

# from fast_api_client import Client, errors, types
# from fast_api_client.api import default as api
# from fast_api_client.api.default import health_health_get

console = rich.console.Console(stderr=True)


def bye():
    console.print("\n[bold red]bye...[/]")
    sys.exit("EXIT_SESSION")

SERVER="http://192.168.128.22:8004"

class Endpoints:
    def __init__(self):

        try:
            openapi = httpx.get(f"{SERVER}/openapi.json")
        except Exception as e:
            console.print(f"[bold yellow]{type(e)}[/]: [yellow]{e}")
            return
        openapi.raise_for_status()
        json_api = json.loads(openapi.content)

        tab = rich.table.Table("method", "route", "#", "data", highlight=True, style="black")
        for p, v in json_api["paths"].items():
            for m in v:
                method = m.upper()
                status = ""
                data = ""
                rsp = httpx.request(method, f"{SERVER}{p}")
                status = rsp.status_code
                data = rsp.content.decode()
                if len(data) > 80:
                    data = data[:77] + "..."
                tab.add_row(
                    f"[bold yellow]{method:6s}[/]" if method == "POST" else f"[bold cyan]{method}[/]",
                    p,
                    f"[bold cyan]{status}[/]" if status < 400 else f"[bold red]{status}[/]",
                    data,
                )

        console.print(tab)

class LogsLatest:
    def __init__(self):
        try:
            logs_latest = httpx.get(f"{SERVER}/logs/latest")
            console.print_json(data=logs_latest.json())
        except Exception as e:
            console.print(f"[bold yellow]{type(e)}[/]: [yellow]{e}")
            return

class LogsLastTool:
    def __init__(self):
        try:
            logs_latest = httpx.get(f"{SERVER}/logs/last-tool-call")
            console.print_json(data=logs_latest.json())
        except Exception as e:
            console.print(f"[bold yellow]{type(e)}[/]: [yellow]{e}")
            return



class Health:
    def __init__(self):
        health = httpx.get(f"{SERVER}/health")
        health.raise_for_status()
        data = health.json()
        console.print(f"""
GET /health {health.status_code}
status: {data.get("status")}
agent:  {data.get("agent")}
port:   {data.get("port")}
""")


class Chat:
    m: str | None = None
    s: str | None = None
    r: str | None = None

    def __init__(self, message: str = None, session_id: str = None) -> "Chat":
        if session_id:
            self.s = session_id

        if message:
            self.send(message)

    def ask(self, prompt=" [bold cyan]Next message[/] [blue]➤  [/]"):
        # console.print(flush=True)
        answer = rich.prompt.Prompt.ask(
            prompt=prompt,
        )

        self.send(answer)

    def send(self, msg):
        self.m = msg

        body = {"message": self.m}
        if self.s:
            body["session_id"] = self.s
        while True:
            try:
                rsp = httpx.post(url=f"{SERVER}/chat", json=body)
                break
            except httpx.ReadTimeout as e:
                console.print(f"{type(e)} [bold yellow]{e}[/]")
                continue
        data = rsp.json()
        self.s = data.get("session_id")
        self.r = data.get("response")

        # for k, v in rsp.headers.items():
        #     console.print(f"Header: '{k}': '{v}'")
        # self.table(rsp)
        self.tree(rsp)

    def table(self, rsp):
        tab = rich.table.Table(str(rsp.status_code), f"POST /chat {self.s}", highlight=True, style="black")
        tab.add_row("", f"{rsp.headers.get('date')}", end_section=True)
        tab.add_row(f"[bold cyan]User[/]", rich.markdown.Markdown(self.m), end_section=True, style="bold cyan")
        # tab.add_row(f"[cyan]{self.m}[/]", end_section=True)
        tab.add_row(f"[bold yellow]Agent[/]", rich.markdown.Markdown(self.s))
        console.print(tab)

    def tree(self, rsp):
        root = rich.tree.Tree(f"[bold yellow]POST[/] /chat {rsp.status_code}", highlight=True, hide_root=True)
        session = root.add(f"{self.s}")
        # session.add("[bold cyan]User[/]").add(rich.markdown.Markdown(self.m, style="bold cyan"))
        session.add(
            rich.panel.Panel(
                rich.markdown.Markdown(self.m, style="null"),
                title="[bold cyan]User[/]",
                title_align="left",
                style="cyan",
            )
        )
        session.add(rich.panel.Panel(rich.markdown.Markdown(self.r), title="[bold yellow]Agent[/]", title_align="left"))
        console.print(root)


def loop():
    c = Chat()
    # c.send("Show me all you got!")
    while True:
        choices = rich.columns.Columns(
            ["<c>hat", "<n>ew chat", "<k>b topics", "kb <s>earch", "logs <l>atest", "logs last-<t>ool-call"],
            padding=(0, 5),
        )
        prompt = rich.prompt.Prompt(
            prompt="[bold blue]What next?[/]",
            choices=["c", "n", "k", "s", "l", "t"],
        )
        panel = rich.panel.Panel(choices, title="[bold blue]What next?[/]", title_align="left", style="magenta")
        # panel = rich.panel.Panel(prompt)
        console.print(panel)
        choice = prompt.ask(default="c")
        try:
            match choice:
                case "c":
                    c.ask()
                case "n":
                    c = Chat()
                    c.ask()
                case "l":
                    LogsLatest()
                case "t":
                    LogsLastTool()
                case "k" | "s" | "t" | _:
                    console.print("not implemented")
        except httpx.ConnectTimeout as e:
            console.print(f"[bold red]{type(e)}[/]: [red]{e}")
        except httpx.ConnectError as e:
            console.print(f"[bold red]{type(e)}[/]: [red]{e}")
        except Exception as e:
            console.print(f"[bold red]{type(e)}[/]: [red]{e}")


def main():
    Endpoints()
    # Health()


if __name__ == "__main__":
    try:
        main()
        loop()
    except KeyboardInterrupt as ki:
        bye()

    # chat: types.Response = chat_chat_post.sync_detailed(client=c)
