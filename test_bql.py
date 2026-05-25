from PIL import Image
from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# Create a dummy image Wx306
img = Image.new('RGB', (1000, 306), 'white')
img.save("test_bql.png")

try:
    qlr = BrotherQLRaster('QL-810W')
    qlr.exception_on_warning = True
    
    instructions = convert(
        qlr=qlr, 
        images=["test_bql.png"], 
        label='29',
        rotate='90',       
        threshold=70.0,
        dither=False,
        compress=True,
        red=False
    )
    print("Success! Size of bin:", len(instructions))
except Exception as e:
    print("Error:", e)
