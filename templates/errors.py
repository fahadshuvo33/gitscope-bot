ERROR_MESSAGE = """❌ *Error loading {context}*

`{error_message}`

Please try again\\."""

VALIDATION_ERROR = """❌ *Invalid GitHub username:* `{username}`

{error_message}"""

USAGE_ERROR = """❌ Usage Error

Correct usage:
{usage_text}

Examples:
{examples}

💡 Tip: {tip}"""

def get_error_message(context="Data", error_message=""):
    return ERROR_MESSAGE.format(
        context=context,
        error_message=error_message
    )

def get_validation_error(username, error_message):
    return VALIDATION_ERROR.format(
        username=username,
        error_message=error_message
    )

def get_usage_error(usage_text, examples, tip="Follow the correct format"):
    return USAGE_ERROR.format(
        usage_text=usage_text,
        examples=examples,
        tip=tip
    )
