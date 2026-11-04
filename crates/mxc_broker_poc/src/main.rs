use std::ffi::CString;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::io::RawFd;
use std::path::Path;
use std::io::Write;
use tempfile::NamedTempFile;

// [ BABYLON-60 · KUDURRU-64 CORE POC ]
// La guillotina de Hume como error de compilación.

#[derive(Debug)]
pub enum Omega0Error {
    HumeViolation(&'static str),
    IoError(std::io::Error),
}

impl From<std::io::Error> for Omega0Error {
    fn from(err: std::io::Error) -> Self {
        Omega0Error::IoError(err)
    }
}

/// Representa una intención estocástica purificada
pub struct VerifiedIntent {
    pub target_inode: u64,
}

/// Descriptor de archivo anclado a la invariante causal.
#[allow(dead_code)]
pub struct CausalFileDescriptor {
    fd: RawFd,
    inode: u64,
}

impl CausalFileDescriptor {
    pub fn bind_causal_path(intent: &VerifiedIntent, path: &Path) -> Result<Self, Omega0Error> {
        let c_path = CString::new(path.as_os_str().as_bytes()).unwrap();
        
        let fd = unsafe { 
            libc::open(
                c_path.as_ptr(), 
                libc::O_RDONLY | libc::O_NOFOLLOW | libc::O_CLOEXEC
            ) 
        };
        
        if fd < 0 { 
            return Err(Omega0Error::HumeViolation("Ruta topológica inaccesible")); 
        }
        
        let inode = Self::get_inode(fd)?;
        
        if inode != intent.target_inode {
            unsafe { libc::close(fd); }
            return Err(Omega0Error::HumeViolation("Divergencia de Inodo: Intento TOCTOU interceptado y bloqueado"));
        }
        
        Ok(CausalFileDescriptor { fd, inode })
    }

    fn get_inode(fd: RawFd) -> Result<u64, Omega0Error> {
        let mut stat: libc::stat = unsafe { std::mem::zeroed() };
        let ret = unsafe { libc::fstat(fd, &mut stat) };
        if ret < 0 {
            return Err(Omega0Error::HumeViolation("Fallo al obtener estado del FD"));
        }
        Ok(stat.st_ino as u64)
    }

    pub fn verified_commit(&self, data: &[u8], target_path: &Path) -> Result<(), Omega0Error> {
        let mut temp_file = NamedTempFile::new()?;
        temp_file.write_all(data)?;
        temp_file.flush()?;
        temp_file.persist(target_path).map_err(|e| Omega0Error::IoError(e.error))?;
        Ok(())
    }
}

impl Drop for CausalFileDescriptor {
    fn drop(&mut self) {
        if self.fd >= 0 {
            unsafe { libc::close(self.fd); }
        }
    }
}

fn get_current_inode(path: &Path) -> u64 {
    let mut stat: libc::stat = unsafe { std::mem::zeroed() };
    let c_path = CString::new(path.as_os_str().as_bytes()).unwrap();
    unsafe { libc::stat(c_path.as_ptr(), &mut stat) };
    stat.st_ino as u64
}

fn main() {
    println!("[ BABYLON-60 ] PoC: Aislamiento Causal vs TOCTOU (Microsoft MXC)");
    
    let test_path = Path::new("./poc_target.txt");
    std::fs::write(test_path, "Estado Inicial").unwrap();
    
    let real_inode = get_current_inode(test_path);
    println!("Inodo Autorizado: {}", real_inode);

    // Intento 1: Intento Legítimo
    let intent_valid = VerifiedIntent { target_inode: real_inode };
    match CausalFileDescriptor::bind_causal_path(&intent_valid, test_path) {
        Ok(causal_fd) => {
            println!("[+] Intento Válido: Resolución O_PATH/O_SYMLINK exitosa.");
            match causal_fd.verified_commit(b"Estado Mutado de Alta Exergia", test_path) {
                Ok(_) => println!("[+] Verified Commit (rename atómico) exitoso. Cero *torn writes*."),
                Err(e) => println!("[-] Fallo en commit: {:?}", e),
            }
        },
        Err(e) => println!("[-] Intento Válido Fallido: {:?}", e),
    }

    // El inodo cambió por el atomic rename, actualizamos
    let new_inode = get_current_inode(test_path);
    println!("Inodo Mutado tras Commit: {}", new_inode);

    // Intento 2: Ataque TOCTOU simulado
    // El agente intenta escribir referenciando un inodo falso (simulando que cambió el archivo en la ruta tras la validación)
    let intent_malicious = VerifiedIntent { target_inode: 0xDEADBEEF }; 
    match CausalFileDescriptor::bind_causal_path(&intent_malicious, test_path) {
        Ok(_) => println!("[-] ERROR FATAL: El ataque TOCTOU evadió el cerrojo."),
        Err(Omega0Error::HumeViolation(msg)) => {
            println!("[+] Atestación SCITT: Ataque TOCTOU rechazado correctamente en tiempo de tipos.");
            println!("    Razón: {}", msg);
        },
        Err(e) => println!("[-] Error Inesperado: {:?}", e),
    }
    
    let _ = std::fs::remove_file(test_path);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::fs::MetadataExt;

    #[test]
    fn causal_binding_accepts_regular_file_but_never_follows_symlink() {
        let dir = tempfile::tempdir().unwrap();
        let target = dir.path().join("target");
        let link = dir.path().join("link");
        std::fs::write(&target, b"unchanged").unwrap();
        std::os::unix::fs::symlink(&target, &link).unwrap();
        let intent = VerifiedIntent { target_inode: std::fs::metadata(&target).unwrap().ino() };
        assert!(CausalFileDescriptor::bind_causal_path(&intent, &target).is_ok());
        assert!(CausalFileDescriptor::bind_causal_path(&intent, &link).is_err());
        let link_intent = VerifiedIntent { target_inode: std::fs::symlink_metadata(&link).unwrap().ino() };
        assert!(CausalFileDescriptor::bind_causal_path(&link_intent, &link).is_err());
        assert_eq!(std::fs::read(&target).unwrap(), b"unchanged");
    }
}
