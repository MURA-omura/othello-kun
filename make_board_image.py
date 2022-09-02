from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGB', (460, 460), (32, 128, 32))
draw = ImageDraw.Draw(img)
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans', 30)

# 線の描画
for x in range(9):
    draw_x = x * 50 + 50
    draw.line((draw_x, 50, draw_x, 450), fill=(192, 192, 192), width=2)
    if x < 8:
        draw.text((draw_x + 15, 10), chr(ord('a') + x), fill=(192, 192, 192), font=font)

for y in range(9):
    draw_y = y * 50 + 50
    draw.line((50, draw_y, 450, draw_y), fill=(192, 192, 192), width=2)
    if y < 8:
        draw.text((15, draw_y + 10), str(y + 1), fill=(192, 192, 192), font=font)

# 行と列の追加

img.save('board_template.png')
