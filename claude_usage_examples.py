"""
Claude Desktop Usage Examples
Copy these examples to use with Claude Desktop
"""

from claude_functions import *

# Example 1: Basic company analysis
print("=" * 60)
print("EXAMPLE 1: Single Company Analysis")
print("=" * 60)
result = analyze_single_company("INFY")
print(result)

# Example 2: Company comparison
print("\n" + "=" * 60)
print("EXAMPLE 2: Company Comparison")
print("=" * 60)
result = compare_companies(["INFY", "TCS"])
print(result)

# Example 3: Sector analysis
print("\n" + "=" * 60)
print("EXAMPLE 3: IT Sector Analysis")
print("=" * 60)
result = analyze_it_sector()
print(result)

# Example 4: Custom analysis
print("\n" + "=" * 60)
print("EXAMPLE 4: Custom Analysis")
print("=" * 60)
result = custom_analysis(["RELIANCE", "ADANIPORTS"])
print(result)