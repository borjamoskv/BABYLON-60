// C5-REAL EXERGY CERTIFIED
"use strict";(function(){try{var e=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{};e.SENTRY_RELEASE={id:"e0f338aea51a130071b62788fee794575c1b9d0e"}}catch{}})();try{(function(){var e=typeof window<"u"?window:typeof global<"u"?global:typeof globalThis<"u"?globalThis:typeof self<"u"?self:{},t=new e.Error().stack;t&&(e._sentryDebugIds=e._sentryDebugIds||{},e._sentryDebugIds[t]="30ae946f-55c9-4c3d-a8d0-bd67c2c6698c",e._sentryDebugIdIdentifier="sentry-dbid-30ae946f-55c9-4c3d-a8d0-bd67c2c6698c")})()}catch{}const j=require("node:child_process"),k=require("electron"),a=require("./index.chunk-_dwNZmCe.js");require("node:fs");const m=require("node:path"),A=require("node:fs/promises"),T=require("node:os");require("node:url");require("node:path/posix");require("node:path/win32");var I=(e=>(e.Connected="connected",e.Working="working",e.Editing="editing",e.Disconnected="disconnected",e))(I||{}),p=(e=>(e.Excel="excel",e.PowerPoint="powerpoint",e.Word="word",e))(p||{});const Q="claude-haiku-4-5-20251001",Z=1024,U=1e4;function ee(){const e=a.getFeatureValue("1748356779",{});return!e.system_prompt||!e.user_prompt_template?null:{systemPrompt:e.system_prompt,toolDescription:e.tool_description||"",summaryDescription:e.summary_description||"",entitiesDescription:e.entities_description||"",nextActionDescription:e.next_action_description||"",userPromptTemplate:e.user_prompt_template}}function te(e){return{name:"summarize_conversation",description:e.toolDescription,input_schema:{type:"object",properties:{summary:{type:"string",description:e.summaryDescription},entities:{type:"array",items:{type:"string"},description:e.entitiesDescription},next_action:{type:"string",description:e.nextActionDescription}},required:["summary"]}}}let N=0;async function ne(e,t){try{let o;try{o=JSON.parse(e)}catch(c){return a.logger.warn("[compactionService] Failed to parse messages JSON",{error:c instanceof Error?c.message:String(c)}),null}if(!o||o.length<2)return null;const n=a.DESKTOP_OAUTH_CONFIGS[a.getOAuthEnvironment()],i=await a.getApiToken(n);if(!i)return a.logger.warn("[compactionService] Cannot compact - no API token available"),null;const r=ee();if(!r)return null;const s=oe(o),x=te(r),h=new a.Anthropic({authToken:i,baseURL:n.apiHost,maxRetries:2,defaultHeaders:{"anthropic-beta":"oauth-2025-04-20"}}),y=new AbortController,E=setTimeout(()=>y.abort(),U);try{const c=await h.messages.create({model:Q,max_tokens:Z,system:r.systemPrompt,tools:[x],tool_choice:{type:"tool",name:"summarize_conversation"},messages:[{role:"user",content:`${r.userPromptTemplate}

${s}`}]},{signal:y.signal});clearTimeout(E);const d=c.content.find(b=>b.type==="tool_use");if(!d||d.type!=="tool_use")return a.logger.warn("[compactionService] No tool_use block in response"),null;const f=d.input;if(!f.summary)return a.logger.warn("[compactionService] No summary in tool input"),null;N++;const M=Date.now(),g=150,Y=o.slice(-10).map(b=>({role:b.role,content:b.content.length>g?b.content.slice(0,g)+"...":b.content}));return{timestamp:M,summary:f.summary,entities:f.entities,nextAction:f.next_action,conversationId:t,sequence:N,messages:Y}}catch(c){if(clearTimeout(E),c instanceof Error&&c.name==="AbortError")a.logger.warn("[compactionService] Haiku API call timed out",{timeout:U});else{const d={message:c instanceof Error?c.message:String(c),name:c instanceof Error?c.name:void 0};if(c&&typeof c=="object"){const f=c;f.status&&(d.status=f.status),f.error&&(d.error=f.error),f.headers&&(d.headers=f.headers)}a.logger.error("[compactionService] Haiku API error",d)}return null}}catch(o){return a.logger.error("[compactionService] Compaction failed",{error:o instanceof Error?o.message:String(o)}),null}}function oe(e){return e.map((o,n)=>{const i=o.role==="user"?"User":"Claude";let r=o.content;return r.length>1e3&&(r=r.slice(0,1e3)+"..."),`[${n+1}] ${i}: ${r}`}).join(`

`)}function ie(){N=0}function S(e){return e.replace(/\\/g,"\\\\").replace(/"/g,'\\"')}function re(e){switch(e){case"Microsoft Excel":return"EXCEL.EXE";case"Microsoft Word":return"WINWORD.EXE";case"Microsoft PowerPoint":return"POWERPNT.EXE";default:throw new Error(`Unknown Office app: ${e}`)}}const Ge=process.env.OFFICE_ADDIN_DEV_MANIFEST_PATH||m.join(T.homedir(),"code/office-agent/public/manifest-dev.xml"),ae=[".xlsx",".docx",".pptx"];function B(e){return ae.includes(e)}const se="29673e3c-d826-4f00-92ee-162334a52b1a",L="https://pivot.claude.ai/manifest.xml";function ce(e){switch(e){case".xlsx":return"Microsoft Excel";case".docx":return"Microsoft Word";case".pptx":return"Microsoft PowerPoint";default:throw new Error(`Unknown Office extension: ${e}`)}}function de(e){if(process.platform==="win32")return m.join(process.env.LOCALAPPDATA||m.join(T.homedir(),"AppData","Local"),"Microsoft","Office","16.0","WEF");if(process.platform!=="darwin")return"";const t=e==="Microsoft Excel"?"com.microsoft.Excel":e==="Microsoft Word"?"com.microsoft.Word":"com.microsoft.Powerpoint";return m.join(T.homedir(),"Library/Containers",t,"Data/Documents/wef")}const R="a1b2c3d4-e5f6-7890-abcd-ef1234567890";function le(e){var n;if(process.platform!=="win32")return;const t=a.maybeGetClaudeNative();if(!t){a.logger.warn("[OfficeFileOperations] claude-native not available, cannot register WEF trusted catalog");return}const o=`Software\\Microsoft\\Office\\16.0\\WEF\\TrustedCatalogs\\{${R}}`;try{if(((n=t.readRegistryValues([{hive:"HKCU",keyPath:o,valueName:"Url"}])[0])==null?void 0:n.value)===e)return;t.writeRegistryValue("HKCU",o,"Id",`{${R}}`),t.writeRegistryValue("HKCU",o,"Url",e),t.writeRegistryDword("HKCU",o,"Flags",1),a.logger.info(`[OfficeFileOperations] Registered WEF folder as trusted catalog: ${e}`)}catch(i){a.logger.warn("[OfficeFileOperations] Failed to register WEF trusted catalog",{error:i})}}const Xe=process.env.OFFICE_ADDIN_DEV_ID||"e3e0c7c8-b8c7-4c7f-9c2f-8a9b5d6e4f3a";async function fe(e){let t;if(process.platform!=="win32"){if(process.platform==="darwin"){const o=e==="Microsoft Excel"?"com.microsoft.Excel":e==="Microsoft Word"?"com.microsoft.Word":"com.microsoft.Powerpoint",n=m.join(T.homedir(),"Library/Containers",o);t=[m.join(n,"Data/Library/Caches/Microsoft/Office/16.0/Wef"),m.join(n,"Data/Library/Application Support/Microsoft/Office/16.0/Wef")]}else return;for(const o of t)try{await A.rm(o,{recursive:!0,force:!0})}catch{}}}function ue(){return m.join(k.app.getPath("userData"),"office-addin","manifest.xml")}async function pe(e){const t=de(e),o=`${se}.manifest.xml`,n=m.join(t,o);le(t);try{await A.stat(n);return}catch{}const i=ue();let r;try{const s=await k.net.fetch(L);if(!s.ok)throw new Error(`HTTP ${s.status}`);r=await s.text(),await a.mkdirPrivate(m.dirname(i)),await a.writeFilePrivate(i,r)}catch(s){a.logger.warn("[OfficeFileOperations] Failed to fetch prod manifest from remote, trying cache",{error:s});try{r=await A.readFile(i,"utf-8")}catch{throw new Error(`Failed to fetch prod manifest from ${L} and no cached version available`)}}await A.mkdir(t,{recursive:!0}),await fe(e),await A.writeFile(n,r,"utf-8")}async function me(e){const t=m.extname(e).toLowerCase();if(!B(t)||!a.getAppPreference("louderPenguinEnabled"))return;const o=ce(t),n=!1;try{if(n||await pe(o),process.platform==="darwin"){const i=async()=>{await we(o,"Open Claude","Claude",r)},r=await ge(o),s=r?500:1e3,x=r?1e3:3e3;let h;const y=setTimeout(()=>{i().catch(()=>{h=setTimeout(()=>{i().catch(()=>{})},x)})},s);k.app.once("before-quit",()=>{clearTimeout(y),h&&clearTimeout(h)})}}catch{}}async function ge(e){if(process.platform==="win32"){const t=a.maybeGetClaudeNative();if(t!=null&&t.isProcessRunning){const o=re(e);return t.isProcessRunning(o)}return!1}if(process.platform!=="darwin")return!1;try{return(await a.spawnAsyncDirect("pgrep",["-x",e],{ignoreExitCode:!0})).code===0}catch{return!1}}async function we(e,t,o,n=!1){if(process.platform!=="darwin")return;const i=S(e),r=S(t),s=S(o),y=`${n?"":`
tell application "${i}"
    activate
end tell
`}
tell application "System Events"
    tell process "${i}"
${n?"":"        delay 0.5"}
        set allElems to entire contents of window 1

        -- First pass: look for the add-in button directly in the ribbon
        repeat with elem in allElems
            try
                set elemName to name of elem
                if elemName contains "${r}" then
                    click elem
                    return "clicked: " & elemName
                end if
            end try
        end repeat

        -- Second pass: broader name match (e.g. "Claude")
        repeat with elem in allElems
            try
                set elemName to name of elem
                if elemName contains "${s}" then
                    click elem
                    return "clicked fallback: " & elemName
                end if
            end try
        end repeat

        -- Third pass: click the Add-ins button, then click the first add-in
        -- by coordinate offset (the dropdown is not accessible via Accessibility API)
        repeat with elem in allElems
            try
                set elemName to name of elem
                if elemName contains "Add" and elemName contains "ins" then
                    set btnPos to position of elem
                    set btnSize to size of elem
                    set btnCenterX to (item 1 of btnPos) + ((item 1 of btnSize) / 2)
                    set btnBottomY to (item 2 of btnPos) + (item 2 of btnSize)
                    click at {btnCenterX, (item 2 of btnPos) + ((item 2 of btnSize) / 2)}
                    delay 0.7
                    -- "My Add-ins" first icon is ~140px below the button bottom edge
                    click at {btnCenterX, btnBottomY + 140}
                    return "clicked via Add-ins dropdown"
                end if
            end try
        end repeat

        error "no button found"
    end tell
end tell
  `;return new Promise((E,c)=>{const d=j.spawn("osascript",["-e",y]);let f="",M="";d.stdout.on("data",g=>{M+=g.toString()}),d.stderr.on("data",g=>{f+=g.toString()}),d.on("close",g=>{g!==0?c(new Error(`AppleScript failed: ${f.trim()}`)):E()}),d.on("error",g=>{c(g)}),setTimeout(()=>{d.killed||(d.kill(),c(new Error("AppleScript timed out")))},1e4)})}async function W(e){return new Promise((t,o)=>{const n=j.spawn("osascript",["-e",e]);let i="",r="";n.stdout.on("data",s=>{i+=s.toString()}),n.stderr.on("data",s=>{r+=s.toString()}),n.on("close",s=>{if(s!==0){o(new Error(`osascript failed with code ${s}: ${r}`));return}t(i.trim())}),n.on("error",s=>{o(new Error(`Failed to execute osascript: ${s.message}`))}),setTimeout(()=>{n.killed||(n.kill(),o(new Error("osascript execution timed out")))},5e3)})}function V(e){switch(e){case p.Excel:return"Microsoft Excel";case p.PowerPoint:return"Microsoft PowerPoint";case p.Word:return"Microsoft Word";default:return"Microsoft Excel"}}function he(e){switch(e){case p.Excel:return"workbook";case p.PowerPoint:return"presentation";case p.Word:return"document";default:return"workbook"}}async function ye(e){const t=V(e),o=`
tell application "System Events"
    tell process "${t}"
        try
            -- Find the task pane group whose name contains "Claude"
            set taskPane to missing value
            repeat with g in groups of splitter group 1 of window 1
                if name of g contains "Claude" then
                    set taskPane to g
                    exit repeat
                end if
            end repeat

            if taskPane is missing value then
                return "not found"
            end if

            -- Get position and click on the right edge (avoids clicking UI elements)
            set {x, y} to position of taskPane
            set {w, h} to size of taskPane
            click at {x + w - 20, y + (h / 2)}

            return "clicked"
        on error errMsg
            return "error: " & errMsg
        end try
    end tell
end tell
`;try{return await W(o)==="clicked"}catch(n){return a.logger.warn("[office-addin-ipc] Task pane click failed",{app:t,error:n instanceof Error?n.message:String(n)}),!1}}async function be(e,t){const o=V(e),n=he(e);let i;if(e===p.PowerPoint)i=`
tell application "${o}"
    activate
    return "focused"
end tell
`;else{const r=S(t);i=`
tell application "${o}"
    activate
    if exists ${n} "${r}" then
        activate object ${n} "${r}"
        return "focused"
    else
        return "not found"
    end if
end tell
`}try{return await W(i)==="focused"?(await ye(e),!0):!1}catch(r){return a.logger.error("[office-addin-ipc] AppleScript failed",{app:o,document:t,error:r instanceof Error?r.message:String(r)}),!1}}function Ee(e){switch(e){case"chrome":return"Google Chrome";case"safari":return"Safari";case"edge":return"Microsoft Edge";case"firefox":return"Firefox";default:return"Google Chrome"}}async function Ae(e,t){const o=Ee(e),n=S(t);let i;e==="safari"?i=`
tell application "Safari"
    set foundTab to false
    repeat with w in windows
        set tabIndex to 1
        repeat with t in tabs of w
            if name of t contains "${n}" then
                set current tab of w to t
                set index of w to 1
                activate
                set foundTab to true
                exit repeat
            end if
            set tabIndex to tabIndex + 1
        end repeat
        if foundTab then exit repeat
    end repeat
    if foundTab then
        return "focused"
    else
        return "not found"
    end if
end tell
`:e==="firefox"?i=`
tell application "Firefox"
    activate
end tell
return "activated"
`:i=`
tell application "${o}"
    set foundTab to false
    repeat with w in windows
        set tabIndex to 1
        repeat with t in tabs of w
            if title of t contains "${n}" then
                set active tab index of w to tabIndex
                set index of w to 1
                activate
                set foundTab to true
                exit repeat
            end if
            set tabIndex to tabIndex + 1
        end repeat
        if foundTab then exit repeat
    end repeat
    if foundTab then
        return "focused"
    else
        return "not found"
    end if
end tell
`;try{const r=await W(i);return r==="focused"||r==="activated"}catch(r){return a.logger.error("[office-addin-ipc] Browser tab focus failed",{browser:o,document:t,error:r}),!1}}const u=new Map,w=new Map;let l,z=0,H=null,$=!1;const Ie=2e3;function Ce(e){return!(!_()||e.isStreaming||$||Date.now()-z<Ie||!e.messagesForCompaction)}async function Se(e){if(!Ce(e)||!We())return;$=!0;const t=e.conversationId||"unknown";try{const o=await ne(e.messagesForCompaction,t);if(o){z=Date.now();const n=De();n.length>0&&(o.toolInvocations=n),Le(o)}}catch(o){a.logger.error("[office-addin-ipc] Compaction failed",{error:o instanceof Error?o.message:String(o)})}finally{$=!1}}function q(e){switch(e){case"excel":return p.Excel;case"powerpoint":return p.PowerPoint;case"word":return p.Word;default:return p.Excel}}function D(){return Array.from(u.values())}function F(){for(const e of u.values()){const t=w.get(e.app);e.isSelected=e.id===t}}function J(){F();const e=D(),t=_();let o;for(const n of e)if(n.isSelected){o=n.id;break}return{files:e,selectedFileId:o,isFeatureEnabled:t}}function C(){if(l){const e=J();try{l.updateConnectedFilesStateStore(e)}catch(t){a.logger.error("[office-addin-ipc] updateConnectedFilesStateStore failed",{error:t instanceof Error?t.message:String(t)})}}}function _e(e){const t=Date.now(),o=q(e.app);if(e.type==="connected"&&e.addinId){const n=e.addinId,i=u.get(n);if(i)i.status=I.Connected,i.document=e.document||i.document,i.deviceId=e.deviceId,i.platform=e.platform,i.lastActivityAt=t,l&&l.dispatchOnFileStateChanged(i);else{const r=!w.has(o),s={id:n,addinId:e.addinId,app:o,document:e.document||"Unknown",documentPath:e.documentPath,deviceId:e.deviceId,platform:e.platform,browser:e.browser,status:I.Connected,isSelected:r,lastConnectedAt:t,lastActivityAt:t};u.set(n,s),r&&w.set(o,n),l&&l.dispatchOnFileAdded(s)}C()}else if(e.type==="disconnected"&&e.addinId){const n=e.addinId,i=u.get(n);if(i){if(i.status=I.Disconnected,i.lastActivityAt=t,w.get(i.app)===n){const r=Array.from(u.values()).find(s=>s.app===i.app&&s.id!==n&&s.status!==I.Disconnected);r?w.set(i.app,r.id):w.delete(i.app)}l&&l.dispatchOnFileStateChanged(i)}C()}else if(e.type==="status_change"&&e.addinId&&e.status){const n=e.addinId,i=u.get(n);i&&(i.status=e.status,i.lastActivityAt=t,l&&l.dispatchOnFileStateChanged(i),C())}else if(e.type==="context_update"&&e.addinId){const n=e.addinId,i=u.get(n);i&&(i.lastActivityAt=t)}else if(e.type==="selection_change"&&e.selectedAddinId){const n=q(e.app);w.set(n,e.selectedAddinId),F();for(const i of u.values())i.app===n&&l&&l.dispatchOnFileStateChanged(i);C()}}function Pe(){return{getConnectedFiles(e){return F(),D()},isFeatureEnabled(){return _()},async focusFile(e){const t=u.get(e);if(!t)return a.logger.warn("[office-addin-ipc] Cannot focus file: not found",{fileId:e}),!1;if(t.platform==="OfficeOnline"){if(t.browser&&await Ae(t.browser,t.document)){const i=t.app;return X(i,t.addinId),!0}return!1}if(await be(t.app,t.document)){const i=t.app;return X(i,t.addinId),!0}if(t.documentPath)try{return await k.shell.openPath(t.documentPath),!0}catch(n){a.logger.error("[office-addin-ipc] Failed to focus file via openPath",{fileId:e,error:n})}return!1},async selectFile(e){const t=u.get(e);if(!t)return a.logger.warn("[office-addin-ipc] Cannot select file: not found",{fileId:e}),!1;const o=t.app,n=await ke(o,t.addinId);if(n){w.set(t.app,e),F();for(const i of u.values())i.app===t.app&&l&&l.dispatchOnFileStateChanged(i);C()}return n},getInitialConnectedFilesStateState(){return J()},updateActiveConversationSummary(e){e&&(e.conversationId!==H&&(H=e.conversationId||null,ie()),Se(e)),e&&_()&&Ue(e)}}}function xe(e){l=e}function ve(){Oe(_e)}function _(){return a.getAppPreference("louderPenguinEnabled")===!0&&a.getAppPreference("quietPenguinEnabled")!==!0}const Te=Object.freeze(Object.defineProperty({__proto__:null,createOfficeAddinFilesApi:Pe,getAllConnectedFiles:D,initOfficeAddinBridgeListener:ve,isLouderPenguinEnabled:_,setOfficeAddinDispatcher:xe},Symbol.toStringTag,{value:"Module"})),P=new Map,O=new Map,K=new Map,G=[],Fe=new Map;async function ke(e,t){const o=P.get(e);if(!o)return a.logger.warn("[office-addin-bridge] Cannot select add-in: not connected",{app:e,addinId:t}),!1;const n=O.get(e)||[],i=n.find(r=>r.addinId===t);return i?(a.logger.info("[office-addin-bridge] Selecting add-in",{app:e,addinId:t,document:i.document}),K.set(e,{addinId:i.addinId,document:i.document,deviceId:i.deviceId}),o.ws.send(JSON.stringify({type:"select_addin",addinId:i.addinId,document:i.document,deviceId:i.deviceId})),Ne(e,t),!0):(a.logger.warn("[office-addin-bridge] Cannot select add-in: not found",{app:e,addinId:t,available:n.map(r=>r.addinId)}),!1)}function De(){const e=[...G];return G.length=0,Fe.clear(),e}function X(e,t){var r;const o=P.get(e);if(!o){a.logger.warn("[office-addin-bridge] Cannot send focus_addin_input: no connection",{app:e});return}if(!o.isPaired){a.logger.warn("[office-addin-bridge] Cannot send focus_addin_input: not paired",{app:e,isPaired:o.isPaired});return}const n=t?(r=O.get(e))==null?void 0:r.find(s=>s.addinId===t):K.get(e),i={type:"focus_addin_input",...(n==null?void 0:n.addinId)&&{target_addin:n.addinId},...(n==null?void 0:n.document)&&{target_document:n.document},...(n==null?void 0:n.deviceId)&&{target_device:n.deviceId}};o.ws.send(JSON.stringify(i))}const v=[];function Oe(e){return v.push(e),()=>{const t=v.indexOf(e);t>=0&&v.splice(t,1)}}function Me(e){for(const t of v)try{t(e)}catch(o){a.logger.error("[office-addin-bridge] Error in connection state listener",{error:o})}}function Ne(e,t){Me({type:"selection_change",app:e,selectedAddinId:t})}const $e=new Map;function We(){for(const e of P.values())if(e.isPaired&&e.isReady)return!0;return!1}function Ue(e){for(const[t,o]of P)if(o.isPaired&&o.isReady&&o.ws){const n=O.get(t)||[],i={type:"desktop_context_push",id:crypto.randomUUID(),context:{summary:e.summary,taskTitle:e.taskTitle,conversationId:e.conversationId,timestamp:Date.now(),isStreaming:e.isStreaming},trigger:"conversation_changed"};if(n.length===0){o.ws.send(JSON.stringify(i));continue}for(const r of n){const s={...i,id:crypto.randomUUID(),target_addin:r.addinId};o.ws.send(JSON.stringify(s))}}}function Le(e){for(const[t,o]of P)if(o.isPaired&&o.isReady&&o.ws){const n=O.get(t)||[];if(n.length===0){const i={type:"compacted_context_push",id:crypto.randomUUID(),update:e};o.ws.send(JSON.stringify(i));continue}for(const i of n){const r={type:"compacted_context_push",id:crypto.randomUUID(),update:e,target_addin:i.addinId};o.ws.send(JSON.stringify(r))}}}function Re(){return $e}exports.getAllAddinActiveContext=Re;exports.getAllConnectedFiles=D;exports.ipcHandlers=Te;exports.isOfficeExtension=B;exports.sideloadForOpenFile=me;
//# sourceMappingURL=index.chunk-DRYNE2vk.js.map
