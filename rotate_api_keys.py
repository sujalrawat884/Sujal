import os
import re
import random
import argparse
from dotenv import load_dotenv

# Define your Google API keys here
API_KEYS = [
    "AIzaSyCxdCrE9ID0t9-uBADq1nj5x4QcPjm45u8",  # Current key from .env
    "YOUR_SECOND_API_KEY",  # Replace with your second key
    "YOUR_THIRD_API_KEY",   # Replace with your third key
    "YOUR_FOURTH_API_KEY"   # Replace with your fourth key
]

def update_env_file(new_key, env_path='.env'):
    """Update the Google API key in the .env file"""
    # Read the current .env file
    with open(env_path, 'r') as file:
        env_content = file.read()
    
    # Replace the Google API key using regex
    updated_content = re.sub(
        r'GOOGLE_API_KEY\s*=\s*"[^"]*"',
        f'GOOGLE_API_KEY = "{new_key}"',
        env_content
    )
    
    # Write the updated content back to the .env file
    with open(env_path, 'w') as file:
        file.write(updated_content)
    
    return new_key

def get_current_key():
    """Get the current Google API key from .env"""
    load_dotenv()
    return os.getenv("GOOGLE_API_KEY").strip('"')

def rotate_key(mode='next'):
    """Rotate the Google API key based on the selected mode"""
    current_key = get_current_key()
    
    try:
        current_index = API_KEYS.index(current_key)
    except ValueError:
        # If the current key isn't in our list, default to the first key
        print(f"Warning: Current key not found in API_KEYS list. Using the first key.")
        return update_env_file(API_KEYS[0])
    
    if mode == 'next':
        # Get the next key in the rotation (loop back to start if needed)
        next_index = (current_index + 1) % len(API_KEYS)
        new_key = API_KEYS[next_index]
    elif mode == 'random':
        # Get a random key that's different from the current one
        remaining_keys = [k for k in API_KEYS if k != current_key]
        if not remaining_keys:
            print("Only one API key available, no rotation possible.")
            return current_key
        new_key = random.choice(remaining_keys)
    elif mode.isdigit():
        # Get a specific key by index
        index = int(mode)
        if 0 <= index < len(API_KEYS):
            new_key = API_KEYS[index]
        else:
            print(f"Invalid index {index}. Using the first key.")
            new_key = API_KEYS[0]
    else:
        print(f"Invalid mode '{mode}'. Using the next key in rotation.")
        next_index = (current_index + 1) % len(API_KEYS)
        new_key = API_KEYS[next_index]
    
    return update_env_file(new_key)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rotate Google API keys in .env file")
    parser.add_argument('--mode', default='next', 
                        help="Rotation mode: 'next', 'random', or an index (0-based)")
    parser.add_argument('--list', action='store_true',
                        help="List all available API keys")
    
    args = parser.parse_args()
    
    if args.list:
        current_key = get_current_key()
        print("Available API keys:")
        for i, key in enumerate(API_KEYS):
            marker = " (current)" if key == current_key else ""
            print(f"{i}: {key[:12]}...{key[-4:]}{marker}")
    else:
        new_key = rotate_key(args.mode)
        print(f"API key updated to: {new_key[:12]}...{new_key[-4:]}")