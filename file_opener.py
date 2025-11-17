"""
Simple file opener utility function
"""

def open_file(file_path, mode='r', encoding='utf-8'):
    """
    Open a file with proper error handling.

    Args:
        file_path (str): Path to the file to open
        mode (str): File opening mode ('r', 'w', 'a', 'rb', 'wb', etc.)
        encoding (str): File encoding (default: 'utf-8')

    Returns:
        file object: Opened file object, or None if error occurs

    Example:
        file = open_file('example.txt', 'r')
        if file:
            content = file.read()
            file.close()
    """
    try:
        # For binary modes, don't use encoding parameter
        if 'b' in mode:
            return open(file_path, mode)
        else:
            return open(file_path, mode, encoding=encoding)
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except PermissionError:
        print(f"Error: Permission denied to access '{file_path}'.")
        return None
    except Exception as e:
        print(f"Error opening file '{file_path}': {str(e)}")
        return None


def read_file(file_path, encoding='utf-8'):
    """
    Convenience function to read entire file content.

    Args:
        file_path (str): Path to the file to read
        encoding (str): File encoding (default: 'utf-8')

    Returns:
        str: File content, or None if error occurs
    """
    file = open_file(file_path, 'r', encoding)
    if file:
        try:
            content = file.read()
            return content
        finally:
            file.close()
    return None


# Example usage
if __name__ == "__main__":
    # Example 1: Using open_file
    f = open_file('example.txt', 'r')
    if f:
        content = f.read()
        print(content)
        f.close()

    # Example 2: Using read_file (simpler)
    content = read_file('example.txt')
    if content:
        print(content)
