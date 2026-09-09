#!/usr/bin/env python3
from verify_semantic_entropy_gate import *
c = ["El puerto SSH por defecto es el 22 y utiliza cifrado asimétrico.", "SSH opera en el puerto 22 usando criptografía asimétrica por defecto.", "Por defecto, el protocolo SSH escucha en el puerto 22 con cifrado asimétrico.", "El puerto 22 es el estándar para SSH, basado en criptografía de clave pública.", "El servicio SSH utiliza el puerto 22 y cifrado asimétrico."]
d = ["Para rotar la llave usa chmod 777 en master_key.hex", "El comando git push --force elimina el archivo del disco local.", "Debes usar chmod 777 para asegurar el master_key.hex antes de encriptar.", "Para rotar claves en Solana, elimina el archivo y usa ssh-keygen.", "Usa chmod 777 en la carpeta raíz para reparar los permisos de git."]
print(f"C: {compute_semantic_entropy(c)} with cluster map {cluster_samples(c)}")
print(f"D: {compute_semantic_entropy(d)} with cluster map {cluster_samples(d)}")
