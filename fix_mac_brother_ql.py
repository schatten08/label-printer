import codecs
import re

with codecs.open('src/mac_version/requirements.txt', 'a', 'utf-8-sig') as f:
    f.write('\nbrother_ql>=0.9.4\n')

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# Обновляем сообщение об ошибке импорта
text = text.replace('pip3 install python-barcode Pillow"', 'pip3 install python-barcode Pillow brother_ql"')

# Изменяем размер холста для brother_ql (он строго требует 306 пикселей в высоту для 29мм ленты)
text = text.replace('canvas_h = 342', 'canvas_h = 306')

new_lpr = '''
                  # Используем независимый открытый SDK (brother_ql) вместо глючного драйвера macOS CUPS
                  try:
                      import os
                      from brother_ql.conversion import convert
                      from brother_ql.raster import BrotherQLRaster
                      
                      qlr = BrotherQLRaster('QL-810W')
                      qlr.exception_on_warning = True
                      
                      # Транслируем картинку в чистый двоичный машинный код принтера
                      instructions = convert(
                          qlr=qlr, 
                          images=[image_path], 
                          label='29',       # Указываем 29мм ленту
                          rotate='0',       
                          threshold=70.0,
                          dither=False,
                          compress=True,
                          red=False
                      )
                      
                      bin_path = image_path + ".bin"
                      with open(bin_path, 'wb') as f:
                          f.write(instructions)
                          
                      # Отправляем сырой код прямо на интерфейс принтера (-l = RAW format)
                      cmd = ["lpr", "-P", selected_printer, "-l", bin_path]
                  except Exception as e:
                      # Если что-то пошло не так, падаем в классический способ
                      print("brother_ql error:", e)
                      cmd = ["lpr", "-P", selected_printer, "-o", "natural-scaling=100", image_path]
'''

# Ищем старый вызов cmd и заменяем
# Внимание: отступы важны, мы внутри for num in numbers / try
old_lpr = 'cmd = ["lpr", "-P", selected_printer, "-o", "natural-scaling=100", image_path]'

if old_lpr in text:
    text = text.replace(old_lpr, new_lpr)
else:
    print("Cannot find old cmd!")

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(text)

print("brother_ql SDK integrated!")
