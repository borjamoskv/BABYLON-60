import threading
from textual.app import App, ComposeResult
from textual.widgets import Static, Header, Footer
from textual.containers import Horizontal
from textual.reactive import reactive
from pynput import keyboard

class AgentStatusWidget(Static):
    agent_id = reactive("AGENT_01")
    status = reactive("⚪ IDLE")

    def render(self) -> str:
        color_map = {
            "🔵 INFERRING": "blue",
            "🟢 DONE": "green",
            "🟠 YIELD": "yellow",
            "🔴 PANIC": "red",
            "⚪ IDLE": "white"
        }
        color = color_map.get(self.status, "white")
        return f"[{color}]{self.agent_id}\n\n{self.status}[/{color}]"

class CodexVirtualHUD(App):
    CSS = """
    AgentStatusWidget {
        width: 1fr;
        height: 1fr;
        border: solid green;
        content-align: center middle;
        text-style: bold;
    }
    #thermal_status {
        dock: top;
        height: 3;
        content-align: center middle;
        background: $boost;
        color: yellow;
        text-style: bold;
    }
    """
    
    thermal_depth = reactive(1)
    active_agent_idx = reactive(0)
    
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Static(id="thermal_status")
        with Horizontal():
            yield AgentStatusWidget(id="agent_0")
            yield AgentStatusWidget(id="agent_1")
            yield AgentStatusWidget(id="agent_2")
        yield Footer()

    def on_mount(self) -> None:
        self.update_thermal_status()
        self.highlight_active_agent()
        
        # Start the global pynput listener in a background thread
        self.start_global_listener()

    def increase_depth(self):
        if self.thermal_depth < 3:
            self.thermal_depth += 1
        self.update_thermal_status()

    def decrease_depth(self):
        if self.thermal_depth > 1:
            self.thermal_depth -= 1
        self.update_thermal_status()
        
    def switch_agent(self):
        self.active_agent_idx = (self.active_agent_idx + 1) % 3
        self.highlight_active_agent()

    def update_thermal_status(self):
        depth_map = {1: "L1 - FLASH LITE (Fast)", 2: "L2 - FLASH (Balanced)", 3: "L3 - PRO (Deep Reasoning)"}
        label = depth_map.get(self.thermal_depth, "MAX DEPTH")
        self.query_one("#thermal_status", Static).update(f"ROTARY DIAL [Depth]: {label}")

    def highlight_active_agent(self):
        for i in range(3):
            widget = self.query_one(f"#agent_{i}", AgentStatusWidget)
            if i == self.active_agent_idx:
                widget.styles.border = ("double", "cyan")
                widget.status = "🔵 INFERRING"
            else:
                widget.styles.border = ("solid", "green")
                widget.status = "⚪ IDLE"

    def start_global_listener(self):
        def on_activate_dial_up():
            self.call_from_thread(self.increase_depth)

        def on_activate_dial_down():
            self.call_from_thread(self.decrease_depth)

        def on_activate_joystick():
            self.call_from_thread(self.switch_agent)

        def run_listener():
            # These global hotkeys require macOS Accessibility Permissions when run outside of active terminal
            with keyboard.GlobalHotKeys({
                '<shift>+<alt>+<up>': on_activate_dial_up,
                '<shift>+<alt>+<down>': on_activate_dial_down,
                '<alt>+j': on_activate_joystick
            }) as listener:
                listener.join()
                
        t = threading.Thread(target=run_listener, daemon=True)
        t.start()

if __name__ == "__main__":
    app = CodexVirtualHUD()
    app.run()
