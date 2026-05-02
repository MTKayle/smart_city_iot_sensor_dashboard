"""Check line endings."""
with open('test_simple_create.sql', 'rb') as f:
    data = f.read()
    
print(f"Has CRLF (\\r\\n): {b'\\r\\n' in data}")
print(f"Has LF (\\n): {b'\\n' in data}")
print(f"Length: {len(data)}")
print(f"First 50 bytes hex: {data[:50].hex()}")
print(f"Last 50 bytes hex: {data[-50:].hex()}")
