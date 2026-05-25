import codecs

with codecs.open('src/mac_version/print_gui_mac.py', 'r', 'utf-8-sig') as f:
    text = f.read()

# Fix the 18-space indentation to 16-space indentation
fixed_text = text.replace('\n                  # Используем', '\n                # Используем')
fixed_text = fixed_text.replace('\n                  try:', '\n                try:')
fixed_text = fixed_text.replace('\n                      import os', '\n                    import os')
fixed_text = fixed_text.replace('\n                      from brother_ql', '\n                    from brother_ql')
fixed_text = fixed_text.replace('\n                      qlr =', '\n                    qlr =')
fixed_text = fixed_text.replace('\n                      # Транслируем', '\n                    # Транслируем')
fixed_text = fixed_text.replace('\n                      instructions =', '\n                    instructions =')
fixed_text = fixed_text.replace('\n                          qlr=qlr', '\n                        qlr=qlr')
fixed_text = fixed_text.replace('\n                          images=[image_path]', '\n                        images=[image_path]')
fixed_text = fixed_text.replace('\n                          label=', '\n                        label=')
fixed_text = fixed_text.replace('\n                          rotate=', '\n                        rotate=')
fixed_text = fixed_text.replace('\n                          threshold=', '\n                        threshold=')
fixed_text = fixed_text.replace('\n                          dither=', '\n                        dither=')
fixed_text = fixed_text.replace('\n                          compress=', '\n                        compress=')
fixed_text = fixed_text.replace('\n                          red=', '\n                        red=')
fixed_text = fixed_text.replace('\n                      )', '\n                    )')
fixed_text = fixed_text.replace('\n                      bin_path =', '\n                    bin_path =')
fixed_text = fixed_text.replace('\n                      with open', '\n                    with open')
fixed_text = fixed_text.replace('\n                          f.write', '\n                        f.write')
fixed_text = fixed_text.replace('\n                      # Отправляем', '\n                    # Отправляем')
fixed_text = fixed_text.replace('\n                      cmd =', '\n                    cmd =')
fixed_text = fixed_text.replace('\n                  except Exception as e:', '\n                except Exception as e:')
fixed_text = fixed_text.replace('\n                      # Если что-то', '\n                    # Если что-то')
fixed_text = fixed_text.replace('\n                      print("brother_ql', '\n                    print("brother_ql')

with codecs.open('src/mac_version/print_gui_mac.py', 'w', 'utf-8-sig') as f:
    f.write(fixed_text)

print("Indentation fixed.")
