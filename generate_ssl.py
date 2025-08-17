#!/usr/bin/env python3
"""
SSL Certificate Generator for App Store Compliance
YouTube Transcript Webapp - Production Ready

Generates self-signed SSL certificates for HTTPS support
Required for App Store review process
"""

import os
import sys
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import socket

def get_local_ip():
    """Get local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def generate_ssl_certificate():
    """Generate SSL certificate and private key"""
    
    print("🔐 Generating SSL Certificate for App Store Compliance...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Get local IP for certificate
    local_ip = get_local_ip()
    
    # Certificate details
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "JP"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Tokyo"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Tokyo"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "YouTube Transcript App"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    
    # Certificate builder
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.utcnow()
    ).not_valid_after(
        datetime.utcnow() + timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.DNSName("127.0.0.1"),
            x509.DNSName(local_ip),
            x509.DNSName("*.ngrok-free.app"),
            x509.DNSName("*.ngrok.app"),
        ]),
        critical=False,
    ).add_extension(
        x509.KeyUsage(
            digital_signature=True,
            key_encipherment=True,
            content_commitment=False,
            data_encipherment=False,
            key_agreement=False,
            key_cert_sign=False,
            crl_sign=False,
            encipher_only=False,
            decipher_only=False,
        ),
        critical=True,
    ).add_extension(
        x509.ExtendedKeyUsage([
            x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
        ]),
        critical=True,
    ).sign(private_key, hashes.SHA256())
    
    # Create ssl directory if it doesn't exist
    os.makedirs('ssl', exist_ok=True)
    
    # Write private key
    with open('ssl/private.key', 'wb') as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    # Write certificate
    with open('ssl/certificate.crt', 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    
    # Create combined certificate file for some applications
    with open('ssl/fullchain.pem', 'wb') as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        ))
    
    print("✅ SSL Certificate generated successfully!")
    print(f"📁 Certificate: ssl/certificate.crt")
    print(f"🔑 Private Key: ssl/private.key")
    print(f"🔗 Full Chain: ssl/fullchain.pem")
    print(f"🌐 Local IP: {local_ip}")
    print(f"⏰ Valid for: 365 days")
    
    # Set proper permissions (Unix-like systems)
    if os.name != 'nt':
        os.chmod('ssl/private.key', 0o600)
        os.chmod('ssl/certificate.crt', 0o644)
        os.chmod('ssl/fullchain.pem', 0o600)
        print("🔒 Proper file permissions set")
    
    return True

def create_start_script():
    """Create production start script with SSL"""
    
    script_content = """#!/bin/bash
# Production Start Script with SSL
# YouTube Transcript Webapp - App Store Ready

export FLASK_ENV=production
export SSL_KEYFILE=ssl/private.key
export SSL_CERTFILE=ssl/certificate.crt

echo "🚀 Starting YouTube Transcript App (Production + SSL)"
echo "🔐 HTTPS enabled on port 8085"
echo "📱 App Store compliance mode active"

# Start with Gunicorn
gunicorn -c gunicorn.conf.py app_mobile:app
"""
    
    with open('start_production.sh', 'w') as f:
        f.write(script_content)
    
    # Make executable (Unix-like systems)
    if os.name != 'nt':
        os.chmod('start_production.sh', 0o755)
    
    print("📝 Production start script created: start_production.sh")

def create_windows_start_script():
    """Create Windows batch file for production"""
    
    script_content = """@echo off
REM Production Start Script with SSL (Windows)
REM YouTube Transcript Webapp - App Store Ready

set FLASK_ENV=production
set SSL_KEYFILE=ssl/private.key
set SSL_CERTFILE=ssl/certificate.crt

echo 🚀 Starting YouTube Transcript App (Production + SSL)
echo 🔐 HTTPS enabled on port 8085
echo 📱 App Store compliance mode active

REM Start with Gunicorn
python -m gunicorn -c gunicorn.conf.py app_mobile:app

pause
"""
    
    with open('start_production.bat', 'w') as f:
        f.write(script_content)
    
    print("📝 Windows production start script created: start_production.bat")

if __name__ == "__main__":
    try:
        print("🔧 Setting up Production SSL Environment...")
        print("=" * 50)
        
        # Generate SSL certificate
        success = generate_ssl_certificate()
        
        if success:
            # Create start scripts
            create_start_script()
            create_windows_start_script()
            
            print("\n" + "=" * 50)
            print("🎉 SSL Setup Complete!")
            print("\n📋 Next Steps:")
            print("1. Install production requirements: pip install -r requirements_production.txt")
            print("2. Start production server:")
            print("   • Linux/Mac: ./start_production.sh")
            print("   • Windows: start_production.bat")
            print("3. Access via HTTPS: https://localhost:8085")
            print("4. Verify SSL certificate in browser")
            print("\n⚠️  Note: Self-signed certificate will show security warning")
            print("   This is normal for development/testing environments")
            
    except Exception as e:
        print(f"❌ SSL setup failed: {e}")
        sys.exit(1)