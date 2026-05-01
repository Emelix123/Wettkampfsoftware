import bcrypt

password = "Sommerfest2025!"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

print(hashed)
