import re

def parse_install_command(user_input: str):
    """
    Parse input like 'I want to install chrome 97'
    Returns (app, version) or None
    """
    match = re.search(r'install\s+([a-zA-Z0-9]+)\s*([\d\.]+)?', user_input, re.I)
    if match:
        app = match.group(1)
        version = match.group(2) if match.group(2) else "latest"
        return app.lower(), version
    return None
