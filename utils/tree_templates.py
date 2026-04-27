"""
Pre-built tree generation templates for common use cases.
"""

from pathlib import Path
from utils.generate_tree import TreeGenerator, OutputFormat


class TreeTemplates:
    """Collection of pre-built tree generation templates."""

    @staticmethod
    def project_overview(
            root_path: str,
            output_file: str = "PROJECT_STRUCTURE.md"
    ) -> Path:
        """
        Generate comprehensive project overview with markdown format.

        Args:
            root_path: Root directory of project
            output_file: Output file path

        Returns:
            Path to generated file
        """
        generator = TreeGenerator(
            root_path=root_path,
            include_sizes=True
        )

        return generator.generate_and_save(
            output_format=OutputFormat.MARKDOWN.value,
            output_file=output_file
        )

    @staticmethod
    def source_code_tree(
            root_path: str,
            max_depth: int = 4,
            output_file: str = "SOURCE_TREE.txt"
    ) -> Path:
        """
        Generate source code tree (ignores build artifacts, caches, etc.).

        Args:
            root_path: Root directory
            max_depth: Maximum depth to show
            output_file: Output file path

        Returns:
            Path to generated file
        """
        ignore_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', '.pytest_cache', '.mypy_cache',
            'dist', 'build', '.egg-info', 'htmlcov'
        }

        generator = TreeGenerator(
            root_path=root_path,
            ignore_dirs=ignore_dirs,
            max_depth=max_depth,
            include_sizes=False
        )

        return generator.generate_and_save(
            output_format=OutputFormat.TREE.value,
            output_file=output_file
        )

    @staticmethod
    def data_files_tree(
            root_path: str,
            output_file: str = "DATA_FILES.json"
    ) -> Path:
        """
        Generate detailed data files tree in JSON format.

        Args:
            root_path: Root directory
            output_file: Output file path

        Returns:
            Path to generated file
        """
        generator = TreeGenerator(
            root_path=root_path,
            include_sizes=True,
            max_depth=5
        )

        return generator.generate_and_save(
            output_format=OutputFormat.JSON.value,
            output_file=output_file
        )

    @staticmethod
    def agents_tree(
            root_path: str,
            output_file: str = "AGENTS_STRUCTURE.txt"
    ) -> Path:
        """
        Generate agents directory structure specifically.

        Args:
            root_path: agents directory path
            output_file: Output file path

        Returns:
            Path to generated file
        """
        ignore_files = {'.pyc', '.pyo', '__pycache__'}

        generator = TreeGenerator(
            root_path=root_path,
            ignore_files=ignore_files,
            include_sizes=True
        )

        return generator.generate_and_save(
            output_format=OutputFormat.TREE_DETAILED.value,
            output_file=output_file
        )

    @staticmethod
    def schemas_tree(
            root_path: str,
            output_file: str = "SCHEMAS_STRUCTURE.md"
    ) -> Path:
        """
        Generate schemas directory structure specifically.

        Args:
            root_path: agents/schemas directory path
            output_file: Output file path

        Returns:
            Path to generated file
        """
        generator = TreeGenerator(
            root_path=root_path,
            max_depth=-1,
            include_sizes=False
        )

        return generator.generate_and_save(
            output_format=OutputFormat.MARKDOWN.value,
            output_file=output_file
        )


def print_project_structure():
    """Print full project structure to console."""
    generator = TreeGenerator(
        root_path='.',
        include_sizes=True
    )

    print("\n" + "=" * 80)
    print("PROJECT STRUCTURE")
    print("=" * 80 + "\n")

    tree = generator.generate(OutputFormat.TREE_DETAILED.value)
    print(tree)

    print(f"\n{'=' * 80}")
    print(f"📊 Statistics:")
    print(f"   Total Files: {generator.total_files}")
    print(f"   Total Directories: {generator.total_dirs}")
    print(f"   Total Size: {generator._format_size(generator.total_size)}")
    print(f"{'=' * 80}\n")


if __name__ == '__main__':
    print_project_structure()
