"""
Scan simulator service.
Applies realistic scan effects (rotation, noise, blur, brightness, contrast)
to create augmented copies of handwritten form images.
"""
import io
import random
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


PRESETS = {
    "light": {
        "rotation_range": 1.5,
        "noise_amount": 3,
        "blur_radius": 0.3,
        "brightness_range": (0.95, 1.05),
        "contrast_range": (0.95, 1.05),
        "paper_tone": (245, 240, 230),
    },
    "medium": {
        "rotation_range": 3.0,
        "noise_amount": 8,
        "blur_radius": 0.7,
        "brightness_range": (0.85, 1.15),
        "contrast_range": (0.85, 1.15),
        "paper_tone": (235, 228, 215),
    },
    "heavy": {
        "rotation_range": 5.0,
        "noise_amount": 15,
        "blur_radius": 1.2,
        "brightness_range": (0.75, 1.25),
        "contrast_range": (0.75, 1.30),
        "paper_tone": (225, 215, 200),
    },
}


class ScanSimulatorService:
    """Service for applying scan simulation effects to images."""

    def apply_scan_effects(
        self, image: Image.Image, preset: str = "medium"
    ) -> Image.Image:
        """
        Apply realistic scan effects to an image.

        Args:
            image: PIL Image to process
            preset: One of "light", "medium", "heavy"

        Returns:
            Augmented PIL Image
        """
        params = PRESETS.get(preset, PRESETS["medium"])
        img = image.copy().convert("RGB")

        # 1. Apply paper tone (slight warm tint like a scanned page)
        tone = params["paper_tone"]
        tone_layer = Image.new("RGB", img.size, tone)
        img = Image.blend(img, tone_layer, alpha=0.08)

        # 2. Random rotation
        angle = random.uniform(
            -params["rotation_range"], params["rotation_range"]
        )
        img = img.rotate(angle, expand=False, fillcolor=(255, 255, 255))

        # 3. Brightness adjustment
        brightness_factor = random.uniform(*params["brightness_range"])
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(brightness_factor)

        # 4. Contrast adjustment
        contrast_factor = random.uniform(*params["contrast_range"])
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(contrast_factor)

        # 5. Gaussian blur
        if params["blur_radius"] > 0:
            blur_r = random.uniform(0, params["blur_radius"])
            img = img.filter(ImageFilter.GaussianBlur(radius=blur_r))

        # 6. Add Gaussian noise
        if params["noise_amount"] > 0:
            arr = np.array(img, dtype=np.float32)
            noise = np.random.normal(0, params["noise_amount"], arr.shape)
            arr = np.clip(arr + noise, 0, 255).astype(np.uint8)
            img = Image.fromarray(arr)

        return img

    def generate_skewed_copy(
        self, image_bytes: bytes, preset: str = "medium"
    ) -> bytes:
        """
        Generate a single skewed copy from image bytes.

        Args:
            image_bytes: Original image as bytes
            preset: Skew preset ("light", "medium", "heavy")

        Returns:
            Augmented image as PNG bytes
        """
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        augmented = self.apply_scan_effects(image, preset)

        output = io.BytesIO()
        augmented.save(output, format="PNG")
        output.seek(0)
        return output.getvalue()
