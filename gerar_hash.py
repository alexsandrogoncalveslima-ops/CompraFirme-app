import bcrypt

senha = "admin123"
senha_bytes = senha.encode('utf-8')
senha_hash = bcrypt.hashpw(senha_bytes, bcrypt.gensalt())

print(f"O hash da sua senha é: {senha_hash.decode('utf-8')}")