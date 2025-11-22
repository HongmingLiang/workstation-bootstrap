#!/usr/bin/env python3
from pathlib import Path
from core.context import EnvironmentContext
from core.manager import PACKAGE_MANAGER_REGISTRY
from core.app import App, APP_REGISTRY
from utils.check_git import ensure_git_installed

APP_LISTS_DIR = Path(__file__).parent / 'app_lists'

def parse_args():
    from argparse import ArgumentParser
    p = ArgumentParser()
    p.add_argument('-m','--mode', choices=['auto'] + PACKAGE_MANAGER_REGISTRY.get_all_managers(), default='auto', help=f'Installation mode: {["auto"] + PACKAGE_MANAGER_REGISTRY.get_all_managers()}.')
    p.add_argument('-f','--force-reinstall', action='store_true', help='Force reinstall packages.')
    p.add_argument('-a','--app-list', type=str, choices=[p.stem for p in APP_LISTS_DIR.glob('*.txt')]+['full'], default=None, help='Specify which app list to install (e.g., minimal, full).')
    p.add_argument('-c', '--custom-bin-path', type=str, default=None, help='Custom binary path for Mamba binary path.')
    return p.parse_args()

def choose_mode(env_ctx: EnvironmentContext) -> str:
    if env_ctx.has_sudo:
        return 'brew'
    else:
        return 'mamba'

def get_app_list_from_file(file_path: Path) -> list[str]:
    app_names = [app.strip() for app in file_path.read_text().splitlines() if app.strip() and not app.startswith('#')]
    return app_names

def main() -> None:
    args = parse_args()
    args_mode: str = args.mode
    args_force_reinstall: bool = args.force_reinstall
    args_app_list: str | None = args.app_list
    args_custom_bin_path: str | None = args.custom_bin_path

    # --- check git ---
    print("\n=== Checking Git Installation ===")
    if not ensure_git_installed():
        raise RuntimeError("Git is required but could not be installed. Please install it manually.")

    # --- detect environment ---
    if args_mode == 'mamba':
        env_ctx = EnvironmentContext(has_sudo=False, home=Path.home(), local_bin=Path.home() / '.local' / 'bin')
    else:
        env_ctx = EnvironmentContext.detect()
    if not env_ctx.local_bin.exists():
        print("[INFO] Local bin directory is missing. Creating local bin directory at:", env_ctx.local_bin)
        env_ctx.local_bin.mkdir(parents=True, exist_ok=True)
    mode = choose_mode(env_ctx) if args.mode == 'auto' else args.mode
    env_ctx.print_info()

    # --- app list ---
    if args_app_list is None:
        raise ValueError("Please specify an app list using --app-list.")
    app_name_list: list[str] = []
    if args_app_list == 'full':
        for app_list_file in APP_LISTS_DIR.glob('*.txt'):
            app_name_list += get_app_list_from_file(app_list_file)
    else:
        app_name_list += get_app_list_from_file(APP_LISTS_DIR / f"{args_app_list}.txt")
    print("[INFO] App names to install:", app_name_list)

    # --- determine apps to install ---
    manager_install_apps: list[App] = []
    for app_name in app_name_list:
        # Firstly, check if the app is registered
        try:
            app = APP_REGISTRY.get_app(app_name.lower())(name=app_name)
            if app.is_installed() and not args_force_reinstall:
                print(f"[INFO] App '{app_name}' is already installed. Skipping installation.")
                continue
            if not hasattr(app, 'install') or not callable(getattr(app, 'install')):
                print(f"[INFO] App '{app_name}' does not have a custom install method. Using package manager installation.")
                manager_install_apps.append(app)
                continue
            # if it has a custom install method, use it
            print(f"[INFO] Installing '{app_name}' via its custom install method.")
            if not app.install(force_reinstall=args_force_reinstall): # pyright: ignore[reportAttributeAccessIssue]
                print(f"[WARNING] App '{app_name}' installed via custom method failed or is not installed. Using package manager installation as fallback.")
                manager_install_apps.append(app)
            continue
        except ValueError as e:
            print(f"[INFO] App '{app_name}' is not registered. Using package manager installation as fallback.")
            app = App(name=app_name)
            if app.is_installed() and not args_force_reinstall:
                print(f"[INFO] App '{app_name}' is already installed. Skipping installation.")
                continue
            manager_install_apps.append(app)
    if not manager_install_apps:
        print("[INFO] All specified apps are already installed. No installation needed.")
        return
    print("[INFO] Manager install apps:", [app.name for app in manager_install_apps])

    # --- set manager ---
    if args_custom_bin_path is not None and mode == 'mamba':
        manager = PACKAGE_MANAGER_REGISTRY.get_manager('mamba')(context=env_ctx, name=mode, custom_bin_path=Path(args_custom_bin_path)) # pyright: ignore[reportCallIssue]
    else:
        manager = PACKAGE_MANAGER_REGISTRY.get_manager(mode)(context=env_ctx, name=mode)

    if not manager.ensure_available():
        raise RuntimeError(f"Failed to ensure package manager '{mode}' is available.")

    # --- install apps ---
    manager.install_package(packages_list=manager_install_apps, force_reinstall=args_force_reinstall)

if __name__ == "__main__":
    main()
