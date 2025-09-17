from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, List

# ═══════════════════════════════════════════════════════════════════
#                    UNIVERSAL PAGINATION SYSTEM
# ═══════════════════════════════════════════════════════════════════


def create_pagination_keyboard(
    base_callback: str,
    current_page: int,
    total_pages: int,
    back_callback: str,
    show_navigation: bool = True,
    extra_buttons: List[List[InlineKeyboardButton]] = None,
) -> InlineKeyboardMarkup:
    """
    Universal pagination keyboard for all pages

    Args:
        base_callback: Base callback like 'user_followers_username' or 'repo_releases_owner/repo'
        current_page: Current page number (1-based)
        total_pages: Total number of pages
        back_callback: Where to go back
        show_navigation: Whether to show pagination (set False if error/success)
        extra_buttons: Additional button rows to add
    """
    buttons = []

    # Add extra buttons first (like retry, refresh, etc.)
    if extra_buttons:
        for button_row in extra_buttons:
            if isinstance(button_row, list):
                # Handle list of button objects or dicts
                row = []
                for button in button_row:
                    if isinstance(button, dict):
                        # Convert dict to InlineKeyboardButton
                        row.append(InlineKeyboardButton(
                            button["text"], 
                            callback_data=button["callback_data"]
                        ))
                    else:
                        # Assume it's already an InlineKeyboardButton
                        row.append(button)
                buttons.append(row)
            else:
                # Single button
                if isinstance(button_row, dict):
                    buttons.append([InlineKeyboardButton(
                        button_row["text"], 
                        callback_data=button_row["callback_data"]
                    )])
                else:
                    buttons.append([button_row])

    # Add pagination row only if needed and show_navigation is True
    if show_navigation and total_pages > 1:
        pagination_row = []

        # First page button (if not on first page)
        if current_page > 1:
            pagination_row.append(
                InlineKeyboardButton("⏮️", callback_data=f"{base_callback}_1")
            )

        # Previous page button (if not on first page)
        if current_page > 1:
            pagination_row.append(
                InlineKeyboardButton(
                    "⬅️", callback_data=f"{base_callback}_{current_page-1}"
                )
            )

        # Current page indicator
        pagination_row.append(
            InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop")
        )

        # Next page button (if not on last page)
        if current_page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    "➡️", callback_data=f"{base_callback}_{current_page+1}"
                )
            )

        # Last page button (if not on last page)
        if current_page < total_pages:
            pagination_row.append(
                InlineKeyboardButton(
                    "⏭️", callback_data=f"{base_callback}_{total_pages}"
                )
            )

        buttons.append(pagination_row)

    # Add back button
    buttons.append([InlineKeyboardButton("⬅️ Back", callback_data=back_callback)])

    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════
#                        SPECIFIC PAGE KEYBOARDS
# ═══════════════════════════════════════════════════════════════════


def get_profile_main_keyboard(username: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main profile page - no pagination needed"""
    buttons = [
        [
            InlineKeyboardButton(
                "📂 Repositories", callback_data=f"user_repos_{username}"
            ),
            InlineKeyboardButton(
                "⭐ Starred", callback_data=f"user_starred_{username}"
            ),
        ],
        [
            InlineKeyboardButton(
                "👥 Followers", callback_data=f"user_followers_{username}"
            ),
            InlineKeyboardButton(
                "👤 Following", callback_data=f"user_following_{username}"
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 Stats & Activity", callback_data=f"user_stats_{username}"
            ),
            InlineKeyboardButton("📸 Avatar", callback_data=f"show_avatar_{username}"),
        ],
    ]

    # Add admin buttons if user is admin
    if is_admin:
        buttons.append([
            InlineKeyboardButton("👑 Admin Profile", callback_data=f"admin_profile_{username}"),
            InlineKeyboardButton("📋 Logs", callback_data="show_logs"),
        ])

    buttons.append([
        InlineKeyboardButton("🔄 Refresh", callback_data=f"refresh_user_{username}"),
        InlineKeyboardButton("🏠 Back to Start", callback_data="start"),
    ])

    return InlineKeyboardMarkup(buttons)


def get_repo_main_keyboard(repo: str, is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main repository page - no pagination needed"""
    buttons = [
        [
            InlineKeyboardButton(
                "👥 Contributors", callback_data=f"repo_contributors_{repo}"
            ),
            InlineKeyboardButton(
                "📝 Pull Requests", callback_data=f"repo_pulls_{repo}"
            ),
        ],
        [
            InlineKeyboardButton("🐛 Issues", callback_data=f"repo_issues_{repo}"),
            InlineKeyboardButton(
                "💻 Languages", callback_data=f"repo_languages_{repo}"
            ),
        ],
        [
            InlineKeyboardButton(
                "🏷️ Releases", callback_data=f"repo_releases_{repo}"
            ),
            InlineKeyboardButton("📖 README", callback_data=f"repo_readme_{repo}"),
        ],
    ]

    # Add admin buttons if user is admin
    if is_admin:
        buttons.append([
            InlineKeyboardButton("👑 Admin Repo", callback_data=f"admin_repo_{repo}"),
        ])

    buttons.append([
        InlineKeyboardButton("🔄 Refresh", callback_data=f"repo_{repo}"),
        InlineKeyboardButton(
            "🏠 Back to Start", callback_data="start"
        ),
    ])

    return InlineKeyboardMarkup(buttons)


# ═══════════════════════════════════════════════════════════════════
#                    PAGE-SPECIFIC PAGINATION HELPERS
# ═══════════════════════════════════════════════════════════════════


def get_followers_keyboard(
    username: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Followers page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"user_followers_{username}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"profile_{username}",
        show_navigation=success,  # Don't show pagination if error occurred
    )


def get_following_keyboard(
    username: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Following page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"user_following_{username}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"profile_{username}",
        show_navigation=success,
    )


def get_user_repos_keyboard(
    username: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """User repositories page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"user_repos_{username}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"profile_{username}",
        show_navigation=success,
    )


def get_starred_repos_keyboard(
    username: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Starred repositories page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"user_starred_{username}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"profile_{username}",
        show_navigation=success,
    )


def get_repo_releases_keyboard(
    repo: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Repository releases page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"repo_releases_{repo}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"repo_{repo}",
        show_navigation=success,
    )


def get_repo_contributors_keyboard(
    repo: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Repository contributors page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"repo_contributors_{repo}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"repo_{repo}",
        show_navigation=success,
    )


def get_repo_issues_keyboard(
    repo: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Repository issues page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"repo_issues_{repo}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"repo_{repo}",
        show_navigation=success,
    )


def get_repo_pulls_keyboard(
    repo: str, page: int, total_pages: int, success: bool = True
) -> InlineKeyboardMarkup:
    """Repository pull requests page with pagination"""
    return create_pagination_keyboard(
        base_callback=f"repo_pulls_{repo}",
        current_page=page,
        total_pages=total_pages,
        back_callback=f"repo_{repo}",
        show_navigation=success,
    )


def get_readme_keyboard(repo: str, success: bool = True) -> InlineKeyboardMarkup:
    """README page (usually no pagination needed, but can add if README is split)"""
    extra_buttons = []
    if success:
        # Add refresh button only on success
        extra_buttons.append(
            [InlineKeyboardButton("🔄 Refresh", callback_data=f"repo_readme_{repo}")]
        )

    return create_pagination_keyboard(
        base_callback=f"repo_readme_{repo}",
        current_page=1,
        total_pages=1,
        back_callback=f"repo_{repo}",
        show_navigation=True,  # README usually doesn't need pagination
        extra_buttons=extra_buttons,
    )


# ═══════════════════════════════════════════════════════════════════
#                        SIMPLE UTILITY KEYBOARDS
# ═══════════════════════════════════════════════════════════════════


def get_back_keyboard(back_callback: str) -> InlineKeyboardMarkup:
    """Simple back button"""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data=back_callback)]]
    )


def get_retry_back_keyboard(
    retry_callback: str, back_callback: str
) -> InlineKeyboardMarkup:
    """Retry and back buttons for errors"""
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Retry", callback_data=retry_callback),
                InlineKeyboardButton("⬅️ Back", callback_data=back_callback),
            ]
        ]
    )
