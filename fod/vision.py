"""Anthropic vision wrapper for before/after FOD comparison."""
import base64
import os

from anthropic import Anthropic

MODEL = "claude-sonnet-5"

COMPARISON_PROMPT = """You are an aviation maintenance safety inspector checking for \
Foreign Object Debris (FOD) after a maintenance task.

You are given two photos of the same work area:
1. The "before" photo, taken before the task started.
2. The "after" photo, taken after the task was completed.

Compare the two images and identify any items visible in the after-photo that were \
NOT present in the before-photo and that could pose a FOD hazard — tools, \
fasteners, rags, hardware, packaging, or other foreign material left in the work area.

Call the report_fod_findings tool with your assessment. If no new items are found, \
set "clear" to true and "flagged_items" to an empty list.
"""

FINDINGS_TOOL = {
    "name": "report_fod_findings",
    "description": "Report the result of comparing before/after FOD inspection photos.",
    "input_schema": {
        "type": "object",
        "properties": {
            "clear": {"type": "boolean", "description": "True if no FOD hazards were found."},
            "summary": {"type": "string", "description": "One sentence overall assessment."},
            "flagged_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "item": {"type": "string", "description": "Short description of the item."},
                        "risk": {"type": "string", "enum": ["high", "medium", "low"]},
                        "location": {"type": "string", "description": "Where in the image it appears."},
                    },
                    "required": ["item", "risk", "location"],
                },
            },
        },
        "required": ["clear", "summary", "flagged_items"],
    },
}


def _image_block(image_bytes: bytes, media_type: str = "image/jpeg") -> dict:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(image_bytes).decode("utf-8"),
        },
    }


def compare_images(before_bytes: bytes, after_bytes: bytes) -> dict:
    """Send before/after images to Claude and return parsed FOD findings.

    Returns a dict with keys: clear (bool), summary (str), flagged_items (list).
    On any parsing/API failure, returns a dict with an "error" key instead.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {"error": "ANTHROPIC_API_KEY is not set. Add it to your .env file."}

    client = Anthropic(api_key=api_key)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            tools=[FINDINGS_TOOL],
            tool_choice={"type": "tool", "name": "report_fod_findings"},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "BEFORE photo:"},
                        _image_block(before_bytes),
                        {"type": "text", "text": "AFTER photo:"},
                        _image_block(after_bytes),
                        {"type": "text", "text": COMPARISON_PROMPT},
                    ],
                }
            ],
        )
    except Exception as exc:  # network/auth/API errors
        return {"error": f"Anthropic API request failed: {exc}"}

    for block in response.content:
        if block.type == "tool_use" and block.name == "report_fod_findings":
            return block.input

    return {"error": "Model did not return a tool call with findings."}
