"""生成应用图标 icon.ico：蓝色渐变圆角方块 + 白色「字」+ 字幕条。"""
from PIL import Image, ImageDraw, ImageFont

SIZE = 256
img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

# 1) 蓝色渐变背景
grad = Image.new("RGBA", (SIZE, SIZE))
gd = ImageDraw.Draw(grad)
c1 = (59, 130, 246)   # #3B82F6
c2 = (99, 102, 241)   # #6366F1
for y in range(SIZE):
    t = y / SIZE
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    gd.line([(0, y), (SIZE, y)], fill=(r, g, b, 255))

# 2) 圆角裁剪
mask = Image.new("L", (SIZE, SIZE), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=56, fill=255)
img.paste(grad, (0, 0), mask)

draw = ImageDraw.Draw(img)

# 3) 白色「字」字，居中偏上
font = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 128)
text = "字"
bbox = draw.textbbox((0, 0), text, font=font)
tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
draw.text(
    ((SIZE - tw) / 2 - bbox[0], (SIZE - th) / 2 - bbox[1] - 30),
    text, font=font, fill=(255, 255, 255, 255),
)

# 4) 底部字幕条（短的上句 + 长的当前句）
draw.rounded_rectangle([72, 178, 150, 188], radius=5, fill=(255, 255, 255, 150))
draw.rounded_rectangle([48, 198, 208, 216], radius=9, fill=(255, 255, 255, 240))

# 5) 保存多尺寸 ico
img.save("F:/zimu/icon.ico", format="ICO",
         sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("icon.ico 已生成")
