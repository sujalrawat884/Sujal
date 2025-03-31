import os
import cv2
import pytesseract
import numpy as np
from PIL import Image
from io import BytesIO
import base64
import logging

# Configure pytesseract path if needed (Windows example)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ImageProcessor:
    @staticmethod
    def extract_text_from_image(image_data):
        """
        Extract text from image using OCR
        
        Args:
            image_data: Base64 encoded image or file path
            
        Returns:
            Extracted text as string
        """
        try:
            # Check if input is base64 string or file path
            if isinstance(image_data, str):
                if os.path.isfile(image_data):
                    # Load image from file
                    img = cv2.imread(image_data)
                elif image_data.startswith('data:image'):
                    # Process base64 image
                    encoded_data = image_data.split(',')[1]
                    nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                else:
                    raise ValueError("Invalid image data format")
            else:
                # Assume bytes-like object
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Preprocess the image for better OCR results
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, threshold = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Extract text using pytesseract
            text = pytesseract.image_to_string(threshold, lang='eng')
            
            return text.strip()
        except Exception as e:
            logging.error(f"Error processing image: {str(e)}")
            return "Error processing image. Please try again with a clearer image."
    
    @staticmethod
    def identify_content_type(image_path):
        """
        Identify if image contains text, diagrams, or other content
        Returns the likely content type
        """
        try:
            # Extract text
            text = ImageProcessor.extract_text_from_image(image_path)
            
            # Count words to determine if text-heavy
            word_count = len(text.split())
            
            if word_count > 50:
                return "text_document", text
            elif word_count > 10:
                return "mixed_content", text
            else:
                return "diagram_or_image", text
        except Exception as e:
            logging.error(f"Error identifying content type: {str(e)}")
            return "unknown", ""