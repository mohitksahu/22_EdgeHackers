

import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileValidator:
	# NON-NEGOTIABLE: ONLY these extensions are allowed
	ALLOWED_EXTENSIONS = {
		'.pdf',           # PDF documents
		'.doc', '.docx',  # Word documents
		'.txt',           # Plain text
		'.png', '.jpg', '.jpeg',  # Images
		'.mp3', '.wav'    # Audio
	}
	
	MAX_SIZE_MB = 50

	def __init__(self):
		self.errors = []

	def validate(self, file_path):
		self.errors = []
		path = Path(file_path)
		
		# Check existence
		if not path.exists():
			self.errors.append(f"File does not exist: {file_path}")
			return False
			
		# Check readability
		if not os.access(path, os.R_OK):
			self.errors.append(f"File is not readable: {file_path}")
			return False
		
		# STRICT EXTENSION CHECK - Only allowed extensions
		ext = path.suffix.lower()
		if ext not in self.ALLOWED_EXTENSIONS:
			logger.warning(f"[VALIDATOR] Rejected file with unsupported extension: {file_path} (extension: {ext})")
			self.errors.append(
				f"File type '{ext}' is not supported. "
				f"Allowed types: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}"
			)
			return False
		
		# Check file size
		size_mb = path.stat().st_size / (1024 * 1024)
		if size_mb > self.MAX_SIZE_MB:
			self.errors.append(f"File size {size_mb:.2f}MB exceeds max {self.MAX_SIZE_MB}MB.")
			return False
			
		logger.info(f"[VALIDATOR] File validated successfully: {file_path}")
		return True



class BatchValidator:
	def __init__(self):
		self.errors = []

	def validate(self, file_list):
		self.errors = []
		validator = FileValidator()
		all_valid = True
		for file_path in file_list:
			if not validator.validate(file_path):
				all_valid = False
				self.errors.append({
					'file': str(file_path),
					'errors': validator.errors.copy()
				})
		return all_valid
