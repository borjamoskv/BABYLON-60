// C5-REAL EXERGY CERTIFIED

import { Record, Union } from "./fable_modules/fable-library-ts.5.8.0/Types.ts";
import { class_type, record_type, string_type, float64_type, union_type, TypeInfo } from "./fable_modules/fable-library-ts.5.8.0/Reflection.ts";
import { int32, float64 } from "./fable_modules/fable-library-ts.5.8.0/Int32.ts";
import { toFail, isNullOrEmpty, replicate, printf, toText } from "./fable_modules/fable-library-ts.5.8.0/String.ts";
import { Exception, comparePrimitives, IComparable, IEquatable } from "./fable_modules/fable-library-ts.5.8.0/Util.ts";
import { FSharpMap__TryFind, FSharpMap__Add, FSharpMap__ContainsKey, empty, FSharpMap } from "./fable_modules/fable-library-ts.5.8.0/Map.ts";
import { FSharpResult$2_$union, FSharpResult$2_Ok, FSharpResult$2_Error$ } from "./fable_modules/fable-library-ts.5.8.0/Result.ts";
import { item, length, empty as empty_1, cons, FSharpList } from "./fable_modules/fable-library-ts.5.8.0/List.ts";
import { value, Option } from "./fable_modules/fable-library-ts.5.8.0/Option.ts";

export type IRPAutomata_Gravity_$union =
    | IRPAutomata_Gravity<0>
    | IRPAutomata_Gravity<1>
    | IRPAutomata_Gravity<2>
    | IRPAutomata_Gravity<3>

export type IRPAutomata_Gravity_$cases = {
    0: ["C5_ColapsoOntologico", []],
    1: ["C4_DegradacionGeometrica", []],
    2: ["C3_FluctuacionTermica", []],
    3: ["C2_FriccionComputacional", []]
}

export function IRPAutomata_Gravity_C5_ColapsoOntologico() {
    return IRPAutomata_Gravity.C5_ColapsoOntologico;
}

export function IRPAutomata_Gravity_C4_DegradacionGeometrica() {
    return IRPAutomata_Gravity.C4_DegradacionGeometrica;
}

export function IRPAutomata_Gravity_C3_FluctuacionTermica() {
    return IRPAutomata_Gravity.C3_FluctuacionTermica;
}

export function IRPAutomata_Gravity_C2_FriccionComputacional() {
    return IRPAutomata_Gravity.C2_FriccionComputacional;
}

export class IRPAutomata_Gravity<Tag extends keyof IRPAutomata_Gravity_$cases> extends Union<Tag, IRPAutomata_Gravity_$cases[Tag][0]> {
    constructor(tag: Tag, fields: IRPAutomata_Gravity_$cases[Tag][1]) {
        super();
        this.tag = tag;
        this.fields = fields;
    }
    readonly tag: Tag;
    readonly fields: IRPAutomata_Gravity_$cases[Tag][1];
    cases() {
        return ["C5_ColapsoOntologico", "C4_DegradacionGeometrica", "C3_FluctuacionTermica", "C2_FriccionComputacional"];
    }
    static readonly C5_ColapsoOntologico: any = new IRPAutomata_Gravity<0>(0, []);
    static readonly C4_DegradacionGeometrica: any = new IRPAutomata_Gravity<1>(1, []);
    static readonly C3_FluctuacionTermica: any = new IRPAutomata_Gravity<2>(2, []);
    static readonly C2_FriccionComputacional: any = new IRPAutomata_Gravity<3>(3, []);
}

export function IRPAutomata_Gravity_$reflection(): TypeInfo {
    return union_type("Babylon60.Domain.IRPAutomata.Gravity", [], IRPAutomata_Gravity, () => [[], [], [], []]);
}

export type IRPAutomata_MembraneState_$union =
    | IRPAutomata_MembraneState<0>
    | IRPAutomata_MembraneState<1>
    | IRPAutomata_MembraneState<2>
    | IRPAutomata_MembraneState<3>

export type IRPAutomata_MembraneState_$cases = {
    0: ["Stable", [float64]],
    1: ["Smoothing", [float64]],
    2: ["Rollback", [string]],
    3: ["Apoptosis", [string]]
}

export function IRPAutomata_MembraneState_Stable(entropyLevel: float64) {
    return new IRPAutomata_MembraneState<0>(0, [entropyLevel]);
}

export function IRPAutomata_MembraneState_Smoothing(variance: float64) {
    return new IRPAutomata_MembraneState<1>(1, [variance]);
}

export function IRPAutomata_MembraneState_Rollback(targetHash: string) {
    return new IRPAutomata_MembraneState<2>(2, [targetHash]);
}

export function IRPAutomata_MembraneState_Apoptosis(taintLog: string) {
    return new IRPAutomata_MembraneState<3>(3, [taintLog]);
}

export class IRPAutomata_MembraneState<Tag extends keyof IRPAutomata_MembraneState_$cases> extends Union<Tag, IRPAutomata_MembraneState_$cases[Tag][0]> {
    constructor(tag: Tag, fields: IRPAutomata_MembraneState_$cases[Tag][1]) {
        super();
        this.tag = tag;
        this.fields = fields;
    }
    readonly tag: Tag;
    readonly fields: IRPAutomata_MembraneState_$cases[Tag][1];
    cases() {
        return ["Stable", "Smoothing", "Rollback", "Apoptosis"];
    }
}

export function IRPAutomata_MembraneState_$reflection(): TypeInfo {
    return union_type("Babylon60.Domain.IRPAutomata.MembraneState", [], IRPAutomata_MembraneState, () => [[["entropyLevel", float64_type]], [["variance", float64_type]], [["targetHash", string_type]], [["taintLog", string_type]]]);
}

export function IRPAutomata_applyThermalStress(currentState: IRPAutomata_MembraneState_$union, gravity: IRPAutomata_Gravity_$union): IRPAutomata_MembraneState_$union {
    switch (gravity.tag) {
        case /* C3_FluctuacionTermica */ 2:
            switch (currentState.tag) {
                case /* Smoothing */ 1:
                    return IRPAutomata_MembraneState_Smoothing((currentState.fields[0] as float64) + 0.1);
                case /* Rollback */ 2:
                    return IRPAutomata_MembraneState_Rollback(currentState.fields[0] as string);
                case /* Apoptosis */ 3:
                    return IRPAutomata_MembraneState_Apoptosis(currentState.fields[0] as string);
                default:
                    return IRPAutomata_MembraneState_Smoothing((currentState.fields[0] as float64) * 1.5);
            }
        case /* C4_DegradacionGeometrica */ 1:
            if ((currentState.tag as int32) === /* Apoptosis */ 3) {
                return IRPAutomata_MembraneState_Apoptosis(currentState.fields[0] as string);
            }
            else {
                return IRPAutomata_MembraneState_Rollback("LATEST_BFT_CHECKPOINT");
            }
        case /* C5_ColapsoOntologico */ 0:
            return IRPAutomata_MembraneState_Apoptosis("TAINT:C5_REAL_TRUNCATED");
        default:
            if ((currentState.tag as int32) === /* Stable */ 0) {
                return IRPAutomata_MembraneState_Stable((currentState.fields[0] as float64) + 0.01);
            }
            else {
                return currentState;
            }
    }
}

export function IRPAutomata_commitBoundary(state: IRPAutomata_MembraneState_$union): string {
    switch (state.tag) {
        case /* Smoothing */ 1: {
            const v = state.fields[0] as float64;
            return toText(printf("STATUS:SMOOTHING|VARIANCE:%.4f"))(v);
        }
        case /* Rollback */ 2: {
            const h = state.fields[0] as string;
            return toText(printf("STATUS:ROLLBACK|HASH:%s"))(h);
        }
        case /* Apoptosis */ 3: {
            const t = state.fields[0] as string;
            return toText(printf("STATUS:APOPTOSIS|TAINT:%s"))(t);
        }
        default: {
            const e = state.fields[0] as float64;
            return toText(printf("STATUS:OK|ENTROPY:%.4f"))(e);
        }
    }
}

export class LedgerValidation_StateNode extends Record implements IEquatable<LedgerValidation_StateNode>, IComparable<LedgerValidation_StateNode> {
    readonly NodeId: string;
    readonly ParentId: string;
    readonly ClaimSummary: string;
    readonly PayloadHash: string;
    constructor(NodeId: string, ParentId: string, ClaimSummary: string, PayloadHash: string) {
        super();
        this.NodeId = NodeId;
        this.ParentId = ParentId;
        this.ClaimSummary = ClaimSummary;
        this.PayloadHash = PayloadHash;
    }
}

export function LedgerValidation_StateNode_$reflection(): TypeInfo {
    return record_type("Babylon60.Domain.LedgerValidation.StateNode", [], LedgerValidation_StateNode, () => [["NodeId", string_type], ["ParentId", string_type], ["ClaimSummary", string_type], ["PayloadHash", string_type]]);
}

export type LedgerValidation_ValidationError_$union =
    | LedgerValidation_ValidationError<0>
    | LedgerValidation_ValidationError<1>
    | LedgerValidation_ValidationError<2>
    | LedgerValidation_ValidationError<3>

export type LedgerValidation_ValidationError_$cases = {
    0: ["ParentNotFound", [string]],
    1: ["InvalidClaimLength", [string]],
    2: ["InvalidHashLength", [string, string]],
    3: ["DuplicateNodeId", [string]]
}

export function LedgerValidation_ValidationError_ParentNotFound(parentId: string) {
    return new LedgerValidation_ValidationError<0>(0, [parentId]);
}

export function LedgerValidation_ValidationError_InvalidClaimLength(claim: string) {
    return new LedgerValidation_ValidationError<1>(1, [claim]);
}

export function LedgerValidation_ValidationError_InvalidHashLength(hashName: string, hash: string) {
    return new LedgerValidation_ValidationError<2>(2, [hashName, hash]);
}

export function LedgerValidation_ValidationError_DuplicateNodeId(nodeId: string) {
    return new LedgerValidation_ValidationError<3>(3, [nodeId]);
}

export class LedgerValidation_ValidationError<Tag extends keyof LedgerValidation_ValidationError_$cases> extends Union<Tag, LedgerValidation_ValidationError_$cases[Tag][0]> {
    constructor(tag: Tag, fields: LedgerValidation_ValidationError_$cases[Tag][1]) {
        super();
        this.tag = tag;
        this.fields = fields;
    }
    readonly tag: Tag;
    readonly fields: LedgerValidation_ValidationError_$cases[Tag][1];
    cases() {
        return ["ParentNotFound", "InvalidClaimLength", "InvalidHashLength", "DuplicateNodeId"];
    }
}

export function LedgerValidation_ValidationError_$reflection(): TypeInfo {
    return union_type("Babylon60.Domain.LedgerValidation.ValidationError", [], LedgerValidation_ValidationError, () => [[["parentId", string_type]], [["claim", string_type]], [["hashName", string_type], ["hash", string_type]], [["nodeId", string_type]]]);
}

export class LedgerValidation_LedgerState extends Record implements IEquatable<LedgerValidation_LedgerState>, IComparable<LedgerValidation_LedgerState> {
    readonly Nodes: FSharpMap<string, LedgerValidation_StateNode>;
    readonly GenesisId: string;
    constructor(Nodes: FSharpMap<string, LedgerValidation_StateNode>, GenesisId: string) {
        super();
        this.Nodes = Nodes;
        this.GenesisId = GenesisId;
    }
}

export function LedgerValidation_LedgerState_$reflection(): TypeInfo {
    return record_type("Babylon60.Domain.LedgerValidation.LedgerState", [], LedgerValidation_LedgerState, () => [["Nodes", class_type("Microsoft.FSharp.Collections.FSharpMap`2", [string_type, LedgerValidation_StateNode_$reflection()])], ["GenesisId", string_type]]);
}

export function LedgerValidation_genesisLedger(): LedgerValidation_LedgerState {
    return new LedgerValidation_LedgerState(empty<string, LedgerValidation_StateNode>({
        Compare: (x: string, y: string): int32 => (comparePrimitives(x, y) | 0),
    }), replicate(64, "0"));
}

export function LedgerValidation_validateAndAppend(state: LedgerValidation_LedgerState, parent: string, claim: string, payload: string, nodeId: string): FSharpResult$2_$union<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union> {
    if ((parent !== state.GenesisId) && !FSharpMap__ContainsKey(state.Nodes, parent)) {
        return FSharpResult$2_Error$<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union>(LedgerValidation_ValidationError_ParentNotFound(parent));
    }
    else if (isNullOrEmpty(claim) ? true : (claim.length > 64)) {
        return FSharpResult$2_Error$<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union>(LedgerValidation_ValidationError_InvalidClaimLength(claim));
    }
    else if (payload.length !== 64) {
        return FSharpResult$2_Error$<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union>(LedgerValidation_ValidationError_InvalidHashLength("PayloadHash", payload));
    }
    else if (nodeId.length !== 64) {
        return FSharpResult$2_Error$<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union>(LedgerValidation_ValidationError_InvalidHashLength("NodeId", nodeId));
    }
    else if (FSharpMap__ContainsKey(state.Nodes, nodeId)) {
        return FSharpResult$2_Error$<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union>(LedgerValidation_ValidationError_DuplicateNodeId(nodeId));
    }
    else {
        const newNode: LedgerValidation_StateNode = new LedgerValidation_StateNode(nodeId, parent, claim, payload);
        return FSharpResult$2_Ok<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union>([new LedgerValidation_LedgerState(FSharpMap__Add(state.Nodes, nodeId, newNode), state.GenesisId), newNode] as [LedgerValidation_LedgerState, LedgerValidation_StateNode]);
    }
}

/**
 * Trazado de ruta puramente funcional y recursivo de cola (Tail-Recursive)
 */
export function LedgerValidation_getPath(state: LedgerValidation_LedgerState, headId: string): FSharpResult$2_$union<FSharpList<LedgerValidation_StateNode>, string> {
    const loop = (currId_mut: string, acc_mut: FSharpList<LedgerValidation_StateNode>): FSharpResult$2_$union<FSharpList<LedgerValidation_StateNode>, string> => {
        loop:
        while (true) {
            const currId: string = currId_mut, acc: FSharpList<LedgerValidation_StateNode> = acc_mut;
            if (currId === state.GenesisId) {
                return FSharpResult$2_Ok<FSharpList<LedgerValidation_StateNode>, string>(acc);
            }
            else {
                const matchValue: Option<LedgerValidation_StateNode> = FSharpMap__TryFind(state.Nodes, currId);
                if (matchValue == null) {
                    return FSharpResult$2_Error$<FSharpList<LedgerValidation_StateNode>, string>(toText(printf("Fail-fast: Missing node in path trace: %s"))(currId));
                }
                else {
                    const node: LedgerValidation_StateNode = value(matchValue);
                    currId_mut = node.ParentId;
                    acc_mut = cons(node, acc);
                    continue loop;
                }
            }
            break;
        }
    };
    return loop(headId, empty_1<LedgerValidation_StateNode>());
}

export function LedgerTests_runVerificationSuite(): void {
    const state0: LedgerValidation_LedgerState = LedgerValidation_genesisLedger();
    const payload1: string = replicate(64, "a");
    const payload2: string = replicate(64, "b");
    const node1Id: string = replicate(64, "1");
    const node2Id: string = replicate(64, "2");
    const matchValue: FSharpResult$2_$union<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union> = LedgerValidation_validateAndAppend(state0, state0.GenesisId, "Node 1", payload1, node1Id);
    if ((matchValue.tag as int32) === /* Ok */ 0) {
        const n1: LedgerValidation_StateNode = (matchValue.fields[0] as [LedgerValidation_LedgerState, LedgerValidation_StateNode])[1];
        const matchValue_1: FSharpResult$2_$union<[LedgerValidation_LedgerState, LedgerValidation_StateNode], LedgerValidation_ValidationError_$union> = LedgerValidation_validateAndAppend((matchValue.fields[0] as [LedgerValidation_LedgerState, LedgerValidation_StateNode])[0], n1.NodeId, "Node 2", payload2, node2Id);
        if ((matchValue_1.tag as int32) === /* Ok */ 0) {
            const n2: LedgerValidation_StateNode = (matchValue_1.fields[0] as [LedgerValidation_LedgerState, LedgerValidation_StateNode])[1];
            const matchValue_2: FSharpResult$2_$union<FSharpList<LedgerValidation_StateNode>, string> = LedgerValidation_getPath((matchValue_1.fields[0] as [LedgerValidation_LedgerState, LedgerValidation_StateNode])[0], n2.NodeId);
            if ((matchValue_2.tag as int32) === /* Ok */ 0) {
                const path = matchValue_2.fields[0] as FSharpList<LedgerValidation_StateNode>;
                if (length(path) !== 2) {
                    const arg_3: int32 = length(path) | 0;
                    toFail(printf("Test failed: expected path length 2, got %d"))(arg_3);
                }
                if ((item(0, path).NodeId !== n1.NodeId) ? true : (item(1, path).NodeId !== n2.NodeId)) {
                    throw new Exception("Test failed: path nodes order or identity mismatch");
                }
                console.log("✅ F# Domain Kernel: All native assertions passed.");
            }
            else {
                const msg = matchValue_2.fields[0] as string;
                toFail(printf("Test failed: getPath trace error: %s"))(msg);
            }
        }
        else {
            const err_1 = matchValue_1.fields[0] as LedgerValidation_ValidationError_$union;
            toFail(printf("Test failed: Node 2 insertion error: %A"))(err_1);
        }
    }
    else {
        const err = matchValue.fields[0] as LedgerValidation_ValidationError_$union;
        toFail(printf("Test failed: Node 1 insertion error: %A"))(err);
    }
}

