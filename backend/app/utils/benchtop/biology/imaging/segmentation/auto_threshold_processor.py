# backend/app/utils/benchtop/biology/imaging/segmentation/auto_threshold_processor.py

import io
import numpy as np
from PIL import Image
from typing import Dict, Any

from app.schemas.benchtop.biology.imaging.segmentation.auto_threshold_schema import AutoThresholdParams

# --- Main Processor Logic ---
def run(
    ij_gateway,  # The initialized PyImageJ gateway instance
    image_bytes: bytes,
    params: AutoThresholdParams
) -> Dict[str, Any]:
    """
    Applies an automatic thresholding algorithm to an image using ImageJ ops.

    This processor follows the standardized architecture: it receives an initialized
    ImageJ gateway and a validated parameters object, performs a specific task,
    and returns a result dictionary.

    Args:
        ij_gateway: The active PyImageJ gateway from the ImageJService.
        image_bytes: The input image as bytes.
        params: A Pydantic model containing the validated thresholding method.

    Returns:
        A dictionary containing the processed binary image as bytes (in PNG format)
        and a summary of the operation.
    """
    # 1. Convert input bytes to a grayscale NumPy array.
    # Thresholding operates on intensity values, so a single channel is required.
    pil_image = Image.open(io.BytesIO(image_bytes))
    if pil_image.mode != 'L':
        pil_image = pil_image.convert('L') # Convert to 8-bit grayscale

    input_array = np.array(pil_image)

    # 2. Convert NumPy array to an ImageJ2 Dataset object
    ij_dataset = ij_gateway.py.to_dataset(input_array)

    # 3. Dynamically select and run the chosen thresholding operation
    # The method name from the frontend (e.g., "Otsu") is converted to lowercase
    # to match the method names on the ImageJ Ops `threshold` service (e.g., `otsu`).
    threshold_op_name = params.method.lower()
    
    # Get the thresholding operation namespace from the gateway
    threshold_ops = ij_gateway.op().threshold()

    # Check if the requested op exists on the threshold service
    if not hasattr(threshold_ops, threshold_op_name):
        raise AttributeError(f"The thresholding operation '{threshold_op_name}' is not available in this ImageJ instance.")

    # Dynamically call the correct op, e.g., `ij_gateway.op().threshold().otsu(ij_dataset)`
    binary_img = getattr(threshold_ops, threshold_op_name)(ij_dataset)

    # 4. Convert the resulting ImageJ Img<BitType> back to a NumPy array
    # The result is a boolean array (True for foreground, False for background).
    output_array_bool = ij_gateway.py.from_java(binary_img)

    # 5. Convert boolean array to an 8-bit integer array (0 and 255) for image saving
    output_array_uint8 = (output_array_bool * 255).astype(np.uint8)

    # 6. Convert output NumPy array back to image bytes (PNG format)
    output_image = Image.fromarray(output_array_uint8, mode='L')
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    output_bytes = output_buffer.getvalue()

    # 7. Construct the final result dictionary
    result = {
        "processed_image_bytes": output_bytes,
        "summary": {
            "filter_applied": "Auto Threshold",
            "parameters_used": params.model_dump(),
            "original_dimensions": f"{pil_image.width}x{pil_image.height}",
        }
    }
    return result