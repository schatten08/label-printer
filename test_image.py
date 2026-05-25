import sys
import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

def generate_test(text_str, output_path):
    Code128 = barcode.get_barcode_class('code128')
    options = { 'write_text': False, 'module_height': 7.0, 'module_width': 0.35, 'quiet_zone': 0.0 }
    my_bc = Code128(text_str, writer=ImageWriter())
    my_bc.save(output_path + '_bc', options=options)
    bc_img = Image.open(output_path + '_bc.png')
    font = None
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/timesbd.ttf', 45)
    except:
        font = ImageFont.load_default()
    canvas_w = 696
    top_text = 'EPAm ' + text_str
    dummy_draw = ImageDraw.Draw(Image.new('RGB', (1,1)))
    try:
        bbox = font.getbbox(top_text)
        text_w = bbox[2] - bbox[0]
        text_h = 45
    except:
        text_w, text_h = dummy_draw.textsize(top_text, font=font)
        text_h = 45
    margin_y = 60
    spacing = 15
    canvas_h = max(290, text_h + bc_img.height + spacing + (margin_y * 2))
    margin_y = (canvas_h - (text_h + spacing + bc_img.height)) // 2
    canvas = Image.new('RGB', (canvas_w, canvas_h), 'white')
    draw = ImageDraw.Draw(canvas)
    text_x = (canvas_w - text_w) // 2
    draw.text((text_x, margin_y), top_text, fill='black', font=font)
    bc_x = (canvas_w - bc_img.width) // 2
    canvas.paste(bc_img, (bc_x, margin_y + text_h + spacing))
    canvas.save(output_path + '_final.png', 'PNG', dpi=(300.0, 300.0))
    print(f'Canvas: {canvas_w}x{canvas_h}, TextW: {text_w}, BcW: {bc_img.width}')

generate_test('1121502', 'tester')
