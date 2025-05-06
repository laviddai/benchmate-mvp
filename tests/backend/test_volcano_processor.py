import io
import base64
import matplotlib.pyplot as plt

def fig_to_base64(fig):
    """
    Convert a Matplotlib figure to a data URI with base64-encoded PNG.
    """
    # 1. Render the figure into an in-memory buffer
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)

    # 2. Read the raw bytes and base64-encode them
    img_bytes = buf.read()
    base64_str = base64.b64encode(img_bytes).decode("utf-8")

    # 3. Prepend the data-URI header so this string can be used directly
    #    as an <img src="…"> in HTML or returned as a JSON field.
    return f"data:image/png;base64,{base64_str}"
