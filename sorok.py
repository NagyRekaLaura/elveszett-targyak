import os
import sys
from pathlib import Path

def count_lines_in_file(file_path):
    """Count lines in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def should_skip_directory(dir_path, exclude_dirs):
    """Check if directory should be skipped."""
    if not exclude_dirs:
        return False
    
    dir_name = os.path.basename(dir_path)
    for exclude in exclude_dirs:
        if exclude in dir_path or dir_name == exclude:
            return True
    return False

def scan_directory(directory, file_extensions=None, exclude_dirs=None):
    """
    Scan directory recursively and count lines in files.
    
    Args:
        directory: Path to the directory to scan
        file_extensions: List of file extensions to include (e.g., ['.py', '.txt'])
                        If None, all files are included
        exclude_dirs: List of directory names or paths to exclude (e.g., ['node_modules', '.git', '__pycache__'])
    
    Returns:
        Tuple of (results dict, total_lines)
    """
    results = {}
    total_lines = 0
    
    if not os.path.isdir(directory):
        print(f"Error: '{directory}' is not a valid directory")
        return None, 0
    
    for root, dirs, files in os.walk(directory):
        if exclude_dirs:
            dirs[:] = [d for d in dirs if not should_skip_directory(os.path.join(root, d), exclude_dirs)]
        
        for file in files:
            if file_extensions:
                if not any(file.endswith(ext) for ext in file_extensions):
                    continue
            
            file_path = os.path.join(root, file)
            line_count = count_lines_in_file(file_path)
            results[file_path] = line_count
            total_lines += line_count
    
    return results, total_lines

def print_results(results, total_lines):
    """Print results in a formatted way."""
    print("\n" + "="*80)
    print("FILE LINE COUNT SUMMARY")
    print("="*80 + "\n")
    
    sorted_results = sorted(results.items())
    
    for file_path, line_count in sorted_results:
        print(f"{line_count:>8} lines | {file_path}")
    
    print("\n" + "-"*80)
    print(f"{'TOTAL':>8} lines | {len(results)} files")
    print("="*80 + "\n")

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python count_lines.py <directory> [--ext extension1 extension2 ...] [--exclude dir1 dir2 ...]")
        print("\nExample 1 (all files):")
        print("  python count_lines.py /path/to/directory")
        print("\nExample 2 (only Python files, exclude node_modules):")
        print("  python count_lines.py /path/to/directory --ext .py --exclude node_modules .git")
        print("\nExample 3 (multiple extensions):")
        print("  python count_lines.py /path/to/directory --ext .py .js .txt --exclude __pycache__ .venv dist")
        print("\nExample 4 (exclude only):")
        print("  python count_lines.py /path/to/directory --exclude node_modules .git __pycache__")
        sys.exit(1)
    
    directory = sys.argv[1]
    file_extensions = None
    exclude_dirs = None
    
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--ext':
            i += 1
            file_extensions = []
            while i < len(args) and not args[i].startswith('--'):
                ext = args[i]
                ext = f".{ext}" if not ext.startswith('.') else ext
                file_extensions.append(ext)
                i += 1
            i -= 1
        elif args[i] == '--exclude':
            i += 1
            exclude_dirs = []
            while i < len(args) and not args[i].startswith('--'):
                exclude_dirs.append(args[i])
                i += 1
            i -= 1
        i += 1
    
    print(f"Directory: {directory}\n")
    
    if file_extensions:
        print(f"File extensions: {', '.join(file_extensions)}")
    else:
        print("Scanning all files")
    
    if exclude_dirs:
        print(f"Excluded directories: {', '.join(exclude_dirs)}")
    else:
        print("No directories excluded")
    
    print()
    
    results, total_lines = scan_directory(directory, file_extensions, exclude_dirs)
    
    if results is None:
        sys.exit(1)
    
    if not results:
        print("No files found matching criteria.")
        sys.exit(0)
    
    print_results(results, total_lines)
    print(f"Total lines across all files: {total_lines}")

if __name__ == "__main__":
    main()