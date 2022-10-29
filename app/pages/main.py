from typing import Sequence

from markyp import ElementType
from markyp_bootstrap4 import colors, dropdowns, forms, navbars, navs, req
from markyp_bootstrap4.layout import container, margin
from markyp_html import block, inline, join, script, webpage as html_webpage


class __defaults:
    chat_id_input = "go-to-chat"
    collapse_id = "main-nabvar-collapse"
    user_dropdown = "user-dropdown"


def navigate_to_chat_script(*, chat_room_base_url: str) -> script:
    return script(
        "\n".join(
            (
                f"function navigateToChat(event) {{",
                f"    event.preventDefault();",
                f"    const searchInput = document.getElementById('{__defaults.chat_id_input}');",
                f"    const value = searchInput.value.trim();",
                f"    const match = value.match('^[a-zA-Z0-9-]+$');",
                f"    if (match) {{",
                f"        window.location.href = `{chat_room_base_url}/${{match[0]}}`;",
                f"    }}",
                f"}}",
            )
        )
    )


def main_page(
    *children: ElementType,
    brand="Lounge > Chat",
    page_title="Lounge > Chat",
    search_placeholder="Chat ID",
    go_to_chat="Go to chat!",
    logout_text="Log Out",
    chat_room_base_url: str,
    logout_url: str,
    user_name: str,
    user_email: str,
    javascript: Sequence[script] | None = None,
):
    return html_webpage(
        block.div(
            navbars.navbar(
                container(
                    navbars.brand(brand),
                    navbars.navbar_toggler(collapse_id=__defaults.collapse_id),
                    navbars.collapse(
                        forms.inline_form(
                            forms.input_(id=__defaults.chat_id_input, type_="search", placeholder=search_placeholder),
                            forms.submit_button.primary(go_to_chat, type="submit", class_=margin(left=1)),
                            action="",
                            onsubmit="navigateToChat(event)",
                        ),
                        navs.nav_item(
                            navs.nav_link(
                                f"{user_name} ({user_email})",
                                class_=join(colors.text.light, "downdown-toggle btn btn-primary"),
                                id=__defaults.user_dropdown,
                                role="button",
                                **{"data-toggle": "dropdown"},
                            ),
                            dropdowns.menu(
                                dropdowns.menu_item(
                                    logout_text,
                                    class_=join(colors.bg.danger, colors.text.light),
                                    href=logout_url,
                                    factory=inline.a,
                                ),
                                button_id=__defaults.user_dropdown,
                                class_=join(colors.bg.dark, colors.text.light),
                            ),
                            is_dropdown=True,
                        ),
                        id=__defaults.collapse_id,
                        style="z-index: 1000;",
                        nav_factory=block.div,  # type: ignore
                        nav_attributes={"class_": "justify-content-between", "style": "flex-grow: 1;"},
                    ),
                ),
                class_=colors.bg.dark,
                expand_point=navbars.ExpandPoint.LG,
                theme=navbars.Theme.DARK,
            ),
            block.div(*children),
            style="display: grid; grid-template-rows: 48px calc(100% - 48px); height:100%; overflow: hidden;",
        ),
        class_=colors.bg.dark,
        style="height: 100vh; width: 100vw; overflow: hidden;",
        page_title=page_title,
        head_elements=[req.bootstrap_css, *req.all_js],
        javascript=(navigate_to_chat_script(chat_room_base_url=chat_room_base_url), *(javascript or ())),
    )
