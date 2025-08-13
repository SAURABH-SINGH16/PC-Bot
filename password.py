import hashlib

password = "1211"  # Replace this with the password you want
hashed = hashlib.sha256(password.encode()).hexdigest()

with open("password.txt", "w") as f:
    f.write(hashed)

print("✅ Password file created.")
