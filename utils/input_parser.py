import re
import logging
from urllib.parse import urlparse
from templates.messages import get_invalid_input_message, get_invalid_command_message, get_invalid_profile_message, get_invaid_repo_message , get_invalid_url_message

# Set up logger
logger = logging.getLogger(__name__)

class InputParser:
    @staticmethod
    def parse_input(text):
        """Parse user input to determine if it's a username, repo, or URL"""
        if not text or not isinstance(text, str):
            return {'type': 'invalid', 'message': get_invalid_input_message()}
            
        text = text.strip()
        valid_commands = ['start', 'help', 'trending', 'developer', 'about','report']
        
        # Check if it's a command
        if text.startswith('/'):
            command = text[1:].split('@')[0].lower()  # Remove bot mention if present
            if command in valid_commands:
                # For report command, check if it has arguments
                if command == 'report':
                    has_args = len(parts) > 1 and parts[1].strip()
                    return {
                        'type': 'command',
                        'command': command,
                        'has_args': has_args
                    }
                return {'type': 'command', 'command': command}
            else:
                return {'type': 'invalid', 'message': get_invalid_command_message()}
        
        # GitHub URL patterns
        if text.startswith(('http://', 'https://')):
            return InputParser._parse_url(text)
        
        # Direct username/repo patterns
        if '/' in text:
            parts = [p for p in text.split('/') if p]  # Remove empty parts
            if len(parts) == 2:
                return {
                    'type': 'repository',
                    'repo_owner': parts[0],
                    'repo_name': parts[1].split('?')[0].split('#')[0]  # Remove query params and fragments
                }
            return {'type': 'invalid', 'message': get_invaid_repo_message()}
        
        # Single username
        if re.match(r'^[a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38}$', text):
            return {
                'type': 'profile',
                'username': text
            }
        
        return {'type': 'invalid', 'message': get_invalid_input_message()}
    
    @staticmethod
    def _parse_url(url):
        """Parse GitHub URL and return repository or profile info"""
        try:
            parsed = urlparse(url)
            if 'github.com' not in parsed.netloc:
                return {'type': 'invalid', 'message': get_invalid_url_message()}
            
            path_parts = [p for p in parsed.path.split('/') if p]
            
            # Handle GitHub profile URLs
            if len(path_parts) == 1:
                username = path_parts[0]
                if re.match(r'^[a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38}$', username):
                    return {
                        'type': 'profile',
                        'username': username
                    }
                return {'type': 'invalid', 'message': get_invalid_profile_message()}
            
            # Handle GitHub repository URLs
            if len(path_parts) >= 2:
                owner = path_parts[0]
                repo = path_parts[1].split('?')[0].split('#')[0]  # Remove query params and fragments
                
                if (re.match(r'^[a-zA-Z\d](?:[a-zA-Z\d]|-(?=[a-zA-Z\d])){0,38}$', owner) and 
                    re.match(r'^[a-zA-Z0-9_.-]+$', repo)):
                    return {
                        'type': 'repository',
                        'repo_owner': owner,
                        'repo_name': repo
                    }
                return {'type': 'invalid', 'message': get_invaid_repo_message()}
            
        except Exception as e:
            logger.error(f"Error parsing URL {url}: {str(e)}")
            
        return {'type': 'invalid', 'message': get_invalid_input_message()}
