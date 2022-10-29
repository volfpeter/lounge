from markyp_bootstrap4 import alerts, colors, forms, req
from markyp_bootstrap4.layout import col, offset, one, padding
from markyp_html import join, script, webpage as html_webpage
from markyp_html.forms import form as html_form


class __defaults:
    submit_button = "submit-button"
    email_input = "login-form-email"
    name_input = "login-form-name"
    success_alert_id = "success-alert"
    error_alert_id = "error-alert"


def login_form_submit_script(
    *,
    email_login_url: str,
):
    return script(
        "\n".join(
            (
                "async function onLoginFormSubmit(event) {",
                f"    event.preventDefault();",
                "",
                f"    const nameInput = document.getElementById('{__defaults.name_input}');",
                f"    const emailInput = document.getElementById('{__defaults.email_input}');",
                f"    const submitButton = document.getElementById('{__defaults.submit_button}');",
                f"    const successAlert = document.getElementById('{__defaults.success_alert_id}');",
                f"    const errorAlert = document.getElementById('{__defaults.error_alert_id}');",
                f"    const formNodes = [nameInput, emailInput, submitButton];",
                "",
                f"    for (const node of formNodes) {{ node.setAttribute('disabled', true); }}",
                f"    successAlert.setAttribute('hidden', true);",
                f"    errorAlert.setAttribute('hidden', true);",
                "",
                f"    const body = JSON.stringify({{ name: nameInput.value, email: emailInput.value }});",
                f"    const headers = {{ 'Content-Type': 'application/json' }};",
                "",
                f"    try {{",
                f"        await fetch('{email_login_url}', {{ body, headers, method: 'POST' }});",
                f"        successAlert.removeAttribute('hidden');",
                f"    }} catch {{",
                f"        for (const node of formNodes) {{ node.removeAttribute('disabled'); }}",
                f"        errorAlert.removeAttribute('hidden');",
                f"    }}",
                "}",
            )
        )
    )


def login_form(
    *,
    name: str | None,
    name_placeholder="Enter your name",
    email: str | None,
    email_placeholder="Enter your email address",
    submit_text="Log In",
    success_message="Please check your inbox for the login link.",
    success_message_hidden=True,
    error_message="Invalid credentials.",
    error_message_hidden=True,
    text_color_class: str | None = colors.text.light,
):
    return html_form(
        forms.form_group(
            forms.text.h5("Name", class_=join(col(md=2), text_color_class)),
            forms.input_.text(
                value=name or "",
                placeholder=name_placeholder,
                class_=col(md=10),
                id=__defaults.name_input,
            ),
            row=True,
        ),
        forms.form_group(
            forms.text.h5("Email", class_=join(col(md=2), text_color_class)),
            forms.input_.email(
                value=email or "",
                placeholder=email_placeholder,
                class_=col(md=10),
                id=__defaults.email_input,
            ),
            row=True,
        ),
        alerts.alert.success(
            success_message,
            id=__defaults.success_alert_id,
            **({"hidden": True} if success_message_hidden else {}),
        ),
        alerts.alert.danger(
            error_message,
            id=__defaults.error_alert_id,
            **({"hidden": True} if error_message_hidden else {}),
        ),
        forms.submit_button.primary(submit_text, id=__defaults.submit_button, type="submit"),
        action="",
        onsubmit="onLoginFormSubmit(event)",
    )


def email_login_page(
    *,
    email_login_url: str,
    page_title="Lounge > Login",
    success_message="Please check your inbox for the login link.",
    success_message_hidden=True,
    error_message="Invalid credentials.",
    error_message_hidden=True,
):
    return html_webpage(
        one(
            login_form(
                name=None,
                email=None,
                error_message=error_message,
                error_message_hidden=error_message_hidden,
                success_message=success_message,
                success_message_hidden=success_message_hidden,
            ),
            class_=join(col(md=4), offset(md=4), padding(y=5)),
        ),
        class_=colors.bg.dark,
        page_title=page_title,
        head_elements=[req.bootstrap_css, *req.all_js],
        javascript=(login_form_submit_script(email_login_url=email_login_url),),
    )
