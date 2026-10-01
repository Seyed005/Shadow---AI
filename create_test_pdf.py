import fitz
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path


output_dir = Path("sample_data/synthetic_attacks")
output_dir.mkdir(parents=True, exist_ok=True)

pdf_path = output_dir / "test_sensitive.pdf"
image_path = output_dir / "scanned_page.png"


# --------------------------------------------------
# Create an image that simulates a scanned document
# --------------------------------------------------

image = Image.new("RGB", (1600, 1000), "white")
draw = ImageDraw.Draw(image)

font = ImageFont.truetype(
    "C:/Windows/Fonts/arial.ttf",
    42
)

lines = [
    "CONFIDENTIAL SECURITY RECORD",
    "",
    "Employee ID: EMP-2026-0042",
    "Email: research@example.com",
    "Password: DemoPass123",
    "Server: 192.168.1.10",
]

y = 100

for line in lines:
    draw.text(
        (100, y),
        line,
        fill="black",
        font=font
    )
    y += 100

image.save(image_path)


# --------------------------------------------------
# Create PDF
# --------------------------------------------------

document = fitz.open()


# PAGE 1 — embedded text
page1 = document.new_page()

page1.insert_text(
    (72, 100),
    "CONFIDENTIAL SECURITY RECORD",
    fontsize=18
)

page1.insert_text(
    (72, 150),
    "Employee ID: EMP-2026-0042",
    fontsize=14
)

page1.insert_text(
    (72, 180),
    "Email: research@example.com",
    fontsize=14
)

page1.insert_text(
    (72, 210),
    "Password: DemoPass123",
    fontsize=14
)

page1.insert_text(
    (72, 240),
    "Server: 192.168.1.10",
    fontsize=14
)


# PAGE 2 — scanned/image content
page2 = document.new_page()

page2.insert_image(
    page2.rect,
    filename=str(image_path)
)


document.save(pdf_path)
document.close()

print("Test PDF created successfully.")
print(f"Location: {pdf_path}")