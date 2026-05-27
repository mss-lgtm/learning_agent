from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    # 创建assets目录
    if not os.path.exists("assets"):
        os.makedirs("assets")

    # 创建不同尺寸的图标
    sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

    images = []
    for size in sizes:
        img = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 绘制圆角矩形背景
        margin = size[0] // 8
        draw.rounded_rectangle(
            [margin, margin, size[0] - margin, size[1] - margin],
            radius=size[0] // 6,
            fill="#FE2C55"  # 抖音红色
        )

        # 绘制文字
        try:
            font_size = size[0] // 3
            font = ImageFont.truetype("msyh.ttc", font_size)
        except:
            font = ImageFont.load_default()

        text = "抖"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2 - bbox[1]
        draw.text((x, y), text, fill="white", font=font)

        images.append(img)

    # 保存为ICO文件
    images[0].save(
        "assets/icon.ico",
        format="ICO",
        sizes=[(img.width, img.height) for img in images],
        append_images=images[1:]
    )

    print("图标已创建: assets/icon.ico")

if __name__ == "__main__":
    create_icon()
