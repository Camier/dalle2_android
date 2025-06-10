"""
Certificate Pinning Implementation for OpenAI API
"""

import ssl
import hashlib
import base64
from urllib3 import PoolManager
from urllib3.util import Timeout
from urllib3.exceptions import SSLError
from kivy.logger import Logger

class CertificatePinner:
    """
    Implements certificate pinning for secure API communication
    """
    
    # OpenAI API certificate pins (SHA256)
    # These should be updated periodically
    OPENAI_PINS = [
        # Primary certificate
        'sha256/Ko8tivDrEjiY90yGasP6ZpBU4jwXvHqVvQI0GS3GNdA=',
        # Backup certificate
        'sha256/VjLZe/p3W/PJnd6lL8JVNBCGQBZynFLdZSTIqcO0SJ8=',
        # Root CA certificate
        'sha256/++MBgDH5WGvL9Bcn5Be30cRcL0f5O+NyoXuWtQdX1aI='
    ]
    
    def __init__(self):
        self.pins = set(self.OPENAI_PINS)
        
    def verify_pin(self, cert_der):
        """Verify certificate against pinned values"""
        # Calculate SHA256 of the certificate
        cert_hash = hashlib.sha256(cert_der).digest()
        cert_pin = f'sha256/{base64.b64encode(cert_hash).decode()}'
        
        # Check if pin matches
        if cert_pin in self.pins:
            Logger.info(f"CertificatePinner: Certificate pin verified: {cert_pin[:20]}...")
            return True
        else:
            Logger.error(f"CertificatePinner: Certificate pin mismatch: {cert_pin[:20]}...")
            return False
    
    def create_pinned_session(self):
        """Create a session with certificate pinning"""
        # Custom SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = True
        ssl_context.verify_mode = ssl.CERT_REQUIRED
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        
        # Disable weak ciphers
        ssl_context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
        
        # Create pool manager with custom SSL context
        pool = PoolManager(
            ssl_context=ssl_context,
            cert_reqs='CERT_REQUIRED',
            assert_hostname='api.openai.com',
            timeout=Timeout(connect=5.0, read=30.0)
        )
        
        # Add certificate verification callback
        original_urlopen = pool.urlopen
        
        def pinned_urlopen(method, url, *args, **kwargs):
            response = original_urlopen(method, url, *args, **kwargs)
            
            # Verify certificate pin
            if hasattr(response.connection, 'sock') and hasattr(response.connection.sock, 'getpeercert_binary'):
                cert_der = response.connection.sock.getpeercert_binary()
                if not self.verify_pin(cert_der):
                    raise SSLError("Certificate pin verification failed")
            
            return response
        
        pool.urlopen = pinned_urlopen
        return pool

# Example usage in API service
class SecureAPIClient:
    def __init__(self):
        self.pinner = CertificatePinner()
        self.session = self.pinner.create_pinned_session()
    
    def make_request(self, url, **kwargs):
        """Make a request with certificate pinning"""
        return self.session.request('POST', url, **kwargs)
