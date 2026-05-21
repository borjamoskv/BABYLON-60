import asyncio
import random
import string
import os
from aioslsk.client import SoulSeekClient
from aioslsk.settings import Settings, CredentialsSettings

# Generar un usuario único
random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
username = f"moskv_down_{random_suffix}"
password = "cortex_password_2026"

async def main():
    query = "Heroes del Silencio Heroe de Leyenda"
    save_dir = "$CORTEX_ROOT/Music/downloads"
    os.makedirs(save_dir, exist_ok=True)
    
    print("="*60)
    print("  CORTEX SOULSEEK DOWNLOAD AGENT")
    print(f"  Target: {query}")
    print(f"  Destination: {save_dir}")
    print("="*60)
    
    settings = Settings(
        credentials=CredentialsSettings(
            username=username,
            password=password
        ),
        shares=__import__('aioslsk.settings', fromlist=['SharesSettings']).SharesSettings(download=save_dir)
    )
    
    client = SoulSeekClient(settings)
    try:
        print("[*] Iniciando cliente Soulseek...")
        await client.start()
        print("[*] Conectando...")
        await client.login()
        print(f"[+] Autenticado exitosamente como: {username}")
        
        print(f"[*] Buscando: '{query}'")
        search_request = await client.searches.search(query)
        
        best_item = None
        best_user = None
        
        # Esperar resultados de búsqueda
        print("[*] Esperando resultados (15 segundos)...")
        for i in range(15):
            await asyncio.sleep(1)
            for res in search_request.results:
                if hasattr(res, 'shared_items') and res.shared_items:
                    for item in res.shared_items:
                        filename = item.filename
                        ext = filename.lower()
                        # Buscar específicamente archivos FLAC
                        if ext.endswith(".flac") and ("heroe de leyenda" in filename.lower() or "heroe_de_leyenda" in filename.lower()):
                            # Preferir archivos de tamaño razonable (ej. > 20MB para FLAC)
                            if not best_item or (item.filesize > best_item.filesize):
                                best_item = item
                                best_user = res.username
            if best_item:
                print(f"[+] FLAC viable encontrado rápido de {best_user}: {best_item.filename} ({best_item.filesize / (1024*1024):.2f} MB)")
                break

        if not best_item:
            # Si no se interrumpió, buscar entre todos los acumulados
            for res in search_request.results:
                if hasattr(res, 'shared_items') and res.shared_items:
                    for item in res.shared_items:
                        filename = item.filename
                        ext = filename.lower()
                        if ext.endswith(".flac"):
                            if not best_item or (item.filesize > best_item.filesize):
                                best_item = item
                                best_user = res.username

        if best_item:
            print(f"\n[+] Seleccionado para descarga:")
            print(f"    Usuario:  {best_user}")
            print(f"    Archivo:  {best_item.filename}")
            print(f"    Tamaño:   {best_item.filesize / (1024*1024):.2f} MB")
            
            print("[*] Iniciando transferencia de descarga...")
            await client.transfers.download(best_user, best_item.filename)
            print("[+] Descarga agregada a la cola de transferencias.")
            
            # Monitorear la descarga
            await asyncio.sleep(2)
            while True:
                unfinished = client.transfers.get_unfinished_transfers()
                if not unfinished:
                    print("\n[+] Descarga completada con éxito.")
                    break
                
                print(f"[*] Descargando de {best_user}... En cola/progreso: {len(unfinished)} archivos.")
                await asyncio.sleep(5)
        else:
            print("[-] No se encontró ningún archivo FLAC para descargar.")
            
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        print("\n[*] Cerrando sesión y deteniendo cliente...")
        await client.stop()
        print("[+] Cliente detenido.")
        print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
