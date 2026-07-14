
import { Union } from "./fable_modules/fable-library-js.5.8.0/Types.js";
import { string_type, float64_type, union_type } from "./fable_modules/fable-library-js.5.8.0/Reflection.js";
import { printf, toText } from "./fable_modules/fable-library-js.5.8.0/String.js";

export class Gravity extends Union {
    constructor(tag, fields) {
        super();
        this.tag = tag;
        this.fields = fields;
    }
    cases() {
        return ["C5_ColapsoOntologico", "C4_DegradacionGeometrica", "C3_FluctuacionTermica", "C2_FriccionComputacional"];
    }
    static C5_ColapsoOntologico = new Gravity(0, []);
    static C4_DegradacionGeometrica = new Gravity(1, []);
    static C3_FluctuacionTermica = new Gravity(2, []);
    static C2_FriccionComputacional = new Gravity(3, []);
}

export function Gravity_$reflection() {
    return union_type("Babylon60.Domain.IRPAutomata.Gravity", [], Gravity, () => [[], [], [], []]);
}

export class MembraneState extends Union {
    constructor(tag, fields) {
        super();
        this.tag = tag;
        this.fields = fields;
    }
    cases() {
        return ["Stable", "Smoothing", "Rollback", "Apoptosis"];
    }
}

export function MembraneState_$reflection() {
    return union_type("Babylon60.Domain.IRPAutomata.MembraneState", [], MembraneState, () => [[["entropyLevel", float64_type]], [["variance", float64_type]], [["targetHash", string_type]], [["taintLog", string_type]]]);
}

export function applyThermalStress(currentState, gravity) {
    switch (gravity.tag) {
        case 2:
            switch (currentState.tag) {
                case 1:
                    return new MembraneState(/* Smoothing */ 1, [currentState.fields[0] + 0.1]);
                case 2:
                    return new MembraneState(/* Rollback */ 2, [currentState.fields[0]]);
                case 3:
                    return new MembraneState(/* Apoptosis */ 3, [currentState.fields[0]]);
                default:
                    return new MembraneState(/* Smoothing */ 1, [currentState.fields[0] * 1.5]);
            }
        case 1:
            if (currentState.tag === 3) {
                return new MembraneState(/* Apoptosis */ 3, [currentState.fields[0]]);
            }
            else {
                return new MembraneState(/* Rollback */ 2, ["LATEST_BFT_CHECKPOINT"]);
            }
        case 0:
            return new MembraneState(/* Apoptosis */ 3, ["TAINT:C5_REAL_TRUNCATED"]);
        default:
            if (currentState.tag === 0) {
                return new MembraneState(/* Stable */ 0, [currentState.fields[0] + 0.01]);
            }
            else {
                return currentState;
            }
    }
}

export function commitBoundary(state) {
    switch (state.tag) {
        case 1:
            return toText(printf("STATUS:SMOOTHING|VARIANCE:%.4f"))(state.fields[0]);
        case 2:
            return toText(printf("STATUS:ROLLBACK|HASH:%s"))(state.fields[0]);
        case 3:
            return toText(printf("STATUS:APOPTOSIS|TAINT:%s"))(state.fields[0]);
        default:
            return toText(printf("STATUS:OK|ENTROPY:%.4f"))(state.fields[0]);
    }
}

