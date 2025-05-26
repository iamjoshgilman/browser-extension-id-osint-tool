#!/usr/bin/env python3
"""
Create a simple favicon for the Browser Extension OSINT Tool
"""
import base64

# Simple 16x16 favicon in base64 (a magnifying glass icon)
FAVICON_BASE64 = """
AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAAAAAAAAAAAAAA
AAAAAAAA////Af///wH///8B////Af///wH///8B////Af///wH///8B////Af///wH///8B////
Af///wH///8B////AQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAACAAAABsAAAAbAAAAGwAAABsAAAAbAAAAGwAAABsAAAAbAAAAGwAAAAgAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAABAAAACQkJD/////+/////v////7////+////+/////sAAAAbAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAACb////+/////////////////////////////////////////
//sAAAAbAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAg////+///////////////////////////////////////////
//v///8bAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAACb////+/////////////////////////////////////////
//7////GwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAJv////7/////////////////////////////////////////
//v///8bAAAAAAAAAAAAAAAAAAAAAAAAAAAAACAAAACb////+/////////////////////////////////////////
//7////GwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAJv////7////+////////////////////////////
//v////7////GwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAsAAAAb////+////////////////////
//v////7////GwAAAAgAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwAAAJv////7////
////+////7////GwAAABsAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABsAAA
AbAAAAGwAAAAbAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
AAAAAAAA//8AAP//AADAAwAAgAEAAIABAACAAQAAgAEAAIABAACAAQAAgAEAAIABAADAAwAA+B8A
AP//AAD//wAA//8AAA==
"""

def create_favicon():
    """Create favicon.ico file from base64 data"""
    favicon_data = base64.b64decode(FAVICON_BASE64.strip())
    
    with open('frontend/favicon.ico', 'wb') as f:
        f.write(favicon_data)
    
    print("✓ Created favicon.ico")

if __name__ == "__main__":
    create_favicon()
