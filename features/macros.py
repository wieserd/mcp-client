"""Macro management and command expansion for the MCP client."""

from __future__ import annotations
import re


class MacroManager:
    """Stores and expands user-defined macros and aliases."""

    def __init__(self, initial_macros: dict[str, str] | None = None):
        self._macros: dict[str, str] = {}
        if initial_macros:
            for k, v in initial_macros.items():
                self.set_macro(k, v)

    def set_macro(self, name: str, template: str) -> None:
        """Adds or updates a macro."""
        cleaned_name = name.strip().lstrip("/").lower()
        if cleaned_name:
            self._macros[cleaned_name] = template.strip()

    def remove_macro(self, name: str) -> bool:
        """Removes a macro by name. Returns True if found and removed."""
        cleaned_name = name.strip().lstrip("/").lower()
        return self._macros.pop(cleaned_name, None) is not None

    def get_macro(self, name: str) -> str | None:
        """Gets the expansion template for a macro."""
        cleaned_name = name.strip().lstrip("/").lower()
        return self._macros.get(cleaned_name)

    def list_macros(self) -> dict[str, str]:
        """Returns a copy of all registered macros."""
        return dict(self._macros)

    def expand(self, name: str, args: list[str]) -> list[str]:
        """
        Expands a macro into one or more runnable command strings.
        Supports parameter replacement ($1, $2, ..., $*) and multiple
        commands separated by semicolons (;).
        """
        template = self.get_macro(name)
        if template is None:
            return []

        expanded = template
        all_args_str = " ".join(args)

        # Replace $* or $@ with all arguments joined
        expanded = re.sub(r"\$(\*|@)", all_args_str, expanded)

        # Replace numbered parameters $1, $2, etc.
        for i, arg in enumerate(args, start=1):
            expanded = re.sub(rf"\${i}\b", arg, expanded)

        # If no placeholder was present and args exist, append them
        if not re.search(r"\$\d+", template) and not re.search(r"\$(\*|@)", template):
            if args:
                expanded = f"{expanded} {all_args_str}"

        # Clean any unreplaced placeholders like $2, $3 to empty string
        expanded = re.sub(r"\$\d+\b", "", expanded)

        # Split commands separated by ';' unless escaped
        commands = [cmd.strip() for cmd in expanded.split(";") if cmd.strip()]
        return commands
