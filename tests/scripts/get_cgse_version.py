"""
This script runs a function from an external package that is installed at a different location.

The purpose of this script is to check that the PYTHONPATH or sys.path are properly set.
"""

from egse import version

print(f"CGSE Version = {version.VERSION}")
