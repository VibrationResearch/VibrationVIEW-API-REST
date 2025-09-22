"""
TEDS Data Formatter

Converts raw TEDS data from VibrationVIEW COM interface into structured JSON format.
"""

import re
from typing import List, Dict, Any, Optional, Union


def parse_numeric_value(value_str: str) -> Optional[float]:
    """
    Extract numeric value from a string, handling various formats.

    Args:
        value_str: String containing numeric value (e.g., "102.0", "10.001 mV/G")

    Returns:
        Float value or None if parsing fails
    """
    if not value_str:
        return None

    # Remove extra spaces and extract first numeric value
    match = re.search(r'[-+]?\d*\.?\d+', value_str.strip())
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def normalize_field_name(field_name: str) -> str:
    """
    Convert TEDS field name to normalized field name.

    Args:
        field_name: Original TEDS field name (e.g., "Model number")

    Returns:
        Normalized field name (e.g., "model_number")
    """
    return field_name.lower().replace(' ', '_').replace('(', '').replace(')', '').replace(',', '').replace('.', '')


def extract_teds_field(teds_data: List[List[str]], field_name: str) -> Dict[str, str]:
    """
    Extract a specific field from TEDS data array.

    Args:
        teds_data: List of [field_name, value, unit] arrays or tuples
        field_name: Name of field to extract

    Returns:
        Dictionary with 'value' and 'unit' keys
    """
    for item in teds_data:
        # Handle both list and tuple formats
        if len(item) >= 2:
            # Convert first element to string and check if it matches
            first_element = str(item[0]) if item[0] is not None else ''
            if first_element.lower() == field_name.lower():
                return {
                    'value': str(item[1]) if len(item) > 1 and item[1] is not None else '',
                    'unit': str(item[2]) if len(item) > 2 and item[2] is not None else ''
                }
    return {'value': '', 'unit': ''}


def extract_all_teds_fields(teds_data: List[List[str]], channel_index: int, include_channel: bool = True) -> Dict[str, Any]:
    """
    Extract all TEDS fields automatically using normalized field names.

    Args:
        teds_data: List of [field_name, value, unit] arrays or tuples
        channel_index: Zero-based channel index
        include_channel: Whether to include channel field in the output

    Returns:
        Dictionary with all fields using normalized names, optionally including channel reference
    """
    fields = {}

    # Only add channel if it's a valid channel index (not URN-based lookup) and requested
    if channel_index >= 0 and include_channel:
        fields['channel'] = channel_index + 1  # Convert to 1-based for user-friendly display

    for item in teds_data:
        if len(item) >= 2:
            # Convert first element to string and normalize field name
            original_field = str(item[0]) if item[0] is not None else ''
            if original_field:
                normalized_field = normalize_field_name(original_field)
                value = str(item[1]) if len(item) > 1 and item[1] is not None else ''
                unit = str(item[2]) if len(item) > 2 and item[2] is not None else ''

                # Store with normalized field name
                if value:  # Only store non-empty values
                    if unit:
                        # If there's a unit, try to parse as numeric
                        numeric_value = parse_numeric_value(value)
                        if numeric_value is not None:
                            fields[normalized_field] = {
                                'value': numeric_value,
                                'unit': unit
                            }
                        else:
                            fields[normalized_field] = {
                                'value': value,
                                'unit': unit
                            }
                    else:
                        # No unit, store as string
                        fields[normalized_field] = value

    return fields




def format_single_transducer_teds(teds_data: List[List[str]], channel_index: int, include_channel: bool = True) -> Dict[str, Any]:
    """
    Format TEDS data for a single transducer.

    Args:
        teds_data: Raw TEDS data for one transducer (can be lists or tuples)
        channel_index: Zero-based channel index
        include_channel: Whether to include channel field in the output

    Returns:
        Formatted transducer dictionary
    """
    # Validate input data format
    if not isinstance(teds_data, (list, tuple)):
        raise ValueError(f"Expected list or tuple for TEDS data, got {type(teds_data)}")

    # Handle different TEDS data formats:
    # 1. List of lists: [[field, value, unit], ...]
    # 2. List of tuples: [(field, value, unit), ...]
    # 3. Direct tuple of tuples: ((field, value, unit), ...)
    # 4. Single item containing list of tuples: [[(field, value, unit), ...]]
    normalized_data = []

    # Convert tuples to lists for consistent processing
    if isinstance(teds_data, tuple):
        teds_data = list(teds_data)

    # If we have a single item that contains the actual data, unwrap it
    if len(teds_data) == 1 and isinstance(teds_data[0], (list, tuple)):
        # Check if the first item is itself a list/tuple of field data
        first_item = teds_data[0]
        if len(first_item) > 0 and isinstance(first_item[0], (list, tuple)):
            # This is a nested structure like [[(field, value, unit), ...]]
            teds_data = first_item
        # Note: We don't unwrap if it's just a single field tuple like ('Manufacturer', 'Dytran', '')

    # Process each item
    for item in teds_data:
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            # Convert to list format for consistent processing
            # Ensure each element is properly converted to string
            converted_item = [
                str(item[0]) if item[0] is not None else '',
                str(item[1]) if len(item) > 1 and item[1] is not None else '',
                str(item[2]) if len(item) > 2 and item[2] is not None else ''
            ]
            normalized_data.append(converted_item)
        elif isinstance(item, str):
            # Skip string items that aren't in the expected format
            continue
        else:
            # Skip malformed items
            continue

    transducer = {}

    # Use normalized data for all field extractions
    teds_data = normalized_data

    # Check if we have any data to work with
    if not teds_data:
        return {
            'channel': channel_index,
            'error': 'No TEDS data available after normalization',
        }

    # Extract all TEDS fields automatically
    all_fields = extract_all_teds_fields(teds_data, channel_index, include_channel)

    # Add all fields to the transducer object
    transducer.update(all_fields)

    return transducer


def format_single_channel_teds(channel_data: Any, channel_index: int = 0) -> Dict[str, Any]:
    """
    Format TEDS data for a single channel.

    Args:
        channel_data: Raw TEDS data for one channel
        channel_index: Zero-based channel index

    Returns:
        Dictionary with either 'sensor' or 'error' key
    """
    if isinstance(channel_data, dict) and 'Error' in channel_data:
        # Error case
        error_data = {'error': channel_data['Error']}
        # Only add channel if it's a valid channel index (not URN-based lookup)
        if channel_index >= 0:
            error_data['channel'] = channel_index + 1  # Convert to 1-based

        return {'error': error_data}
    elif isinstance(channel_data, (list, tuple)) and len(channel_data) > 0:
        # Valid TEDS data - handle both list and tuple formats
        try:
            # For single channel responses, don't include channel in transducer block
            # since it's already provided at the response level
            transducer = format_single_transducer_teds(channel_data, channel_index, include_channel=False)
            return {'transducer': transducer}
        except Exception as e:
            # If formatting fails, return error
            error_data = {'error': f'Failed to format TEDS data: {str(e)}'}
            # Only add channel if it's a valid channel index (not URN-based lookup)
            if channel_index >= 0:
                error_data['channel'] = channel_index + 1  # Convert to 1-based

            return {'error': error_data}
    elif channel_data is None or (isinstance(channel_data, (list, tuple)) and len(channel_data) == 0):
        # Empty or None data
        error_data = {'error': 'No TEDS data available'}
        # Only add channel if it's a valid channel index (not URN-based lookup)
        if channel_index >= 0:
            error_data['channel'] = channel_index + 1  # Convert to 1-based

        return {'error': error_data}
    else:
        # Unknown data format
        error_data = {'error': f'Unknown TEDS data format: {type(channel_data)}'}
        # Only add channel if it's a valid channel index (not URN-based lookup)
        if channel_index >= 0:
            error_data['channel'] = channel_index + 1  # Convert to 1-based

        return {'error': error_data}


def format_teds_data(all_teds_data: List[Any]) -> Dict[str, Any]:
    """
    Format complete TEDS data into structured JSON.

    Args:
        all_teds_data: Raw TEDS data from VibrationVIEW API

    Returns:
        Formatted dictionary with transducers and errors arrays
    """
    result = {
        'transducers': [],
        'errors': []
    }

    for channel_index, channel_data in enumerate(all_teds_data):
        # For multi-channel list view, we need to include channel info in each transducer
        if isinstance(channel_data, (list, tuple)) and len(channel_data) > 0:
            # For valid data, include channel in transducer
            try:
                transducer = format_single_transducer_teds(channel_data, channel_index, include_channel=True)
                result['transducers'].append(transducer)
            except Exception as e:
                # If formatting fails, add to errors
                error_data = {'error': f'Failed to format TEDS data: {str(e)}'}
                if channel_index >= 0:
                    error_data['channel'] = channel_index + 1  # Convert to 1-based
                result['errors'].append(error_data)
        else:
            # For errors or empty data, add to errors
            error_data = {'error': 'No TEDS data available or invalid format'}
            if channel_index >= 0:
                error_data['channel'] = channel_index + 1  # Convert to 1-based
            result['errors'].append(error_data)

    return result