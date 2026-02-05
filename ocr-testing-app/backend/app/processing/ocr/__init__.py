# OCR Engines
from .base import OCREngineBase, OCRResult

# Lazy registry - only import implementations when requested
_OCR_ENGINE_NAMES = ["easyocr", "surya", "paddleocr", "tesseract", "trocr", "got_ocr", "mineru"]

def get_ocr_engine(name: str) -> OCREngineBase:
    """Get an OCR engine by name (lazy import)."""
    if name == "easyocr":
        from .easyocr_engine import EasyOCREngine
        return EasyOCREngine()
    elif name == "surya":
        from .surya_ocr import SuryaOCREngine
        return SuryaOCREngine()
    elif name == "paddleocr":
        from .paddleocr_engine import PaddleOCREngine
        return PaddleOCREngine()
    elif name == "tesseract":
        from .tesseract_engine import TesseractEngine
        return TesseractEngine()
    elif name == "trocr":
        from .trocr_engine import TrOCREngine
        return TrOCREngine()
    elif name == "got_ocr":
        from .got_ocr_engine import GotOCREngine
        return GotOCREngine()
    elif name == "mineru":
        from .mineru_engine import MinerUEngine
        return MinerUEngine()
    else:
        raise ValueError(f"Unknown OCR engine: {name}. Available: {_OCR_ENGINE_NAMES}")

def list_ocr_engines() -> list[str]:
    """List available OCR engine names."""
    return _OCR_ENGINE_NAMES
