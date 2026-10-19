from app.menu import MenuItem, MenuTree

BACK_ID = "nav:back:"
MAIN_ID = "nav:main"


def callback_button(title: str, payload: str) -> dict:
    return {"type": "callback", "text": title, "payload": payload}


def link_button(title: str, url: str) -> dict:
    return {"type": "link", "text": title, "url": url}


def keyboard_for(item: MenuItem, tree: MenuTree) -> list[dict]:
    rows: list[list[dict]] = []
    if item.type == "submenu":
        rows.extend([[callback_button(child.title, f"go:{child.id}")] for child in item.items])
    if item.type == "answer":
        rows.extend([[link_button(link.title, link.url)] for link in item.links])
    if item.id != "main":
        navigation = []
        parent = tree.parent(item.id)
        if parent and parent != "main":
            navigation.append(callback_button(tree.document.back_button, f"{BACK_ID}{parent}"))
        navigation.append(callback_button(tree.document.main_menu_button, MAIN_ID))
        rows.append(navigation)
    return [{"type": "inline_keyboard", "payload": {"buttons": rows}}] if rows else []

