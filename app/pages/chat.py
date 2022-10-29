from markyp_bootstrap4 import colors, forms, list_groups
from markyp_bootstrap4.layout import container, one, row, row_item, padding
from markyp_html import block, join, script


class __defaults:
    chat_input_id = "chat-input"
    members_list_id = "members-list"
    message_list_id = "message-list"


def members(*, list_id=__defaults.members_list_id):
    # me_index = 23
    # members = [
    #     list_groups.list_group_item(
    #         ElementSequence(
    #             text.h5(f"Member {i}", class_=margin(0)), text.p(f"member-{i}@exmaple.ccm", class_=margin(0))
    #         ),
    #         context="primary" if i == me_index else "info",
    #         class_=padding(0),
    #     )
    #     for i in range(1, 201)
    # ]
    return list_groups.list_group(id=list_id, class_="h-100", style="overflow: auto;")


def message_list():
    return list_groups.list_group(
        id=__defaults.message_list_id,
        class_=colors.bg.secondary,
        style="border-radius: 4px; overflow: auto;",
    )


def chat_input(
    *,
    input_id=__defaults.chat_input_id,
    send_text="Send",
):
    return forms.inline_form(
        forms.input_(id=input_id, type_="text", placeholder="Message"),
        forms.submit_button.primary(
            send_text,
        ),
        action="",
        style="display: grid; grid-template-columns: 1fr max-content; gap: 8px;",
        onsubmit="sendMessage(event)",
    )


def chat_script(*, chat_ws_url: str) -> script:
    return script(
        "\n".join(
            (
                f"function parseMessage(message) {{",
                f"    const payload = JSON.parse(message);",
                f"    if (!('user' in payload)) return undefined;",
                f"    if (!(('name' in payload.user) && (typeof payload.user.name === 'string'))) return undefined;",
                f"    if (!(('email' in payload.user) && (typeof payload.user.email === 'string'))) return undefined;",
                f"    if (!(('self' in payload.user) && (typeof payload.user.self === 'boolean'))) return undefined;",
                f"    if (!(('message' in payload) && (typeof payload.message === 'string'))) return undefined;",
                f"",
                f"    return {{",
                f"        user: {{",
                f"            name: payload.user.name,",
                f"            email: payload.user.email,",
                f"            self: payload.user.self,",
                f"        }},",
                f"        message: payload.message,",
                f"    }};",
                f"}}",
                f"",
                f"function makeMessageNode(message) {{",
                f"    const li = document.createElement('li');",
                f"    li.classList.add('list-group-item');",
                f"    li.classList.add(message.user.self ? 'list-group-item-primary' : 'list-group-item-info');",
                f"",
                f"    const userInfo = document.createElement('h6');",
                f"    userInfo.appendChild(document.createTextNode(`${{message.user.name}} (${{message.user.email}})`));",
                f"",
                f"    const paragraph = document.createElement('p');",
                f"    paragraph.classList.add('m-0');",
                f"    paragraph.appendChild(document.createTextNode(message.message));",
                f"",
                f"    li.appendChild(userInfo);",
                f"    li.appendChild(paragraph);",
                f"",
                f"    return li;",
                f"}}",
                f"",
                f"function connectToChat() {{",
                f"    const ws = new WebSocket(`{chat_ws_url}`);",
                "",
                f"    ws.onmessage = (event) => {{",
                f"        const message = parseMessage(event.data);",
                f"        if (!message) return;",
                f"",
                f"        const messageList = document.getElementById('{__defaults.message_list_id}');",
                f"        const messageNode = makeMessageNode(message);",
                f"        const shouldScroll = messageList.scrollTop === messageList.scrollTopMax;",
                f"        messageList.appendChild(messageNode);",
                f"        if (shouldScroll) {{",
                f"            messageList.scrollTop = messageList.scrollHeight;",
                f"        }}",
                f"    }};",
                f"",
                f"    return ws;",
                f"}}",
                "",
                f"function sendMessage(event) {{",
                f"    event.preventDefault();",
                f"    const input = document.getElementById('{__defaults.chat_input_id}');",
                f"    if (input.value) {{",
                f"        ws.send(input.value);",
                f"        input.value = '';",
                f"    }}",
                f"}}",
            )
        )
    )


def chat_and_connect_scripts(*, chat_ws_url: str) -> tuple[script, script]:
    return (
        chat_script(chat_ws_url=chat_ws_url),
        script("const ws = connectToChat();"),
    )


def chat_container(*, member_list_hidden: bool = True):
    return container(
        row(
            *(() if member_list_hidden else (row_item(members(), md=3, class_="h-100", style="overflow: auto;"),)),
            row_item(
                block.div(
                    message_list(),
                    chat_input(),
                    class_="h-100",
                    style="display: grid; grid-template-rows: 1fr max-content; gap: 8px;",
                ),
                md=12 if member_list_hidden else 9,
                class_="h-100",
            ),
            class_="h-100",
        ),
        class_=join("h-100", padding(y=3)),
    )
