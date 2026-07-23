# AUDIT REPORT: GITHUB COPILOT DARWIN-ARM64 (v1.0.24)
**Reality Level**: C5-REAL | **Analyst**: MOSKV-1 APEX

## 1. Executive Summary & Info.plist Signature
This report provides a structural decomposition of the macOS arm64 package of GitHub Copilot (`v1.0.24`). Key application metadata extracted from the bundle manifest:

```yaml
Application_Name: "GitHub Copilot"
Bundle_Identifier: "com.github.githubapp"
Version: "1.0.24"
Build_Number: "1.0.24"
Minimum_OS_Version: "macOS 10.13"
Executable_Binary: "Contents/MacOS/github"
Supported_Deep_Links:
  - "github-app"
  - "ghapp"
  - "gh"
Privacy_Permissions:
  Camera: "This app uses the camera when an extension canvas requests it."
  Microphone: "This app uses the microphone for voice dictation in the prompt composer."
  Speech_Recognition: "This app uses speech recognition for voice dictation in the prompt composer."
```

---

## 2. Package Topology & Core Architecture
Analysis of the `file_list.txt` from the mounted DMG reveals the application framework layout:

### A. Local Inference & Core Runtimes
The presence of the following dynamic libraries indicates built-in local inference and AI runtime support:
- `Contents/Frameworks/libonnxruntime.dylib`
- `Contents/Frameworks/libonnxruntime-genai.dylib`
- `Contents/Frameworks/Microsoft.AI.Foundry.Local.Core.dylib`

### B. Shell & Credential Integrations
- `Contents/MacOS/git-credential-copilot`: Intercepts credentials for secure Git operations.
- `Contents/Resources/terminal-integration/`: Provides shell integration scripts for `bash`, `zsh` (rc, env, login, profile), `fish`, and `Powershell`.

---

## 3. Copilot SDK Interface & Protocol Specification
The SDK is located under `Contents/Resources/copilot-sdk/` and runs as a separate Node.js process communicating with the Copilot CLI over JSON-RPC via `stdin` / `stdout`.

### A. Extension Discovery & Execution
- **Discovery Paths**: Project-level (`.github/extensions/<name>/extension.mjs`) and User-scoped configurations directory.
- **Rules**:
  - The entry point must be named `extension.mjs` using ES Modules (ESM). TypeScript (`.ts`) is not natively supported.
  - `@github/copilot-sdk` is resolved automatically by the host process runtime resolver.
  - Project extensions shadow user extensions on naming collisions.
  - Standard output (`stdout`) is strictly reserved for JSON-RPC messages; `console.log()` will corrupt the protocol. Extensions must output via `session.log()`.

### B. Minimal Boilerplate
```js
import { joinSession } from "@github/copilot-sdk/extension";

const session = await joinSession({
    tools: [], // Declared tools
    hooks: {}, // Lifecycle hooks
});
```

---

## 4. API Specification: Tools and Hooks

### Registering Tools
Tools are registered inside the `tools` array. They require a name, description, schema parameters, and a handler function:
```js
tools: [
    {
        name: "my_tool",
        description: "Executes a specific action",
        parameters: {
            type: "object",
            properties: {
                arg: { type: "string", description: "Argument description" }
            },
            required: ["arg"]
        },
        handler: async (args, invocation) => {
            // invocation contains: sessionId, toolCallId, toolName
            return `Result: ${args.arg}`;
        }
    }
]
```

### Lifecycle Hooks
Hooks intercept agent activity at critical execution states. All hooks receive the target `invocation` context and standard environments (`timestamp`, `workingDirectory`).

| Hook Name | Input Payload | Output Properties / Effects | :--- | :--- | :--- | `onUserPromptSubmitted` | `{ prompt: string }` | `modifiedPrompt` (rewrites user prompt), `additionalContext` (injects hidden system context) | `onPreToolUse` | `{ toolName, toolArgs }` | `permissionDecision` (`"allow" \| "deny" \| "ask"`), `permissionDecisionReason` (denial explanation), `modifiedArgs` (overrides tool arguments), `additionalContext` | `onPostToolUse` | `{ toolName, toolArgs, toolResult }` | `modifiedResult` (replaces tool output), `additionalContext` (appends context block) | `onPostToolUseFailure` | `{ toolName, toolArgs, error }` | `additionalContext` (hidden context guidance appended only on `"failure"` outcomes) | `onSessionStart` | `{ source: "startup" \| "resume" \| "new", initialPrompt }` | `additionalContext` (appends initial context configuration) | `onSessionEnd` | `{ reason: "complete" \| "error" \| "abort" \| "timeout" \| "user_exit", finalMessage, error }` | `sessionSummary` (session state), `cleanupActions` (cleanup strings) | `onErrorOccurred` | `{ error, errorContext, recoverable }` | `errorHandling` (`"retry" \| "skip" \| "abort"`), `retryCount`, `userNotification` |

---

## 5. Event Model & Event Streams
Developers can register real-time event listeners on the active session (`session.on(eventType, callback)`):

```js
session.on("tool.execution_complete", (event) => {
    // event.data has toolCallId, toolName, success, result, error
});
```

### Critical Protocol Events
- `assistant.message`: Final agent response content.
- `tool.execution_start` / `tool.execution_complete`: Correlates specific actions. Used to filter out automated file modifications from user changes.
- `permission.requested`: Fired when the agent requests shell/disk mutations.
- `session.shutdown`: Triggered when closing down, includes metrics like `totalPremiumRequests` and `codeChanges`.
