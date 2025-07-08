# backend/app/utils/benchtop/biology/imaging/filters/gaussian_blur_processor.py

import io
import numpy as np
from PIL import Image
from typing import Dict, Any

from app.schemas.benchtop.biology.imaging.filters.gaussian_blur_schema import GaussianBlurParams

# --- Main Processor Logic ---
def run(
    ij_gateway,  # The initialized PyImageJ gateway instance
    image_bytes: bytes,
    params: GaussianBlurParams
) -> Dict[str, Any]:
    """
    Applies a Gaussian blur to an image using ImageJ ops.

    This function follows the standard pattern for PyImageJ processing:
    1. Convert Python data (NumPy array) into ImageJ data types (Dataset).
    2. Run the desired ImageJ operation(s).
    3. Convert the ImageJ result back into Python data types.

    Args:
        ij_gateway: The active PyImageJ gateway from the ImageJService.
        image_bytes: The input image as bytes (e.g., from an uploaded file).
        params: A Pydantic model containing validated parameters for the filter.

    Returns:
        A dictionary containing the processed image as bytes (in PNG format)
        and a summary of the operation.
    """
    # 1. Convert input bytes to a NumPy array
    # Using PIL (Pillow) as an intermediate to handle various image formats.
    pil_image = Image.open(io.BytesIO(image_bytes))
    
    # For this initial implementation, we will process the image in its original mode
    # if it's a common type like Grayscale (L) or RGB. More complex modes might
    # require specific handling in future iterations.
    original_mode = pil_image.mode
    if original_mode not in ['L', 'RGB', 'RGBA']:
        # Convert to a standard mode (e.g., RGB) to ensure compatibility.
        pil_image = pil_image.convert('RGB')

    input_array = np.array(pil_image)

    # 2. Convert NumPy array to an ImageJ2 Dataset object
    # The gateway's `py.to_dataset` helper handles this conversion.
    ij_dataset = ij_gateway.py.to_dataset(input_array)

    # 3. Run the Gaussian Blur command from the ImageJ Ops framework
    # This is the core processing step. We call the 'gauss' op within the 'filter' namespace.
    # The result is another ImageJ2 Dataset object.
    blurred_dataset = ij_gateway.op().filter().gauss(ij_dataset, params.sigma)

    # 4. Convert the resulting ImageJ2 Dataset back to a NumPy array
    # The gateway's `py.from_java` helper handles the conversion back to a Python object.
    output_array = ij_gateway.py.from_java(blurred_dataset)

    # 5. Convert output NumPy array back to image bytes (in PNG format) for storage/display
    output_image = Image.fromarray(output_array)
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    output_bytes = output_buffer.getvalue()

    # 6. Construct the final result dictionary
    result = {
        "processed_image_bytes": output_bytes,
        "summary": {
            "filter_applied": "Gaussian Blur",
            "parameters_used": params.model_dump(),
            "original_dimensions": f"{pil_image.width}x{pil_image.height}",
            "original_mode": original_mode,
        }
    }
    return result