print("Hello from test script!")
import sys
print(f"Arguments: {sys.argv}")

if len(sys.argv) > 1 and sys.argv[1] == '--status':
    print("Status check requested")
else:
    print("No status check")