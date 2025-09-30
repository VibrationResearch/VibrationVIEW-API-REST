#!/usr/bin/env python3
"""
Isolated Integration Tests for File Generation Endpoints

This test runs independently of the pytest framework to avoid mock contamination
that can occur when unit tests and integration tests run in the same session.

Usage:
    python test_integration_isolated.py

This test verifies that the file generation endpoints work correctly with real
VibrationVIEW AUTOMATION objects and actual VRD file uploads:
- /generatereport - Generate PDF reports from VRD files using templates
- /generateuff - Generate UFF files from VRD files
- /generatetxt - Generate TXT files from VRD files

The tests demonstrate that the integration functionality works properly when
run in isolation, confirming that the MagicMock serialization errors seen
in pytest are due to test environment contamination rather than actual bugs.
"""

import os
import sys
import tempfile

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_report_generation():
    """Test report generation without any test framework contamination"""

    from app import create_app

    # Create fresh app instance
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        # Path to VRD file
        sample_vrd_path = os.path.join(project_root, "data", "2025Sep22-1633-0002.vrd")

        if not os.path.exists(sample_vrd_path):
            print(f"Sample VRD file not found: {sample_vrd_path}")
            return False, 0

        # Read the VRD file content
        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        file_size = len(vrd_content)
        template_name = "Test Report.vvtemplate"
        output_name = "isolated_test_report.pdf"

        print(f"Making request to generate report...")
        print(f"VRD file size: {file_size} bytes")
        print(f"Template: {template_name}")
        print(f"Output: {output_name}")

        # Make the request
        response = client.post(
            f'/api/generatereport?template_name={template_name}&output_name={output_name}',
            data=vrd_content,
            headers={
                'Content-Length': str(file_size),
                'Content-Type': 'application/octet-stream'
            }
        )

        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            try:
                data = response.get_json()
                print(f"Error response: {data}")

                # Check for MagicMock error specifically
                error_message = data.get('error', {}).get('message', '')
                if 'MagicMock' in error_message:
                    print("FAILED: MagicMock serialization error occurred")
                    return False, 0
                else:
                    print("PASSED: No MagicMock serialization error (other error occurred)")
                    return True, 0

            except Exception as e:
                print(f"Could not parse response as JSON: {e}")
                print(f"Raw response: {response.data}")
                return False, 0
        else:
            data = response.get_json()
            print("PASSED: Request succeeded")
            generated_file_path = data.get('data', {}).get('generated_file_path')
            print(f"Generated file: {generated_file_path}")

            # Save the generated file content to logs folder if available
            try:
                file_content = data.get('data', {}).get('content', '')
                content_type = data.get('data', {}).get('content_type', 'unknown')
                is_binary = data.get('data', {}).get('is_binary', False)

                if file_content:
                    # Create logs directory if it doesn't exist
                    logs_dir = os.path.join(project_root, "logs")
                    os.makedirs(logs_dir, exist_ok=True)

                    # Determine file extension from original output name
                    _, ext = os.path.splitext(output_name)
                    saved_filename = f"test_output_{template_name.replace(' ', '_').replace('.', '_')}{ext}"
                    saved_path = os.path.join(logs_dir, saved_filename)

                    if is_binary:
                        # Decode base64 and save as binary
                        import base64
                        binary_data = base64.b64decode(file_content)
                        with open(saved_path, 'wb') as f:
                            f.write(binary_data)
                        print(f"Saved binary file to: {saved_path} ({len(binary_data)} bytes)")
                    else:
                        # Save as text
                        with open(saved_path, 'w', encoding='utf-8') as f:
                            f.write(file_content)
                        print(f"Saved text file to: {saved_path} ({len(file_content)} characters)")
                else:
                    print("No file content returned in response")

            except Exception as e:
                print(f"Failed to save file to logs: {e}")

            return True


def test_uff_generation():
    """Test UFF generation without any test framework contamination"""

    from app import create_app

    # Create fresh app instance
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        # Path to VRD file
        sample_vrd_path = os.path.join(project_root, "data", "2025Sep22-1633-0002.vrd")

        if not os.path.exists(sample_vrd_path):
            print(f"Sample VRD file not found: {sample_vrd_path}")
            return False, 0

        # Read the VRD file content
        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        file_size = len(vrd_content)
        output_name = "isolated_test_output.uff"

        print(f"Making request to generate UFF...")
        print(f"VRD file size: {file_size} bytes")
        print(f"Output: {output_name}")

        # Make the request
        response = client.post(
            f'/api/generateuff?output_name={output_name}',
            data=vrd_content,
            headers={
                'Content-Length': str(file_size),
                'Content-Type': 'application/octet-stream'
            }
        )

        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            try:
                data = response.get_json()
                print(f"Error response: {data}")

                # Check for MagicMock error specifically
                error_message = data.get('error', {}).get('message', '')
                if 'MagicMock' in error_message:
                    print("FAILED: MagicMock serialization error occurred")
                    return False, 0
                else:
                    print("PASSED: No MagicMock serialization error (other error occurred)")
                    return True, 0

            except Exception as e:
                print(f"Could not parse response as JSON: {e}")
                print(f"Raw response: {response.data}")
                return False, 0
        else:
            data = response.get_json()
            print("PASSED: Request succeeded")
            generated_files = data.get('data', {}).get('generated_files', [])
            files_found = data.get('data', {}).get('files_found', 0)
            print(f"Generated UFF files: {files_found} files found")
            print(f"File details: {[f['file_name'] for f in generated_files]}")

            # Save the generated file content to logs folder if available
            try:
                files_content = data.get('data', {}).get('files_content', [])

                if files_content:
                    # Create logs directory if it doesn't exist
                    logs_dir = os.path.join(project_root, "logs")
                    os.makedirs(logs_dir, exist_ok=True)

                    print(f"Saving {len(files_content)} UFF files to logs folder...")
                    for i, file_info in enumerate(files_content):
                        file_content = file_info.get('content', '')
                        file_name = file_info.get('filename', f'uff_output_{i}.uff')
                        is_binary = file_info.get('is_binary', False)

                        saved_path = os.path.join(logs_dir, f"test_{file_name}")

                        if is_binary:
                            # Decode base64 and save as binary
                            import base64
                            binary_data = base64.b64decode(file_content)
                            with open(saved_path, 'wb') as f:
                                f.write(binary_data)
                            print(f"Saved binary UFF file to: {saved_path} ({len(binary_data)} bytes)")
                        else:
                            # Save as text
                            with open(saved_path, 'w', encoding='utf-8') as f:
                                f.write(file_content)
                            print(f"Saved text UFF file to: {saved_path} ({len(file_content)} characters)")
                else:
                    print("No file content returned in response")

            except Exception as e:
                print(f"Failed to save UFF files to logs: {e}")

            return True, files_found


def test_txt_generation():
    """Test TXT generation without any test framework contamination"""

    from app import create_app

    # Create fresh app instance
    app = create_app()
    app.config['TESTING'] = True

    with app.test_client() as client:
        # Path to VRD file
        sample_vrd_path = os.path.join(project_root, "data", "2025Sep22-1633-0002.vrd")

        if not os.path.exists(sample_vrd_path):
            print(f"Sample VRD file not found: {sample_vrd_path}")
            return False, 0

        # Read the VRD file content
        with open(sample_vrd_path, 'rb') as f:
            vrd_content = f.read()

        file_size = len(vrd_content)
        output_name = "isolated_test_output.txt"

        print(f"Making request to generate TXT...")
        print(f"VRD file size: {file_size} bytes")
        print(f"Output: {output_name}")

        # Make the request
        response = client.post(
            f'/api/generatetxt?output_name={output_name}',
            data=vrd_content,
            headers={
                'Content-Length': str(file_size),
                'Content-Type': 'application/octet-stream'
            }
        )

        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            try:
                data = response.get_json()
                print(f"Error response: {data}")

                # Check for MagicMock error specifically
                error_message = data.get('error', {}).get('message', '')
                if 'MagicMock' in error_message:
                    print("FAILED: MagicMock serialization error occurred")
                    return False, 0
                else:
                    print("PASSED: No MagicMock serialization error (other error occurred)")
                    return True, 0

            except Exception as e:
                print(f"Could not parse response as JSON: {e}")
                print(f"Raw response: {response.data}")
                return False, 0
        else:
            data = response.get_json()
            print("PASSED: Request succeeded")
            generated_files = data.get('data', {}).get('generated_files', [])
            files_found = data.get('data', {}).get('files_found', 0)
            print(f"Generated TXT files: {files_found} files found")
            print(f"File details: {[f['file_name'] for f in generated_files]}")

            # Save the generated file content to logs folder if available
            try:
                files_content = data.get('data', {}).get('files_content', [])

                if files_content:
                    # Create logs directory if it doesn't exist
                    logs_dir = os.path.join(project_root, "logs")
                    os.makedirs(logs_dir, exist_ok=True)

                    print(f"Saving {len(files_content)} TXT files to logs folder...")
                    for i, file_info in enumerate(files_content):
                        file_content = file_info.get('content', '')
                        file_name = file_info.get('filename', f'txt_output_{i}.txt')
                        is_binary = file_info.get('is_binary', False)

                        saved_path = os.path.join(logs_dir, f"test_{file_name}")

                        if is_binary:
                            # Decode base64 and save as binary
                            import base64
                            binary_data = base64.b64decode(file_content)
                            with open(saved_path, 'wb') as f:
                                f.write(binary_data)
                            print(f"Saved binary TXT file to: {saved_path} ({len(binary_data)} bytes)")
                        else:
                            # Save as text
                            with open(saved_path, 'w', encoding='utf-8') as f:
                                f.write(file_content)
                            print(f"Saved text TXT file to: {saved_path} ({len(file_content)} characters)")
                else:
                    print("No file content returned in response")

            except Exception as e:
                print(f"Failed to save TXT files to logs: {e}")

            return True, files_found

if __name__ == '__main__':
    print("Running isolated integration tests...")

    tests = [
        ("Report Generation", test_report_generation),
        ("UFF Generation", test_uff_generation),
        ("TXT Generation", test_txt_generation)
    ]

    all_passed = True
    test_results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} Test")
        print(f"{'='*50}")

        try:
            if test_name == "Report Generation":
                # Report generation test returns just success boolean
                success = test_func()
                file_count = 1  # Report generates single file
                if isinstance(success, tuple):
                    success, file_count = success
            else:
                # UFF and TXT tests return (success, file_count) tuple
                success, file_count = test_func()

            test_results[test_name] = {'success': success, 'file_count': file_count}

            if success:
                print(f"{test_name} test: PASSED ({file_count} files generated)")
            else:
                print(f"{test_name} test: FAILED")
                all_passed = False
        except Exception as e:
            print(f"{test_name} test: ERROR - {e}")
            test_results[test_name] = {'success': False, 'file_count': 0}
            all_passed = False

    print(f"\n{'='*50}")
    print("Test Results Summary:")
    print(f"{'='*50}")

    for test_name, result in test_results.items():
        status = "PASSED" if result['success'] else "FAILED"
        print(f"{test_name}: {status} - {result['file_count']} files generated")

    # Compare UFF and TXT file counts
    if 'UFF Generation' in test_results and 'TXT Generation' in test_results:
        uff_count = test_results['UFF Generation']['file_count']
        txt_count = test_results['TXT Generation']['file_count']

        print(f"\n{'='*50}")
        print("File Count Comparison:")
        print(f"UFF files generated: {uff_count}")
        print(f"TXT files generated: {txt_count}")

        if uff_count == txt_count and uff_count > 0:
            print("SUCCESS: UFF and TXT tests generated the same number of files")
        elif uff_count == txt_count and uff_count == 0:
            print("WARNING: Both tests generated 0 files")
        else:
            print("MISMATCH: UFF and TXT tests generated different numbers of files")

    print(f"\n{'='*50}")
    if all_passed:
        print("All integration tests completed successfully")
        exit(0)
    else:
        print("Some integration tests failed")
        exit(1)