#!/usr/bin/env python3
from subprocess import run
from abc import ABC, abstractmethod
from typing import Callable


class Installable(ABC):
    class InstallMethodRegistry:
        def __init__(self) -> None:
            self.methods: dict[str, Callable] = {}

        def register(self, name: str) -> Callable:
            def decorator(func: Callable) -> Callable:
                self.methods[name] = func
                return func

            return decorator

        def get_method(self, name: str) -> Callable | None:
            return self.methods.get(name)

    def __init__(self, name: str, version: str, commands: list[str]) -> None:
        self.name = name
        self.version = version
        self.commands = commands
        self.methods_registry = self.InstallMethodRegistry()

    @abstractmethod
    def is_installed(self) -> bool:
        return (
            run(
                f'$SHELL -i -c "type {self.name}"', shell=True, capture_output=True
            ).returncode
            == 0
        )

    @abstractmethod
    def install(self, force: bool = False) -> bool: ...


class App(Installable):
    def __init__(self, name: str, version: str, commands: list[str]) -> None:
        super().__init__(name, version, commands)

    def __init__commands(self, commands: list[str]) -> list[str]:
        return commands

    def is_installed(self) -> bool:
        return super().is_installed()

    def install(self, force: bool = False) -> bool:
        # TODO: 实现安装逻辑
        return True
