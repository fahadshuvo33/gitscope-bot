# Templates Package - Consolidated

from .templates import get_admin_section, get_loading_message
from .profile import get_profile_message, get_profile_loading
from .repos import get_repo_message, get_repo_loading
from .trending import get_trending_message, get_trending_loading, get_trending_list, get_trending_help
from .welcome import get_welcome_message
from .developer import get_developer_info
from .about import get_about_info
from .help import get_help_message
from .errors import get_error_message
from .messages import get_info_message, get_success_message, get_loading_message, get_invalid_input_message,get_warning_message,get_invalid_command_message,get_invalid_profile_message,get_invaid_repo_message, get_invalid_url_message

__all__ = [
    'get_admin_section', 'get_loading_message',
    'get_profile_message', 'get_profile_loading',
    'get_repo_message', 'get_repo_loading',
    'get_trending_message', 'get_trending_loading', 'get_trending_list', 'get_trending_help',
    'get_welcome_message', 'get_developer_info', 'get_about_info',
    'get_help_message', 'get_error_message',
    'get_info_message', 'get_success_message', 'get_loading_message','get_warning_message',"get_invalid_input_message","get_invalid_command_message","get_invalid_profile_message","get_invaid_repo_message","get_invalid_url_message"
]
