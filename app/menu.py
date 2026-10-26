import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError, model_validator


class Link(BaseModel):
    title: str = Field(min_length=1)
    url: str = Field(pattern=r"^https?://")


class MenuItem(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9_]{1,40}$")
    title: str = Field(min_length=1)
    type: Literal["submenu", "answer"]
    text: str | None = None
    links: list[Link] = []
    items: list["MenuItem"] = []

    @model_validator(mode="after")
    def validate_content(self) -> "MenuItem":
        if self.type == "submenu" and not self.items:
            raise ValueError("submenu must contain items")
        if self.type == "answer" and not self.text:
            raise ValueError("answer must contain text")
        if self.type == "answer" and self.items:
            raise ValueError("answer cannot contain items")
        return self


class MenuDocument(BaseModel):
    welcome: str = Field(min_length=1)
    unknown_message: str = Field(min_length=1)
    stale_callback_message: str = Field(min_length=1)
    start_button: str = Field(min_length=1)
    back_button: str = Field(min_length=1)
    main_menu_button: str = Field(min_length=1)
    main: MenuItem

    @model_validator(mode="after")
    def main_is_submenu(self) -> "MenuDocument":
        if self.main.id != "main" or self.main.type != "submenu":
            raise ValueError("main must be a submenu with id main")
        return self


@dataclass(frozen=True)
class MenuTree:
    document: MenuDocument
    by_id: dict[str, MenuItem]
    parent_id: dict[str, str]

    def get(self, item_id: str) -> MenuItem | None:
        return self.by_id.get(item_id)

    def parent(self, item_id: str) -> str | None:
        return self.parent_id.get(item_id)


def load_menu(path: Path) -> MenuTree:
    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
        document = MenuDocument.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise RuntimeError(f"Invalid menu JSON at {path}: {exc}") from exc
    by_id: dict[str, MenuItem] = {}
    parents: dict[str, str] = {}

    def walk(item: MenuItem, parent: str | None = None) -> None:
        if item.id in by_id:
            raise RuntimeError(f"Invalid menu JSON at {path}: duplicate id {item.id}")
        by_id[item.id] = item
        if parent:
            parents[item.id] = parent
        for child in item.items:
            walk(child, item.id)

    walk(document.main)
    return MenuTree(document, by_id, parents)

