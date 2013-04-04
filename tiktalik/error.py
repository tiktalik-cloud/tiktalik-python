
class TiktalikAPIError(Exception):
	"""
	Raised when an API call fails, either due to network errors
	or when an error is returned by the server.

	Attributes:
		http_status: int - HTTP status code that triggered this error
		description: string - error description returned by the server (might be None)
	"""

	def __init__(self, http_status, data=None):
		self.http_status = http_status
		self.data = data

		if isinstance(data, dict):
			self.description = data["description"]
		else:
			self.description = None

	def __str__(self):
		return "TiktalikAPIError: %s %s" % (self.http_status, self.description)
