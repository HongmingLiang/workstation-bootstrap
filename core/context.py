from subprocess import run
from dataclasses import dataclass
from pathlib import Path

@dataclass
class EnvironmentContext:
    has_sudo: bool
    home: Path
    local_bin: Path
    
    @classmethod
    def detect(cls) -> "EnvironmentContext":
        has_sudo = (run( 'sudo echo "detect sudo privileges" ' , shell=True ,capture_output=True).returncode == 0)
        home = Path.home()
        local_bin = home / '.local' / 'bin'
        if not local_bin.exists():
            print(f"[INFO] Local bin directory does not exist. Creating local bin directory at {local_bin}")
            local_bin.mkdir(parents=True, exist_ok=True)
        return cls(has_sudo=has_sudo, home=home, local_bin=local_bin)
    
    def print_info(self) -> None:
        print(f"[INFO] Environment Context: has_sudo={self.has_sudo}, home={self.home}, local_bin={self.local_bin}")
