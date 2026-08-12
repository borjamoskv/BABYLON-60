// File System Access API Wrapper

export async function mountProject(): Promise<FileSystemDirectoryHandle | null> {
  try {
    const handle = await (window as any).showDirectoryPicker({ mode: 'readwrite' });
    return handle;
  } catch (error) {
    console.error("User cancelled or failed to mount directory", error);
    return null;
  }
}

export async function writeFile(dir: FileSystemDirectoryHandle, path: string, content: string) {
  const parts = path.split('/');
  let current = dir;
  for (const part of parts.slice(0, -1)) {
    current = await current.getDirectoryHandle(part, { create: true });
  }
  const file = await current.getFileHandle(parts.at(-1)!, { create: true });
  const writable = await file.createWritable();
  await writable.write(content);
  await writable.close();
}
