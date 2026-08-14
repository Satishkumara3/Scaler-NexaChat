"""
Phase 7A: Attachment Security & Validation Tests
Runs against the live backend at http://localhost:8000
"""
import requests
import os
import io
import json
import sys

BASE = "http://localhost:8000"
PASS = []
FAIL = []

def register(name, phone):
    requests.post(f"{BASE}/api/auth/register/request-otp", json={"phone": phone})
    r = requests.post(f"{BASE}/api/auth/register/verify", json={
        "phone": phone, "otp_code": "123456", "display_name": name
    })
    if r.status_code not in (200, 201):
        print(f"  [FAIL] Register {name}: {r.status_code} {r.text[:100]}")
        return None, None
    return r.cookies["scaler_session"], r.json()["user"]["id"]

def check(label, cond, detail=""):
    if cond:
        PASS.append(label)
        print(f"  ✅ PASS: {label}")
    else:
        FAIL.append(label)
        print(f"  ❌ FAIL: {label} {detail}")

print("\n=== Phase 7A Security & Validation Tests ===\n")

# Setup users
print("Setting up users...")
token_a, uid_a = register("Alice7A", "+91-7000000001")
token_b, uid_b = register("Bob7A",   "+91-7000000002")
token_c, uid_c = register("Charlie7A","+91-7000000003")

if not token_a:
    print("Failed to register users. Is the backend running on port 8000?")
    sys.exit(1)

# Create direct conversation Alice <-> Bob
r = requests.post(f"{BASE}/api/conversations", json={"user_id": uid_b},
                  cookies={"scaler_session": token_a})
conv_id = r.json()["conversation"]["id"]
print(f"  Direct conversation: {conv_id}")

# ─── TEST 1: Normal text message ─────────────────────────────────────────────
print("\n[Test 1] Normal text messaging...")
r = requests.post(f"{BASE}/api/messages",
    json={"conversation_id": conv_id, "content": "Hello!", "message_type": "TEXT"},
    cookies={"scaler_session": token_a})
check("Text message accepted", r.status_code == 200)
check("Message has correct id", "id" in r.json().get("message", {}))

# ─── TEST 2: Valid image upload ───────────────────────────────────────────────
print("\n[Test 2] Valid image upload...")
# Minimal valid PNG (1x1 pixel)
png_bytes = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
    b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
)
r = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("test_image.png", io.BytesIO(png_bytes), "image/png")},
    cookies={"scaler_session": token_a})
check("PNG upload accepted (200)", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
if r.status_code == 200:
    msg = r.json()["message"]
    check("MESSAGE type is IMAGE", msg["message_type"] == "IMAGE")
    check("Attachment has url", "url" in msg.get("attachment", {}))
    att_url = msg["attachment"]["url"]
    stored_filename = att_url.split("/")[-1]
    print(f"    stored_filename={stored_filename}")

# ─── TEST 3: Valid PDF upload ─────────────────────────────────────────────────
print("\n[Test 3] Valid PDF upload...")
pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n%%EOF\n"
r = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("report.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    cookies={"scaler_session": token_a})
check("PDF upload accepted (200)", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
if r.status_code == 200:
    msg2 = r.json()["message"]
    check("MESSAGE type is FILE", msg2["message_type"] == "FILE")

# ─── TEST 4: File size > 10MB → rejected ─────────────────────────────────────
print("\n[Test 4] File > 10MB should be rejected...")
large = io.BytesIO(b"A" * (11 * 1024 * 1024))  # 11MB
r = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("big.txt", large, "text/plain")},
    cookies={"scaler_session": token_a})
check("Large file rejected (413)", r.status_code == 413, f"got {r.status_code}")

# ─── TEST 5: Unsupported MIME type → rejected ─────────────────────────────────
print("\n[Test 5] Unsupported MIME type...")
r = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("evil.exe", io.BytesIO(b"MZrandom"), "application/octet-stream")},
    cookies={"scaler_session": token_a})
check("EXE upload rejected (415)", r.status_code == 415, f"got {r.status_code}")

# ─── TEST 6: Unauthenticated upload → rejected ────────────────────────────────
print("\n[Test 6] Unauthenticated upload...")
r = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("test.png", io.BytesIO(png_bytes), "image/png")})
check("Unauth upload rejected (401/403)", r.status_code in (401, 403), f"got {r.status_code}")

# ─── TEST 7: Non-member cannot access attachment ──────────────────────────────
print("\n[Test 7] Non-member cannot download attachment...")
r_img = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("private.png", io.BytesIO(png_bytes), "image/png")},
    cookies={"scaler_session": token_a})
if r_img.status_code == 200:
    priv_filename = r_img.json()["message"]["attachment"]["stored_filename"]
    r = requests.get(f"{BASE}/api/messages/attachments/{priv_filename}",
        cookies={"scaler_session": token_c})  # Charlie is NOT in this conv
    check("Non-member download rejected (403)", r.status_code == 403, f"got {r.status_code}")

# ─── TEST 8: Authorized member CAN download ──────────────────────────────────
print("\n[Test 8] Authorized member can download...")
if r_img.status_code == 200:
    r = requests.get(f"{BASE}/api/messages/attachments/{priv_filename}",
        cookies={"scaler_session": token_b})
    check("Member can download (200)", r.status_code == 200, f"got {r.status_code}")
    check("Binary content returned", len(r.content) > 0)

# ─── TEST 9: Path traversal filename  ────────────────────────────────────────
print("\n[Test 9] Path traversal in attachment URL...")
r = requests.get(f"{BASE}/api/messages/attachments/../../../etc/passwd",
    cookies={"scaler_session": token_a})
check("Path traversal rejected (404/403/422)", r.status_code in (404, 403, 422), f"got {r.status_code}")

# ─── TEST 10: Non-member upload → rejected ────────────────────────────────────
print("\n[Test 10] Non-member cannot upload to conversation...")
r = requests.post(f"{BASE}/api/messages/{conv_id}/attachments",
    files={"file": ("x.png", io.BytesIO(png_bytes), "image/png")},
    cookies={"scaler_session": token_c})
check("Non-member upload rejected (403)", r.status_code == 403, f"got {r.status_code}")

# ─── TEST 11: Message persistence check ──────────────────────────────────────
print("\n[Test 11] Persistence — messages with attachments still readable...")
r = requests.get(f"{BASE}/api/messages/{conv_id}",
    cookies={"scaler_session": token_a})
check("Conversation messages fetch OK (200)", r.status_code == 200)
msgs = r.json().get("messages", [])
att_msgs = [m for m in msgs if m.get("attachment")]
check("Attachment messages present in history", len(att_msgs) >= 2, f"found {len(att_msgs)}")

# ─── TEST 12: Group attachments ───────────────────────────────────────────────
print("\n[Test 12] Group attachment sharing...")
rg = requests.post(f"{BASE}/api/groups",
    json={"name": "TestGroup7A", "member_ids": [uid_b, uid_c]},
    cookies={"scaler_session": token_a})
if rg.status_code == 200:
    grp_id = rg.json()["group"]["id"]
    r = requests.post(f"{BASE}/api/messages/{grp_id}/attachments",
        files={"file": ("group_img.png", io.BytesIO(png_bytes), "image/png")},
        cookies={"scaler_session": token_a})
    check("Group image upload accepted (200)", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
    if r.status_code == 200:
        grp_filename = r.json()["message"]["attachment"]["stored_filename"]
        # Bob (member) can download
        r2 = requests.get(f"{BASE}/api/messages/attachments/{grp_filename}",
            cookies={"scaler_session": token_b})
        check("Group member (Bob) can download (200)", r2.status_code == 200, f"got {r2.status_code}")
        # Charlie (member) can download
        r3 = requests.get(f"{BASE}/api/messages/attachments/{grp_filename}",
            cookies={"scaler_session": token_c})
        check("Group member (Charlie) can download (200)", r3.status_code == 200, f"got {r3.status_code}")
else:
    print(f"  [SKIP] Group creation failed: {rg.status_code} {rg.text[:100]}")

# ─── SUMMARY ─────────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"RESULTS: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print(f"\nFailed tests:")
    for f in FAIL:
        print(f"  ❌ {f}")
else:
    print("\n🎉 All security/validation tests passed!")
print('='*50)
