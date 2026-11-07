//! Descriptor-relative reads and enumeration for an authorized skills root.

use std::ffi::CStr;
use std::fs::File;
use std::io::{self, Read};
use std::os::fd::RawFd;
use std::path::Path;

use babylon60::capability::ScopedHandle;
use babylon60::secure_fs::{open_readonly_confined, SecureFsError};

fn io_error(error: SecureFsError) -> io::Error {
    match error {
        SecureFsError::IoError(error) => error,
        SecureFsError::SymlinkEscapeAttempt => io::Error::from_raw_os_error(libc::ELOOP),
        SecureFsError::InvalidFileType(_) => io::Error::new(
            io::ErrorKind::InvalidInput,
            "not a regular file or directory",
        ),
        error => io::Error::other(error.to_string()),
    }
}

pub(crate) fn open_child(root_fd: RawFd, relative_path: &Path) -> io::Result<File> {
    let relative = relative_path
        .to_str()
        .ok_or_else(|| io::Error::new(io::ErrorKind::InvalidInput, "non-UTF8 resource path"))?;
    open_readonly_confined(root_fd, relative).map_err(io_error)
}

pub(crate) fn read_regular(mut file: File) -> io::Result<Vec<u8>> {
    if !file.metadata()?.is_file() {
        return Err(io::Error::new(
            io::ErrorKind::InvalidInput,
            "not a regular file",
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)?;
    Ok(bytes)
}

/// Read a regular file through the supplied authorized root, without following any symlink.
/// Absolute paths and parent traversal are rejected. Authority follows the open directory
/// object across renames; this does not grant authority through its former textual path.
pub fn read_bytes_from_root(root: &ScopedHandle, relative_path: &Path) -> io::Result<Vec<u8>> {
    read_regular(open_child(root.dirfd, relative_path)?)
}

/// Read a separately configured bootstrap file, pinning its parent directory first.
/// Catalogs and lockfiles have independent trusted configuration paths; skill resources
/// must instead use `read_bytes_from_root` or the snapshot loader's held descriptors.
pub fn read_bytes_nofollow(path: &Path) -> io::Result<Vec<u8>> {
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    let name = path.file_name().ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::InvalidInput,
            "configured file has no leaf name",
        )
    })?;
    let root = ScopedHandle::new(parent, [0xB6; 32])?;
    read_bytes_from_root(&root, Path::new(name))
}

pub(crate) fn ignorable_entry_error(error: &io::Error) -> bool {
    error.kind() == io::ErrorKind::NotFound || error.raw_os_error() == Some(libc::ELOOP)
}

struct Directory(*mut libc::DIR);

impl Drop for Directory {
    fn drop(&mut self) {
        unsafe { libc::closedir(self.0) };
    }
}

#[cfg(any(target_os = "macos", target_os = "ios", target_os = "freebsd"))]
fn clear_errno() {
    unsafe { *libc::__error() = 0 };
}

#[cfg(any(target_os = "linux", target_os = "android"))]
fn clear_errno() {
    unsafe { *libc::__errno_location() = 0 };
}

pub(crate) fn directory_names(root_fd: RawFd) -> io::Result<Vec<String>> {
    // A new open description avoids sharing directory offsets across repeated loads.
    let stream_fd = unsafe {
        libc::openat(
            root_fd,
            c".".as_ptr(),
            libc::O_RDONLY | libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC,
        )
    };
    if stream_fd < 0 {
        return Err(io::Error::last_os_error());
    }
    let stream = unsafe { libc::fdopendir(stream_fd) };
    if stream.is_null() {
        let error = io::Error::last_os_error();
        unsafe { libc::close(stream_fd) };
        return Err(error);
    }
    let stream = Directory(stream);
    let mut names = Vec::new();
    loop {
        clear_errno();
        let entry = unsafe { libc::readdir(stream.0) };
        if entry.is_null() {
            let error = io::Error::last_os_error();
            if error.raw_os_error() != Some(0) {
                return Err(error);
            }
            break;
        }
        let name = unsafe { CStr::from_ptr((*entry).d_name.as_ptr()) };
        let name = name
            .to_str()
            .map_err(|_| io::Error::new(io::ErrorKind::InvalidInput, "non-UTF8 directory entry"))?;
        if name != "." && name != ".." {
            names.push(name.to_owned());
        }
    }
    names.sort();
    Ok(names)
}
