from abc import ABC, abstractmethod
from typing import Iterable
from pathlib import Path
from subprocess import run
from typing import Optional, Callable
from core.context import EnvironmentContext
from core.app import App

class PackageManager(ABC):
    def __init__(self, context: EnvironmentContext, name: str):
        self.context: EnvironmentContext = context
        self.name: str = name
        self.is_installed: bool = False

    @abstractmethod
    def _install_package_manager(self):
        """Install the underlying package manager."""
        if self.is_installed:
            raise RuntimeError(f"{self.__class__.__name__} is already installed.")
    
    @abstractmethod
    def ensure_available(self) -> bool:
        """Install underlying package manager if missing."""
        raise NotImplementedError

    @abstractmethod
    def install_package(self, packages_list: list[App], force_reinstall: bool = False):
        """Install a package or a collection of packages."""
        raise NotImplementedError
    
    @abstractmethod
    def _link_binary(self, app: App) -> None:
        """Link a binary from source to target location."""
        raise NotImplementedError

class PackageManagerRegistry:
    def __init__(self) -> None:
        self._registry: dict[str, type[PackageManager]] = {}

    def register(self, name: str) -> Callable:
        def wrapper(pm_class: type[PackageManager]):
            self._registry[name] = pm_class
            return pm_class
        return wrapper

    def get_manager(self, name: str) -> type[PackageManager]:
        if name not in self._registry:
            raise ValueError(f"Package manager '{name}' is not registered.")
        return self._registry[name]
    
    def get_all_managers(self) -> list[str]:
        return list(self._registry.keys())

PACKAGE_MANAGER_REGISTRY = PackageManagerRegistry()

@PACKAGE_MANAGER_REGISTRY.register("brew")
class Homebrew(PackageManager):
    def __init__(self, context: EnvironmentContext, name: str):
        super().__init__(context, name)

    def _install_package_manager(self) -> bool:
        super()._install_package_manager()
        if not self.context.has_sudo:
            print("[WARNING] Sudo privileges are required to install Homebrew.")

        print("[INFO] Installing Homebrew...")
        install_cmd: str = 'NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
        run(install_cmd, shell=True, check=True)
        self.context.has_sudo = True  # Assume sudo is now available after installation
        run('source ~/.profile', shell=True, check=True)
        print("[INFO] Homebrew installation completed.")
        self.is_installed = True
        return True

    def ensure_available(self) -> bool:
        from shutil import which
        if which('brew') is not None:
            print("[INFO] Homebrew is already installed. Found at:", which('brew'))
            self.is_installed = True
            return True

        print("[INFO] Homebrew not found. Proceeding with installation.")
        return self._install_package_manager()

    def install_package(self, packages_list: list[App], force_reinstall: bool = False) -> None:
        if not self.is_installed:
            raise RuntimeError("Homebrew is not installed. Call ensure_available() first.")
        
        print("[INFO] Package(s) installed via Homebrew:", packages_list)
        packages_names: list[str] = [app.name for app in packages_list]
        install_cmd: list[str] = ['brew', 'install', '--force'] if force_reinstall else ['brew', 'install']
        install_cmd = install_cmd + packages_names
        run(install_cmd, check=True)
        print("[INFO] Package installation completed.")

    def _link_binary(self, app: App) -> None:
        print("[WARNING] Linking binaries via Homebrew is not implemented.")

@PACKAGE_MANAGER_REGISTRY.register("mamba")
class Miniforge(PackageManager):
    def __init__(self, context: EnvironmentContext, name: str, custom_bin_path: Optional[Path] = None):
        super().__init__(context, name)
        self.bin_path: Path | None = custom_bin_path
        self.apps_env_name: str = "apps"

    def _install_package_manager(self) -> bool:
        super()._install_package_manager()
        print("[INFO] Installing Mamba (Miniforge)...")
        install_script: str = 'wget -O Miniforge3.sh "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"'
        run(install_script, shell=True, check=True)
        run("chmod +x Miniforge3.sh", shell=True, check=True)
        run(f'bash Miniforge3.sh -b -p {str(self.context.home / "miniforge3")}', shell=True, check=True)
        run("rm Miniforge3.sh", shell=True, check=True)
        self.bin_path = self.context.home / 'miniforge3' / 'bin' / 'mamba'
        self.is_installed = True
        print("[INFO] Mamba installation completed. Mamba binary at:", str(self.bin_path))
        return True

    def ensure_available(self) -> bool:
        if self.bin_path is not None and self.bin_path.exists():
            print("[INFO] Mamba is already installed. Found at:", self.bin_path)
            self.is_installed = True
            return True
        possible_dir: list[Path] = [
            self.context.home / 'miniforge3' / 'bin' / 'mamba',
            Path('/opt/miniforge3/bin/mamba'),
        ]
        print("[INFO] Custom binary path not provided or does not exist.")
        print("[INFO] Checking standard installation directories:", possible_dir)
        for dir in possible_dir:
            if dir.exists():
                print("[INFO] Mamba is already installed. Found at:", dir)
                self.bin_path = dir
                self.is_installed = True
                return True
        #end of for
        print("[INFO] Mamba not found in standard locations. Proceeding with installation.")
        return self._install_package_manager()
    
    def _check_env_exists(self) -> bool:
        if not self.is_installed:
            raise RuntimeError("Mamba is not installed. Call ensure_available() first.")
        return run(f'{str(self.bin_path)} env list | grep {self.apps_env_name} -w', shell=True, capture_output=True).returncode == 0
    
    def _create_env(self) -> None:
        if not self.is_installed:
            raise RuntimeError("Mamba is not installed. Call ensure_available() first.")
        print(f"[INFO] Creating Mamba environment '{self.apps_env_name}'...")
        run(f'{str(self.bin_path)} create -n {self.apps_env_name} -y', shell=True, check=True)
        print(f"[INFO] Mamba environment '{self.apps_env_name}' created successfully.")

    def install_package(self, packages_list: list[App], force_reinstall: bool = False) -> None:
        if not self.is_installed:
            raise RuntimeError("Mamba is not installed. Call ensure_available() first.")
        if self._check_env_exists():
            print(f"[INFO] Mamba environment '{self.apps_env_name}' already exists.")
        else:
            print(f"[INFO] Mamba environment '{self.apps_env_name}' does not exist. Creating it now.")
            self._create_env()
        packages_names: list[str] = [app.name for app in packages_list]
        print("[INFO] Package(s) installed via mamba:", packages_list)
        install_cmd = [str(self.bin_path), 'install', '-n', self.apps_env_name, '-y','--force-reinstall'] if force_reinstall else [str(self.bin_path), 'install', '-n', self.apps_env_name, '-y']
        install_cmd = install_cmd + packages_names
        run(install_cmd, check=True)
        print("[INFO] Package installation completed.")
        print("[INFO] Linking binaries to local bin directory...")
        for app in packages_list:
            self._link_binary(app)

    def _link_binary(self, app: App) -> None:
        for bin_name in app.commands:
            link_path: Path = self.context.local_bin / bin_name
            if link_path.exists():
                print(f"[INFO] Binary '{bin_name}' is already linked at {link_path}.")
                return
            source_path: Path = self.bin_path.parent.parent / 'envs' / self.apps_env_name / 'bin' / bin_name # pyright: ignore[reportOptionalMemberAccess]
            if not source_path or not source_path.exists():
                print(f"[WARNING] Source binary '{bin_name}' does not exist at {source_path}. Cannot create link. SKIPPING.")
                return
            print(f"[INFO] Linking binary '{bin_name}' from {source_path} to {link_path}...")
            try:
                link_path.symlink_to(source_path)
                print(f"[LINK] {link_path} -> {source_path}")
            except Exception as e:
                print(f"[ERROR] Failed to link binary '{bin_name}': {e}")
                print("[INFO] Continuing with the next binary...")
