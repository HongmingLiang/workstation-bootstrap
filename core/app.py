from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Callable
from shutil import which
from subprocess import run
from json import loads

COMMANDS_FILE_PATH = Path(__file__).parent.parent / 'app_lists' / "commands.json"

COMMANDS_DICT: dict[str, list[str]] = loads(COMMANDS_FILE_PATH.read_text(encoding="utf-8"))

@dataclass
class App:
    name: str
    commands: list[str] = field(default_factory=list, init=False)

    def __post_init__(self):
        """Set command names automatically after initialization."""
        if not self.commands:
            self.commands = self._get_commands()

    def _get_commands(self) -> list[str]:
        """Derive the command name from the app name."""
        commands = COMMANDS_DICT[self.name.lower()] if self.name.lower() in COMMANDS_DICT else [self.name.lower()]
        return commands

    def is_installed(self) -> bool:
        """Check if the app is installed by verifying if the command exists in PATH."""
        return which(self.commands[0]) is not None


class AppRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, type[App]] = {}

    def register(self, name: str) -> Callable:
        def wrapper(app: type[App]):
            self._registry[name] = app
            return app
        return wrapper

    def get_app(self, name: str) -> type[App]:
        if name not in self._registry:
            raise ValueError(f"App '{name}' is not registered.")
        return self._registry[name]

    def get_all_apps(self) -> list[str]:
        return list(self._registry.keys())

APP_REGISTRY = AppRegistry()

@APP_REGISTRY.register("neovim")
class Neovim(App):
    def __init__(self, name: str = "neovim") -> None:
        super().__init__(name=name)

    def install(self, force_reinstall: bool = False) -> bool:
        if which('brew') is not None:
            print("[INFO] Installing Neovim via Homebrew...")
            install_cmd = ['brew', 'install', 'neovim']
            if force_reinstall:
                install_cmd.append('--force')
            run(install_cmd, check=True)
            return True
        bin_path = Path.home() / '.local' / 'bin' / 'nvim'
        if bin_path.exists() and not force_reinstall:
            print(f"[INFO] Neovim is already installed at {bin_path}.")
            return True
        bin_path.parent.mkdir(parents=True, exist_ok=True)
        install_cmd = f'curl -L https://github.com/neovim/neovim/releases/latest/download/nvim-linux-$(uname -m).appimage -o {str(bin_path)}'
        run(install_cmd, shell=True, check=True)
        run(f'chmod +x {str(bin_path)}', shell=True, check=True)
        print(f"[INFO] Neovim installed successfully at {bin_path}.")
        return True
