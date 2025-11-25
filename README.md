# Workstation Bootstrap

Automated app installer for personal workstation setup using Python (with Homebrew or Miniforge/Mamba as package manager).

## Features

- Batch install of CLI/dev tools via Python (using Homebrew or Miniforge/Mamba as package manager)
- Auto-detect and install Git on major Linux distributions
- Install by list: `minimal`, `optional`, or `full`
- Smart package manager selection based on environment

## Repository Layout

```plaintext
workstation-bootstrap/
├── README.md
├── install.py             # Entry point
├── app_lists              # App lists (*.txt)
│   ├── minimal.txt          # Base set: vim, fzf, yazi, ...
│   ├── optional.txt         # Extras: tmux, lazygit, neovim
│   └── commands.json        # Command mappings
├── core                   # Environment, package managers, registry
│   ├── app.py
│   ├── context.py
│   └── manager.py
└── utils                  # Git check/installer
    ├── check_git.py
    └── check_git.sh
```

## Quick Start

```bash
git clone https://github.com/HongmingLiang/workstation-bootstrap.git
cd workstation-bootstrap

# Auto mode + minimal set
python3 install.py --mode auto --app-list minimal

# Install everything from all list files
python3 install.py --mode auto --app-list full
```

## Installation

### Modes and Selection Logic

- `auto`: chooses `brew` if sudo is available, otherwise `mamba`
- `brew`: uses Homebrew if present; installs it if missing
- `mamba`: installs Miniforge if missing, then uses an environment named `apps`

### Arguments

- `--mode {auto,brew,miniforge}`: default `auto`
- `--app-list {minimal,optional,full}`: required; `full` installs all lists
- `--force-reinstall`: reinstall even if command already exists in PATH
- `--custom-bin-path <path>`: custom Mamba binary path when using `miniforge`

### Examples

```bash
# Auto mode + minimal set
python3 install.py --mode auto --app-list minimal

# Install everything from all list files
python3 install.py --mode auto --app-list full

# Force reinstall optional set via miniforge
python3 install.py --mode miniforge --app-list optional --force-reinstall

# Use custom Mamba path with miniforge mode
python3 install.py --mode miniforge --app-list minimal --custom-bin-path /custom/mamba
```

### How It Works

1. Ensures Git is available (`utils/check_git.py` supports Debian/Fedora/Arch/Alpine/SUSE)
2. Detects environment (`core/context.py`) to decide package manager
3. Loads apps from `app_lists/*.txt` (ignores blank lines and comments)
4. Skips already installed apps unless `--force-reinstall` is used
5. Package managers:
	 - Homebrew: `brew install`
	 - Miniforge (Mamba): installs Miniforge if missing, creates `apps` env, installs there, and tries to symlink binaries into `~/.local/bin`

## Update & Maintain

To add more apps:
1. Append package names to the desired `*.txt` list in `app_lists/`
2. Rerun the installer: `python3 install.py --mode auto --app-list <list-name>`

## Troubleshooting

| Issue | Fix |
|------|-----|
| Git not auto-installed | Install via your distro's package manager, then rerun the app installer |
| Miniforge install fails | Check network and rerun; verify `mamba` binary path if using `--custom-bin-path` |
