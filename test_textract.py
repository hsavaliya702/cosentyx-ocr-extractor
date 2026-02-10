"""Test if AWS Textract is working with a simple image."""
import io
from PIL import Image, ImageDraw, ImageFont
from src.ocr.textract_client import TextractClient

print("Creating a simple test image...")

# Create a simple test image with text
img = Image.new('RGB', (800, 400), color='white')
draw = ImageDraw.Draw(img)

# Add some text
text_lines = [
    "Patient First Name: John",
    "Patient Last Name: Doe",
    "Date of Birth: 01/15/1980",
    "Gender: M"
]

y_position = 50
for line in text_lines:
    draw.text((50, y_position), line, fill='black')
    y_position += 50

# Convert to bytes
img_bytes = io.BytesIO()
img.save(img_bytes, format='PNG')
img_bytes = img_bytes.getvalue()

print(f"Test image created: {len(img_bytes)} bytes")
print("\nTesting AWS Textract...")

try:
    client = TextractClient()
    response = client.analyze_document(img_bytes)
    print("✓ AWS Textract is working!")
    print(f"  Response contains {len(response.get('Blocks', []))} blocks")
    
    # Show some extracted text
    for block in response.get('Blocks', [])[:5]:
        if block.get('BlockType') == 'LINE':
            print(f"  Extracted: {block.get('Text')}")
            
except Exception as e:
    print(f"✗ AWS Textract failed: {e}")
    print("\nPossible issues:")
    print("1. AWS credentials not configured correctly")
    print("2. AWS region doesn't support Textract")
    print("3. IAM permissions missing (textract:AnalyzeDocument)")
    print("4. Bedrock not enabled in your region")
