"""
Comprehensive file operations module with error handling and utilities.
"""

import os
import json
import csv
from pathlib import Path
from typing import Optional, List, Dict, Any, Union
from contextlib import contextmanager


class FileOpenerError(Exception):
    """Base exception for file opener errors."""
    pass


class FileNotFoundError(FileOpenerError):
    """Raised when file is not found."""
    pass


class PermissionError(FileOpenerError):
    """Raised when permission is denied."""
    pass


@contextmanager
def open_file(file_path: Union[str, Path], mode: str = 'r', encoding: str = 'utf-8'):
    """
    Context manager for opening files with proper error handling.

    Args:
        file_path: Path to the file to open
        mode: File opening mode ('r', 'w', 'a', 'rb', 'wb', etc.)
        encoding: File encoding (default: 'utf-8')

    Yields:
        file object: Opened file object

    Raises:
        FileOpenerError: If file operation fails

    Example:
        with open_file('example.txt', 'r') as f:
            content = f.read()
    """
    file_path = Path(file_path)
    file_obj = None

    try:
        # For binary modes, don't use encoding parameter
        if 'b' in mode:
            file_obj = open(file_path, mode)
        else:
            file_obj = open(file_path, mode, encoding=encoding)
        yield file_obj
    except IOError as e:
        if e.errno == 2:
            raise FileNotFoundError(f"File '{file_path}' not found") from e
        elif e.errno == 13:
            raise PermissionError(f"Permission denied to access '{file_path}'") from e
        else:
            raise FileOpenerError(f"Error opening file '{file_path}': {str(e)}") from e
    finally:
        if file_obj and not file_obj.closed:
            file_obj.close()


def read_file(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[str]:
    """
    Read entire file content as string.

    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: 'utf-8')

    Returns:
        File content as string, or None if error occurs
    """
    try:
        with open_file(file_path, 'r', encoding) as f:
            return f.read()
    except FileOpenerError as e:
        print(f"Error: {e}")
        return None


def read_lines(file_path: Union[str, Path], encoding: str = 'utf-8',
               strip: bool = True) -> Optional[List[str]]:
    """
    Read file content as list of lines.

    Args:
        file_path: Path to the file to read
        encoding: File encoding (default: 'utf-8')
        strip: Whether to strip whitespace from lines (default: True)

    Returns:
        List of lines, or None if error occurs
    """
    try:
        with open_file(file_path, 'r', encoding) as f:
            lines = f.readlines()
            if strip:
                lines = [line.strip() for line in lines]
            return lines
    except FileOpenerError as e:
        print(f"Error: {e}")
        return None


def write_file(file_path: Union[str, Path], content: str,
               encoding: str = 'utf-8', append: bool = False) -> bool:
    """
    Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write
        encoding: File encoding (default: 'utf-8')
        append: Whether to append to file (default: False)

    Returns:
        True if successful, False otherwise
    """
    mode = 'a' if append else 'w'
    try:
        with open_file(file_path, mode, encoding) as f:
            f.write(content)
        return True
    except FileOpenerError as e:
        print(f"Error: {e}")
        return False


def write_lines(file_path: Union[str, Path], lines: List[str],
                encoding: str = 'utf-8', append: bool = False) -> bool:
    """
    Write list of lines to a file.

    Args:
        file_path: Path to the file to write
        lines: List of lines to write
        encoding: File encoding (default: 'utf-8')
        append: Whether to append to file (default: False)

    Returns:
        True if successful, False otherwise
    """
    content = '\n'.join(lines) + '\n'
    return write_file(file_path, content, encoding, append)


def read_json(file_path: Union[str, Path], encoding: str = 'utf-8') -> Optional[Any]:
    """
    Read and parse JSON file.

    Args:
        file_path: Path to the JSON file
        encoding: File encoding (default: 'utf-8')

    Returns:
        Parsed JSON data, or None if error occurs
    """
    try:
        with open_file(file_path, 'r', encoding) as f:
            return json.load(f)
    except FileOpenerError as e:
        print(f"Error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{file_path}': {e}")
        return None


def write_json(file_path: Union[str, Path], data: Any,
               encoding: str = 'utf-8', indent: int = 2) -> bool:
    """
    Write data to JSON file.

    Args:
        file_path: Path to the JSON file
        data: Data to write (must be JSON serializable)
        encoding: File encoding (default: 'utf-8')
        indent: JSON indentation (default: 2)

    Returns:
        True if successful, False otherwise
    """
    try:
        with open_file(file_path, 'w', encoding) as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except FileOpenerError as e:
        print(f"Error: {e}")
        return False
    except (TypeError, ValueError) as e:
        print(f"Error: Cannot serialize data to JSON: {e}")
        return False


def read_csv(file_path: Union[str, Path], encoding: str = 'utf-8',
             delimiter: str = ',', has_header: bool = True) -> Optional[List[Dict[str, str]]]:
    """
    Read CSV file as list of dictionaries.

    Args:
        file_path: Path to the CSV file
        encoding: File encoding (default: 'utf-8')
        delimiter: CSV delimiter (default: ',')
        has_header: Whether CSV has header row (default: True)

    Returns:
        List of dictionaries (one per row), or None if error occurs
    """
    try:
        with open_file(file_path, 'r', encoding) as f:
            if has_header:
                reader = csv.DictReader(f, delimiter=delimiter)
            else:
                reader = csv.reader(f, delimiter=delimiter)
            return list(reader)
    except FileOpenerError as e:
        print(f"Error: {e}")
        return None
    except csv.Error as e:
        print(f"Error: Invalid CSV in '{file_path}': {e}")
        return None


def write_csv(file_path: Union[str, Path], data: List[Dict[str, Any]],
              encoding: str = 'utf-8', delimiter: str = ',') -> bool:
    """
    Write data to CSV file.

    Args:
        file_path: Path to the CSV file
        data: List of dictionaries to write
        encoding: File encoding (default: 'utf-8')
        delimiter: CSV delimiter (default: ',')

    Returns:
        True if successful, False otherwise
    """
    if not data:
        print("Error: No data to write")
        return False

    try:
        with open_file(file_path, 'w', encoding) as f:
            fieldnames = data[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()
            writer.writerows(data)
        return True
    except FileOpenerError as e:
        print(f"Error: {e}")
        return False
    except (csv.Error, AttributeError) as e:
        print(f"Error: Cannot write CSV: {e}")
        return False


def read_binary(file_path: Union[str, Path]) -> Optional[bytes]:
    """
    Read file in binary mode.

    Args:
        file_path: Path to the file to read

    Returns:
        File content as bytes, or None if error occurs
    """
    try:
        with open_file(file_path, 'rb') as f:
            return f.read()
    except FileOpenerError as e:
        print(f"Error: {e}")
        return None


def write_binary(file_path: Union[str, Path], data: bytes) -> bool:
    """
    Write binary data to file.

    Args:
        file_path: Path to the file to write
        data: Binary data to write

    Returns:
        True if successful, False otherwise
    """
    try:
        with open_file(file_path, 'wb') as f:
            f.write(data)
        return True
    except FileOpenerError as e:
        print(f"Error: {e}")
        return False


def file_exists(file_path: Union[str, Path]) -> bool:
    """
    Check if file exists.

    Args:
        file_path: Path to check

    Returns:
        True if file exists, False otherwise
    """
    return Path(file_path).is_file()


def get_file_info(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Get file information.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file info, or None if file doesn't exist
    """
    path = Path(file_path)
    if not path.is_file():
        return None

    stat = path.stat()
    return {
        'name': path.name,
        'size': stat.st_size,
        'size_human': _human_readable_size(stat.st_size),
        'created': stat.st_ctime,
        'modified': stat.st_mtime,
        'is_readable': os.access(path, os.R_OK),
        'is_writable': os.access(path, os.W_OK),
        'extension': path.suffix,
        'absolute_path': str(path.absolute())
    }


def _human_readable_size(size: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def create_file(file_path: Union[str, Path], content: str = '',
                encoding: str = 'utf-8', overwrite: bool = False) -> bool:
    """
    Create a new file.

    Args:
        file_path: Path to the file to create
        content: Initial content (default: empty string)
        encoding: File encoding (default: 'utf-8')
        overwrite: Whether to overwrite if file exists (default: False)

    Returns:
        True if successful, False otherwise
    """
    path = Path(file_path)
    if path.exists() and not overwrite:
        print(f"Error: File '{file_path}' already exists")
        return False

    return write_file(file_path, content, encoding)


# Example usage
if __name__ == "__main__":
    print("=== File Opener Module Examples ===\n")

    # Example 1: Context manager usage
    print("1. Using context manager:")
    try:
        with open_file('example.txt', 'w') as f:
            f.write("Hello, World!\n")
            f.write("This is a test file.\n")
        print("   ✓ File written successfully")
    except FileOpenerError as e:
        print(f"   ✗ Error: {e}")

    # Example 2: Read file
    print("\n2. Reading file:")
    content = read_file('example.txt')
    if content:
        print(f"   Content: {content.strip()}")

    # Example 3: Read lines
    print("\n3. Reading lines:")
    lines = read_lines('example.txt')
    if lines:
        for i, line in enumerate(lines, 1):
            print(f"   Line {i}: {line}")

    # Example 4: JSON operations
    print("\n4. JSON operations:")
    test_data = {'name': 'John', 'age': 30, 'city': 'New York'}
    if write_json('test.json', test_data):
        print("   ✓ JSON written successfully")
        data = read_json('test.json')
        if data:
            print(f"   Data read: {data}")

    # Example 5: CSV operations
    print("\n5. CSV operations:")
    csv_data = [
        {'name': 'Alice', 'age': '25', 'city': 'Boston'},
        {'name': 'Bob', 'age': '35', 'city': 'Seattle'}
    ]
    if write_csv('test.csv', csv_data):
        print("   ✓ CSV written successfully")
        data = read_csv('test.csv')
        if data:
            print(f"   Rows read: {len(data)}")

    # Example 6: File info
    print("\n6. File information:")
    info = get_file_info('example.txt')
    if info:
        print(f"   Name: {info['name']}")
        print(f"   Size: {info['size_human']}")
        print(f"   Readable: {info['is_readable']}")
        print(f"   Writable: {info['is_writable']}")

    # Example 7: Binary operations
    print("\n7. Binary file operations:")
    binary_data = b'\x89PNG\r\n\x1a\n'  # PNG file signature
    if write_binary('test.bin', binary_data):
        print("   ✓ Binary file written")
        read_data = read_binary('test.bin')
        if read_data:
            print(f"   ✓ Binary file read ({len(read_data)} bytes)")
