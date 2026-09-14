# 🧠 Integración de cortex-lsp: El LSP Paracortex Soberano

`cortex-lsp` es un servidor Language Server Protocol (LSP 3.17) nativo en Rust ubicado en `01_CORTEX_ENGINE/crates/cortex-lsp`.  
Permite transformar cualquier editor tonto (VS Code, Zed, Neovim, Helix) en un **Babylon IDE Soberano** con diagnósticos C5-REAL en tiempo real y atestación biométrica por hardware (TouchID).

---

## 1. Compilación del Binario Soberano

Para compilar el binario en modo optimizado de alta exergía:
```bash
cargo build --release -p cortex-lsp
```
El binario ejecutable quedará en:
```text
$BABYLON_HOME/target/release/cortex-lsp
```

---

## 2. Configuración en Editores

### A. Zed Editor (`~/.config/zed/settings.json`)
Añade la definición del servidor LSP en tu configuración de Zed:
```json
{
  "lsp": {
    "cortex-lsp": {
      "binary": {
        "path": "cortex-lsp"
      }
    }
  },
  "languages": {
    "Rust": {
      "language_servers": ["rust-analyzer", "cortex-lsp"]
    },
    "Python": {
      "language_servers": ["pyright", "cortex-lsp"]
    }
  }
}
```

---

### B. Neovim (`~/.config/nvim/init.lua`)
Usando el cliente LSP integrado de Neovim:
```lua
vim.api.nvim_create_autocmd("FileType", {
  pattern = { "rust", "python" },
  callback = function()
    vim.lsp.start({
      name = "cortex-lsp",
      cmd = { "/Users/borjafernandezangulo/BABYLON-60/target/release/cortex-lsp" },
      root_dir = vim.fs.dirname(vim.fs.find({ 'Cargo.toml', 'pyproject.toml', '.git' }, { upward = true })[1]),
    })
  end,
})
```

---

### C. Helix Editor (`~/.config/helix/languages.toml`)
```toml
[language-server.cortex-lsp]
command = "/Users/borjafernandezangulo/BABYLON-60/target/release/cortex-lsp"

[[language]]
name = "rust"
language-servers = [ "rust-analyzer", "cortex-lsp" ]

[[language]]
name = "python"
language-servers = [ "pyright", "cortex-lsp" ]
```

---

### D. VS Code
Puedes ejecutarlo como un Language Server estándar usando cualquier extensión genérica de LSP (por ejemplo, *Generic LSP Client* o crear una micro-extensión de 10 líneas en `client.ts`). Al conectarse por Stdin/Stdout, el servidor empezará inmediatamente a:
1. Subrayar violaciones de axiomas en rojo (`.unwrap()`, paths absolutos, floating-point en Ring-0).
2. Ofrecer la bombilla de acción rápida (`Cmd + .`) para:  
   `🛡️ [C5-REAL] Sellar Transacción Causal con TouchID (EU AI Act)`.
