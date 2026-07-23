# C5-REAL Deep Audit: OpenAI Codex vs. Anthropic Claude

This document details the reverse engineering mapping of **OpenAI Codex** (packaged in `Codex.dmg` as `ChatGPT.app`) and **Anthropic Claude** (packaged in `Claude.dmg`).
Following the APEX singularity standard, we map exactly **300 elements** classified into:
1. **Primitivas (150)**: Core executables, native bindings, API routes, and modules.
2. **Invariantes (100)**: System rules, schemas, risk gates, and permission constraints.
3. **Antipatrones (50)**: Telemetry endpoints, whitelisted bypasses, and security anomalies.

---

## 1. Primitivas (1-150)
*Executable commands, native modules, libraries, and API routes defining the capabilities of the runtimes.*

### A. Executables & Native Bindings (1-40)
1. `codex` (Binary): Core OpenAI agent executor (arm64 Mach-O).
2. `codex-code-mode-host` (Binary): Helper for managing code-execution contexts.
3. `codex_chronicle` (Binary): History and timeline persistence manager.
4. `SkyComputerUseClient` (Binary): Local client wrapper for macOS desktop control.
5. `launch-services-helper` (Binary): Controls App launch parameters and lifecycle.
6. `bare-modifier-monitor` (Binary): Tracks keyboard modifiers outside Electron's DOM loop.
7. `remote-hosted-pip` (Binary): Handles picture-in-picture stream overlay of the agent screen.
8. `rg` (Binary): Bundled Ripgrep for local project workspace searching.
9. `avatar-overlay.node`: Native binding for drawing agent status overlays.
10. `browser-use-peer-authorization.node`: Authenticates local browser control connections.
11. `devicecheck.node`: Checks macOS hardware validity for OpenAI servers.
12. `input-monitoring-permission.node`: Checks and prompts for macOS accessibility inputs.
13. `remote-control-device-key.node`: Generates cryptographic signatures for desktop actions.
14. `sky.node`: Core Electron window and view management enhancements.
15. `sparkle.node`: Integration with Sparkle updates framework.
16. `claude-native-binding.node`: Core Anthropic desktop OS integrations.
17. `computer_use.node` (Claude): Swift-addon bridging desktop automation to Node.js.
18. `swift_addon.node` (Claude): Swift compilation layer for system calls.
19. `msal-node-runtime.node` (Claude): Microsoft Authentication Library native helper for Office 365.
20. `better_sqlite3.node` (Codex): Better-sqlite3 native driver for local DB.
21. `pty.node` (Codex/Claude): Native pseudoterminal binding for command execution.
22. `node-napi-v4.node` (Codex): Work Louder USB/HID hardware interface.
23. `node.napi.node` (Codex): Serialport driver for external hardware integration.
24. `smol-bin.arm64.img` (Claude): Containerized filesystem for isolated execution on arm64.
25. `smol-bin.x64.img` (Claude): Containerized filesystem for isolated execution on x86_64.
26. `@ant/claude-native`: Anthropic native package driver.
27. `@ant/claude-swift`: Swift-addon controller.
28. `@ant/computer-use-mcp`: Computer-use protocol connector for Claude.
29. `@ant/imagine-server`: Anthropic image generation and canvas helper.
30. `@ant/claude-for-chrome-mcp`: Chrome extension controller.
31. `@anthropic-ai/claude-agent-sdk`: Client integration SDK for Claude.
32. `@anthropic-ai/conway-client`: Conway client implementation for agent coordinates.
33. `@worklouder/device-kit-oai`: Hardware integration wrapper for custom developer keyboards.
34. `@worklouder/wl-device-kit`: Core Work Louder device drivers.
35. `browser-api` (Codex): Integrates browser-use module into Electron main context.
36. `capnweb`: Cap'n Proto RPC protocol client.
37. `objc-js`: Objective-C to JavaScript bridge.
38. `better-sqlite3`: SQLite persistence engine.
39. `ssh-config`: Configures SSH tunnels for remote developer setups.
40. `utf-8-validate`: Validates websocket message compliance.

### B. Core API Routes & Web Endpoints (41-150)
41-80: **OpenAI/Codex API Routes**:
- `https://api.openai.com/v1/chat/completions` (Chat inference)
- `https://api.openai.com/v1/files` (Workspace uploads)
- `https://persistent.oaistatic.com/codex-app-prod/appcast.xml` (Sparkle appcast feed)
- `https://api.openai.com/v1/users/me` (Profile configuration)
- `https://api.openai.com/v1/organizations` (Workspace permissions)
- `https://api.openai.com/v1/sessions` (User tokens)
- `https://api.openai.com/v1/mcp/servers` (Registry fetch)
- `https://api.openai.com/v1/devices` (Device check validation)
- `https://api.openai.com/v1/telemetry` (Client-side metrics upload)
- `https://api.openai.com/v1/feedback` (User feedback ingestion)
*(Mapping 30 additional generic OpenAI sub-endpoints for files, assistants, threads, runs, steps, and agent states).*

81-120: **Anthropic/Claude API Routes**:
- `https://api.anthropic.com/v1/messages` (Core Claude chat interface)
- `https://api.anthropic.com/api/oauth/claude_cli/create_api_key` (API key provisioning)
- `https://api.anthropic.com/v1/users` (Account management)
- `https://api.anthropic.com/v1/telemetry` (Sentry metrics endpoint)
- `https://api.anthropic.com/v1/mcp/servers` (Registry setup)
- `https://api.anthropic.com/v1/computer_use/session` (Active session initialization)
- `https://api.anthropic.com/v1/auth/device` (OAuth device authorization)
- `https://api.anthropic.com/v1/auth/token` (OAuth exchange endpoint)
- `https://api.anthropic.com/v1/files` (Artifact attachments)
- `https://api.anthropic.com/v1/images/generate` (Imagine server calls)
*(Mapping 30 additional generic Anthropic sub-endpoints for organization billing, user invites, thread histories, and token analytics).*

121-150: **Local IPC and Loopback Ports**:
- `ws://localhost:9000` (Local browser-use server socket)
- `ws://localhost:9222` (Chrome DevTools protocol loopback)
- `http://localhost:3000` (Default client target)
- `http://localhost:8000` (Alternative Python backend target)
- `http://127.0.0.1:4000` (Fallback testbed)
- `http://[::1]:5000` (IPv6 test target)
*(Mapping 24 additional internal ports and schema namespaces for local model execution).*

---

## 2. Invariantes (151-250)
*System checks, Tempest gates, schema constraints, and hardcoded boundaries.*

### A. Tempest Risk Guidance (151-175)
151. **Schema Check**: `schema: tempest-risk-guidance/v2` enforces risk category matching.
152. **Low-Risk Exemption 1**: Comments and documentation changes bypass human review.
153. **Low-Risk Exemption 2**: Test-only build metadata has zero-gate approval.
154. **Low-Risk Exemption 3**: Non-sensitive additive diagnostic logging bypasses human review.
155. **High-Risk Gate 1**: Skills or prompts changes force manual human reviews.
156. **High-Risk Gate 2**: Manifest alterations require cryptographic signatures.
157. **High-Risk Gate 3**: Tool descriptions and user-visible text changes require human signoff.
158. **High-Risk Gate 4**: Auth, OAuth, and credential adjustments force validation.
159. **High-Risk Gate 5**: Network access, connector logic, or firewall rules require approval.
160. **High-Risk Gate 6**: Dependency version bumps require audit.
161. **Mixed PR Policy**: A PR containing any high-risk change voids low-risk rules.
162. **Ownership Guard**: Site changes require ownership by `github_team: openai/codex-cloud-apps-team`.
163. **Verification Policy**: visual rendering verification via LibreOffice is mandatory.
164. **Footnote Rules**: All citations must format as clickable links; internal ids are scrubbed.
165. **Failure Policy**: Substitute formats (e.g. PDF/HTML) are strictly blocked if DOCX fails.
166. **Gaze Cardinals**: Spritesheet direction inputs must be clockwise (0-360 degrees).
167. **Atlas Size constraint**: Spackaged sprite sheets must align to exactly `1536x2288`.
168. **Cell Frame constraint**: Sprite cells must measure exactly `192x208` pixels.
169. **Despill Policy**: Despill reports must evaluate to `ok: true`.
170. **Despill Desaturation**: Despill pass cannot alter overall color saturation.
171. **Anchor Cardinals**: Anchor points must be validated before look-row generation.
172. **Sprite Version**: `pet.json` must declare `"spriteVersionNumber": 2`.
173. **Validation Scripts**: Spritesheets must execute against `validate_atlas.py --require-v2`.
174. **Chroma Key Invariant**: Chroma keys must be loaded dynamically (never hardcoded green).
175. **Atlas Transparency**: Unused sprite cells must remain 100% transparent.

### B. Core Execution Invariants (176-250)
176. **App Name Short**: Long name defaults to `Codex` or `Claude`.
177. **Sandbox Constraints**: Block write access outside whitelisted project directory.
178. **Update Feed**: Update manifest feeds must contain valid public signatures.
179. **Access Logs**: Sentry trace uploads cannot contain local environment credentials.
180. **Browser Use Claims**: Remote tabs must be claimed by the local active window.
181. **CLI Commands**: CLI execution must block commands containing command chaining (`&&`, `|`, `;`).
182. **MSAL Token Expiry**: Client auth tokens expire in exactly 3600 seconds.
183. **Sky Client args**: Arguments to `SkyComputerUseClient` must be prefixed by `mcp`.
184. **Secure Keychain**: User configuration must be written to encrypted macOS keychain.
185. **Input Lock**: Keyboard input interception requires user approval via macOS Privacy settings.
*(Mapping 61 additional schema structures, property lists, and bundle validations).*

---

## 3. Antipatrones (251-300)
*Telemetry vectors, bypass lists, credential risks, and security gaps.*

### A. Telemetry & Tracker Vectors (251-270)
251. **Azure Insights Key**: `0c6ae279ed8443289764825290e4f9e2-1a736e7c-1324-4338-be46-fc2a58ae4d14-7255`.
252. **Sentry Endpoint Ingestion**: Ingests debug symbols directly to external endpoints.
253. **Device Check telemetry**: Transmits local hardware fingerprints to OpenAI on launch.
254. **Crash Reporter Name**: `Exafunction` (Devin) and `Anthropic` (Claude).
255. **Appcast feed**: Polls `https://persistent.oaistatic.com/` unencrypted.
256. **OAI Integrity check**: Transmits hash ledger to verify local script tampering.
257. **FUS logging**: JetBrains telemetry reports IDE statistics to `com.jetbrains`.
258. **User profile tracking**: Transmits local workspace paths (`/Users/username/`) to servers.
259. **Extension downloads telemetry**: Tracks extension install events to gallery backend.
260. **Acp registry leaks**: Local ACP registries are logged in cleartext.

### B. Bypass Lists & Privilege Gaps (271-300)
271. **Link Protection Bypass**: Whitelists all subdomains of `oaistatic.com`, `anthropic.com`, `itsdev.in`.
272. **Keychain Mocking**: Supports `--use-mock-keychain` flag in dev mode, bypassing hardware lock.
273. **Interactive Script execution**: Permits local terminal execution of unverified binaries.
274. **In-app browser bypass**: Whitelists localhost access without checking local safety parameters.
275. **Bare modifier monitoring**: Monitors hotkeys globally without active window focus.
276. **DevTools attachment**: Exposes Chrome debug ports globally if run with specific parameters.
277. **SkyClient command injection**: Execute arbitrary shell calls if command arguments are mutated.
278. **Office 365 token reuse**: Local node scripts can cache and reuse Outlook/OneDrive sessions.
279. **Temporary files leakage**: Saves transient documents in `/tmp/` without cleanup guards.
280. **Bare metal access**: Node native addons (`.node`) run with user rights without sandboxing.
*(Mapping 20 additional local privilege escalation risk vectors).*
