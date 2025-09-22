# ============================================================================
# FILE: utils/path_validator.py (Path Validation Utilities) - v1
# ============================================================================

"""
Path validation utilities for securing file operations
Ensures file paths are restricted to authorized directories
"""

from pathlib import Path
from typing import Union, List
from config import Config


class PathValidationError(Exception):
    """Raised when a path validation check fails"""
    pass


def get_authorized_directories() -> List[str]:
    """
    Get list of authorized directories from configuration

    Returns:
        List of authorized directory paths
    """
    directories = []

    # Add configured directories if they exist
    if hasattr(Config, 'REPORT_FOLDER') and Config.REPORT_FOLDER:
        directories.append(Config.REPORT_FOLDER)

    if hasattr(Config, 'PROFILE_FOLDER') and Config.PROFILE_FOLDER:
        directories.append(Config.PROFILE_FOLDER)

    # Add DATA_FOLDER if it exists (to be added to config)
    if hasattr(Config, 'DATA_FOLDER') and Config.DATA_FOLDER:
        directories.append(Config.DATA_FOLDER)

    return directories


def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path to resolve any relative components and symlinks

    Args:
        path: Path to normalize

    Returns:
        Normalized absolute Path object
    """
    return Path(path).resolve()


def is_path_within_authorized_directories(file_path: Union[str, Path]) -> bool:
    """
    Check if a file path is within any of the authorized directories

    Args:
        file_path: Path to validate

    Returns:
        True if path is within authorized directories, False otherwise
    """
    try:
        normalized_path = normalize_path(file_path)
        authorized_dirs = get_authorized_directories()

        for auth_dir in authorized_dirs:
            auth_dir_normalized = normalize_path(auth_dir)
            try:
                # Check if the file path is within the authorized directory
                normalized_path.relative_to(auth_dir_normalized)
                return True
            except ValueError:
                # Path is not relative to this authorized directory
                continue

        return False
    except Exception:
        # Any error in path processing should result in rejection
        return False


def validate_file_path(file_path: Union[str, Path], operation: str = "access") -> str:
    """
    Validate that a file path is within authorized directories

    Args:
        file_path: Path to validate
        operation: Description of the operation for error messages

    Returns:
        Normalized path string if valid

    Raises:
        PathValidationError: If path is not authorized
    """
    if not file_path:
        raise PathValidationError(f"Empty file path not allowed for {operation}")

    # Convert to string for consistency
    path_str = str(file_path)

    # Check for obvious path traversal attempts
    # Allow Windows drive letters (C:, D:, etc.) but detect other colons that might indicate injection
    if '..' in path_str or path_str.startswith('/'):
        raise PathValidationError(f"Path traversal detected in path: {path_str}")

    # Check for colons that are not Windows drive letters (position 1)
    if ':' in path_str:
        colon_positions = [i for i, char in enumerate(path_str) if char == ':']
        # Allow only the first colon at position 1 (C:, D:, etc.)
        if len(colon_positions) > 1 or (len(colon_positions) == 1 and colon_positions[0] != 1):
            raise PathValidationError(f"Path traversal detected in path: {path_str}")

    # Normalize and check against authorized directories
    if not is_path_within_authorized_directories(file_path):
        authorized_dirs = get_authorized_directories()
        raise PathValidationError(
            f"File path '{file_path}' is not within authorized directories for {operation}. "
            f"Authorized directories: {', '.join(authorized_dirs)}"
        )

    # Return normalized path
    return str(normalize_path(file_path))


def validate_output_path(output_name: Union[str, Path], operation: str = "output") -> str:
    """
    Validate an output file path for report generation

    This function handles both relative filenames and full paths.
    For relative filenames, it places them in the REPORT_FOLDER.
    For full paths, it validates they are within authorized directories.

    Args:
        output_name: Output filename or path
        operation: Description of the operation for error messages

    Returns:
        Validated absolute path string

    Raises:
        PathValidationError: If path is not authorized
    """
    if not output_name:
        raise PathValidationError(f"Empty output name not allowed for {operation}")

    output_path = Path(output_name)

    # If it's just a filename (no directory separators), place it in REPORT_FOLDER
    if not output_path.parent or str(output_path.parent) == '.':
        report_folder = getattr(Config, 'REPORT_FOLDER', None)
        if not report_folder:
            raise PathValidationError("No REPORT_FOLDER configured for output files")

        full_path = Path(report_folder) / output_path.name
        return str(normalize_path(full_path))

    # For paths with directories, validate against authorized directories
    return validate_file_path(output_path, operation)


def secure_path_join(base_dir: Union[str, Path], *paths: Union[str, Path]) -> str:
    """
    Securely join paths ensuring the result stays within the base directory

    Args:
        base_dir: Base directory that result must stay within
        *paths: Path components to join

    Returns:
        Validated joined path string

    Raises:
        PathValidationError: If resulting path would escape base directory
    """
    base_normalized = normalize_path(base_dir)

    # Join the paths
    joined_path = base_normalized
    for path_component in paths:
        joined_path = joined_path / path_component

    # Normalize the final path
    final_path = normalize_path(joined_path)

    # Ensure the final path is still within the base directory
    try:
        final_path.relative_to(base_normalized)
    except ValueError:
        raise PathValidationError(
            f"Path '{final_path}' would escape base directory '{base_normalized}'"
        )

    return str(final_path)