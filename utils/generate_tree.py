"""
Utility script to generate project folder structure tree.
Supports multiple output formats and filtering options.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import argparse
from datetime import datetime


class OutputFormat(Enum):
    """Output format options."""
    TREE = "tree"  # ASCII tree format
    TREE_DETAILED = "tree_detailed"  # Tree with file sizes and counts
    JSON = "json"  # JSON format
    MARKDOWN = "markdown"  # Markdown format
    VISUAL = "visual"  # Visual tree with colors (terminal)


@dataclass
class FileInfo:
    """Information about a file or directory."""
    name: str
    path: Path
    is_dir: bool
    size: int = 0
    file_count: int = 0
    dir_count: int = 0
    depth: int = 0


class TreeGenerator:
    """Generate project structure tree in various formats."""

    # Default ignore patterns
    DEFAULT_IGNORE_DIRS = {
        '__pycache__',
        '.git',
        '.venv',
        'venv',
        'env',
        '.env',
        'node_modules',
        '.pytest_cache',
        '.mypy_cache',
        '.idea',
        '.vscode',
        'dist',
        'build',
        '*.egg-info',
        '.DS_Store',
        'htmlcov',
        '.tox',
        '__pypackages__',
    }

    DEFAULT_IGNORE_FILES = {
        '.pyc',
        '.pyo',
        '.pyd',
        '.so',
        '.o',
        '.a',
        '.lib',
        '.dll',
        '.exe',
        '.class',
        '.jar',
        '.zip',
        '.tar',
        '.gz',
        '.bak',
        '.tmp',
        '.log',
    }

    def __init__(
            self,
            root_path: str,
            ignore_dirs: Optional[Set[str]] = None,
            ignore_files: Optional[Set[str]] = None,
            max_depth: int = -1,
            include_hidden: bool = False,
            include_sizes: bool = False
    ):
        """
        Initialize TreeGenerator.

        Args:
            root_path: Root directory path to analyze
            ignore_dirs: Set of directory names to ignore
            ignore_files: Set of file extensions to ignore
            max_depth: Maximum depth to traverse (-1 for unlimited)
            include_hidden: Include hidden files/directories
            include_sizes: Include file sizes in output
        """
        self.root_path = Path(root_path).resolve()

        if not self.root_path.exists():
            raise ValueError(f"Path does not exist: {root_path}")

        if not self.root_path.is_dir():
            raise ValueError(f"Path is not a directory: {root_path}")

        self.ignore_dirs = ignore_dirs or self.DEFAULT_IGNORE_DIRS
        self.ignore_files = ignore_files or self.DEFAULT_IGNORE_FILES
        self.max_depth = max_depth
        self.include_hidden = include_hidden
        self.include_sizes = include_sizes

        # Statistics
        self.total_files = 0
        self.total_dirs = 0
        self.total_size = 0

    def _should_ignore(self, name: str, is_dir: bool) -> bool:
        """Check if item should be ignored."""
        # Check hidden files
        if not self.include_hidden and name.startswith('.'):
            return True

        # Check ignored directories
        if is_dir:
            return name in self.ignore_dirs

        # Check ignored file extensions
        for ext in self.ignore_files:
            if name.endswith(ext):
                return True

        return False

    def _get_file_size(self, path: Path) -> int:
        """Get file size in bytes."""
        try:
            return path.stat().st_size
        except OSError:
            return 0

    def _get_dir_size(self, path: Path) -> int:
        """Get total size of directory."""
        total = 0
        try:
            for entry in path.rglob('*'):
                if entry.is_file():
                    total += self._get_file_size(entry)
        except OSError:
            pass
        return total

    def _format_size(self, size: int) -> str:
        """Format size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"

    def _count_items(self, path: Path) -> Tuple[int, int]:
        """Count files and directories."""
        files = 0
        dirs = 0
        try:
            for entry in path.iterdir():
                if entry.is_dir() and not self._should_ignore(entry.name, True):
                    dirs += 1
                elif entry.is_file() and not self._should_ignore(entry.name, False):
                    files += 1
        except OSError:
            pass
        return files, dirs

    def build_tree(self, path: Optional[Path] = None, depth: int = 0) -> List[FileInfo]:
        """
        Build tree structure recursively.

        Args:
            path: Current path to process
            depth: Current depth in tree

        Returns:
            List of FileInfo objects
        """
        if path is None:
            path = self.root_path

        items = []

        # Check depth limit
        if self.max_depth != -1 and depth > self.max_depth:
            return items

        try:
            entries = sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        except PermissionError:
            return items

        for entry in entries:
            # Skip ignored items
            if self._should_ignore(entry.name, entry.is_dir()):
                continue

            is_dir = entry.is_dir()

            # Calculate size
            if is_dir:
                size = self._get_dir_size(entry) if self.include_sizes else 0
                file_count, dir_count = self._count_items(entry)
                self.total_dirs += 1
            else:
                size = self._get_file_size(entry) if self.include_sizes else 0
                file_count = 0
                dir_count = 0
                self.total_files += 1

            self.total_size += size

            file_info = FileInfo(
                name=entry.name,
                path=entry,
                is_dir=is_dir,
                size=size,
                file_count=file_count,
                dir_count=dir_count,
                depth=depth
            )
            items.append(file_info)

            # Recursively process subdirectories
            if is_dir:
                sub_items = self.build_tree(entry, depth + 1)
                items.extend(sub_items)

        return items

    def generate_tree_format(self, items: List[FileInfo]) -> str:
        """Generate ASCII tree format."""
        lines = [f"{self.root_path.name}/"]

        for i, item in enumerate(items):
            # Calculate prefix
            is_last = (i == len(items) - 1) or (
                    i + 1 < len(items) and items[i + 1].depth <= item.depth
            )

            # Build tree characters
            prefix = ""
            for parent_depth in range(item.depth):
                prefix += "    "

            connector = "└── " if is_last else "├── "

            # Item indicator
            indicator = "📁" if item.is_dir else "📄"

            lines.append(f"{prefix}{connector}{indicator} {item.name}")

        return "\n".join(lines)

    def generate_tree_detailed_format(self, items: List[FileInfo]) -> str:
        """Generate detailed tree format with sizes and counts."""
        lines = [f"{self.root_path.name}/"]

        for i, item in enumerate(items):
            # Calculate prefix
            is_last = (i == len(items) - 1) or (
                    i + 1 < len(items) and items[i + 1].depth <= item.depth
            )

            prefix = ""
            for parent_depth in range(item.depth):
                prefix += "    "

            connector = "└── " if is_last else "├── "
            indicator = "📁" if item.is_dir else "📄"

            # Add size/count information
            if item.is_dir:
                info = f" ({item.file_count}f, {item.dir_count}d"
                if self.include_sizes:
                    info += f", {self._format_size(item.size)}"
                info += ")"
            else:
                info = ""
                if self.include_sizes:
                    info = f" ({self._format_size(item.size)})"

            lines.append(f"{prefix}{connector}{indicator} {item.name}{info}")

        return "\n".join(lines)

    def generate_markdown_format(self, items: List[FileInfo]) -> str:
        """Generate Markdown format."""
        lines = [
            f"# Project Structure: {self.root_path.name}",
            "",
            f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Directory Tree",
            "",
            "```",
            f"{self.root_path.name}/",
        ]

        for item in items:
            prefix = "  " * item.depth
            connector = "└── " if item.depth > 0 else ""
            indicator = "📁" if item.is_dir else "📄"

            if item.is_dir:
                info = f" ({item.file_count} files, {item.dir_count} dirs"
                if self.include_sizes:
                    info += f", {self._format_size(item.size)}"
                info += ")"
            else:
                info = ""
                if self.include_sizes:
                    info = f" ({self._format_size(item.size)})"

            lines.append(f"{prefix}{connector}{indicator} {item.name}{info}")

        lines.append("```")
        lines.append("")
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total Files**: {self.total_files}")
        lines.append(f"- **Total Directories**: {self.total_dirs}")
        if self.include_sizes:
            lines.append(f"- **Total Size**: {self._format_size(self.total_size)}")

        return "\n".join(lines)

    def generate_json_format(self, items: List[FileInfo]) -> str:
        """Generate JSON format."""

        def build_json_tree(items: List[FileInfo]) -> Dict:
            """Build nested JSON structure."""
            tree = {
                "name": self.root_path.name,
                "type": "directory",
                "path": str(self.root_path),
                "children": []
            }

            # Group items by parent
            current_level = {}
            for item in items:
                if item.depth == 0:
                    node = {
                        "name": item.name,
                        "type": "directory" if item.is_dir else "file",
                        "path": str(item.path),
                    }

                    if item.is_dir:
                        node["file_count"] = item.file_count
                        node["dir_count"] = item.dir_count
                        if self.include_sizes:
                            node["size"] = item.size
                        node["children"] = []
                    else:
                        if self.include_sizes:
                            node["size"] = item.size

                    tree["children"].append(node)

            return tree

        # Simpler JSON structure
        structure = {
            "root": str(self.root_path),
            "generated": datetime.now().isoformat(),
            "statistics": {
                "total_files": self.total_files,
                "total_directories": self.total_dirs,
                "total_size": self.total_size if self.include_sizes else None,
                "max_depth": self.max_depth
            },
            "items": [
                {
                    "name": item.name,
                    "type": "directory" if item.is_dir else "file",
                    "path": str(item.path),
                    "depth": item.depth,
                    "size": item.size if self.include_sizes else None,
                    "file_count": item.file_count if item.is_dir else None,
                    "dir_count": item.dir_count if item.is_dir else None,
                }
                for item in items
            ]
        }

        return json.dumps(structure, indent=2, ensure_ascii=False)

    def generate_visual_format(self, items: List[FileInfo]) -> str:
        """Generate visual format with colors for terminal."""
        lines = [f"\033[1;36m{self.root_path.name}/\033[0m"]

        for i, item in enumerate(items):
            prefix = ""
            for _ in range(item.depth):
                prefix += "    "

            is_last = (i == len(items) - 1) or (
                    i + 1 < len(items) and items[i + 1].depth <= item.depth
            )
            connector = "└── " if is_last else "├── "

            if item.is_dir:
                # Blue for directories
                color = "\033[1;34m"
                indicator = "📁"
                info = f" ({item.file_count}f, {item.dir_count}d"
                if self.include_sizes:
                    info += f", {self._format_size(item.size)}"
                info += ")"
            else:
                # Green for files
                color = "\033[0;32m"
                indicator = "📄"
                info = ""
                if self.include_sizes:
                    info = f" ({self._format_size(item.size)})"

            reset = "\033[0m"
            lines.append(f"{prefix}{connector}{indicator} {color}{item.name}{reset}{info}")

        return "\n".join(lines)

    def generate(self, output_format: str = "tree") -> str:
        """
        Generate tree in specified format.

        Args:
            output_format: Output format (tree, json, markdown, visual)

        Returns:
            Formatted tree string
        """
        items = self.build_tree()

        if output_format == OutputFormat.TREE.value:
            return self.generate_tree_format(items)
        elif output_format == OutputFormat.TREE_DETAILED.value:
            return self.generate_tree_detailed_format(items)
        elif output_format == OutputFormat.JSON.value:
            return self.generate_json_format(items)
        elif output_format == OutputFormat.MARKDOWN.value:
            return self.generate_markdown_format(items)
        elif output_format == OutputFormat.VISUAL.value:
            return self.generate_visual_format(items)
        else:
            raise ValueError(f"Unknown output format: {output_format}")

    def generate_and_save(
            self,
            output_format: str = "tree",
            output_file: Optional[str] = None
    ) -> Optional[Path]:
        """
        Generate tree and optionally save to file.

        Args:
            output_format: Output format
            output_file: Optional output file path

        Returns:
            Path to saved file, or None if no file specified
        """
        tree_content = self.generate(output_format)

        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(tree_content)

            return output_path

        return None


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(
        description='Generate project folder structure tree',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate simple tree for current directory
  python utils/generate_tree.py

  # Generate detailed tree with file sizes
  python utils/generate_tree.py --detailed --sizes

  # Generate JSON format and save to file
  python utils/generate_tree.py --format json --output tree.json

  # Generate markdown for specific directory
  python utils/generate_tree.py /path/to/project --format markdown --output README_STRUCTURE.md

  # Limit depth and include hidden files
  python utils/generate_tree.py --max-depth 3 --hidden

  # Generate visual output (colors in terminal)
  python utils/generate_tree.py --format visual --sizes
        '''
    )

    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        help='Root directory path (default: current directory)'
    )

    parser.add_argument(
        '--format',
        '-f',
        choices=['tree', 'tree_detailed', 'json', 'markdown', 'visual'],
        default='tree',
        help='Output format (default: tree)'
    )

    parser.add_argument(
        '--output',
        '-o',
        help='Output file path (if not specified, prints to stdout)'
    )

    parser.add_argument(
        '--detailed',
        '-d',
        action='store_true',
        help='Show detailed information (files, dirs, sizes)'
    )

    parser.add_argument(
        '--sizes',
        '-s',
        action='store_true',
        help='Include file/directory sizes'
    )

    parser.add_argument(
        '--max-depth',
        '-m',
        type=int,
        default=-1,
        help='Maximum depth to traverse (default: unlimited)'
    )

    parser.add_argument(
        '--hidden',
        action='store_true',
        help='Include hidden files and directories'
    )

    parser.add_argument(
        '--ignore-dir',
        action='append',
        dest='ignore_dirs',
        help='Additional directory names to ignore (can be used multiple times)'
    )

    parser.add_argument(
        '--ignore-file',
        action='append',
        dest='ignore_files',
        help='Additional file extensions to ignore (can be used multiple times)'
    )

    args = parser.parse_args()

    try:
        # Build ignore sets
        ignore_dirs = TreeGenerator.DEFAULT_IGNORE_DIRS.copy()
        if args.ignore_dirs:
            ignore_dirs.update(args.ignore_dirs)

        ignore_files = TreeGenerator.DEFAULT_IGNORE_FILES.copy()
        if args.ignore_files:
            ignore_files.update(args.ignore_files)

        # Determine output format
        output_format = 'tree_detailed' if args.detailed else args.format

        # Create generator
        generator = TreeGenerator(
            root_path=args.path,
            ignore_dirs=ignore_dirs,
            ignore_files=ignore_files,
            max_depth=args.max_depth,
            include_hidden=args.hidden,
            include_sizes=args.sizes or args.detailed
        )

        # Generate and save
        output_path = generator.generate_and_save(
            output_format=output_format,
            output_file=args.output
        )

        # Generate tree
        tree_content = generator.generate(output_format)

        # Print to stdout
        print(tree_content)

        # Print statistics
        print(f"\n{'=' * 80}")
        print(f"📊 Statistics:")
        print(f"   Total Files: {generator.total_files}")
        print(f"   Total Directories: {generator.total_dirs}")
        if args.sizes or args.detailed:
            print(f"   Total Size: {generator._format_size(generator.total_size)}")
        print(f"{'=' * 80}")

        if output_path:
            print(f"\n✅ Output saved to: {output_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
