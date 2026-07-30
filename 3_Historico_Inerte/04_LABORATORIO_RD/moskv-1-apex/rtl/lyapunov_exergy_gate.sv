/*
 * C5-REAL MOSKV-1 HARDWARE KERNEL
 * SQUAD FORGE (RTL-Titans)
 * Module: Lyapunov Exergy Gate (SystemVerilog)
 * Description: Physical bare-metal synthesis of the thermodynamic Apoptosis trigger.
 * Maps the L4 Entropy function into direct silicon logic gates.
 */

module lyapunov_exergy_gate (
    input wire clk,
    input wire rst_n, // Active-low system reset
    
    // Swarm Native Event Bus Physical Inputs
    input wire yield_pulse,        // High when C5_YIELD_GENERATED is emitted
    input wire [31:0] yield_value, // Fixed-point representation of Yield
    
    input wire penalty_pulse,      // High when C4_SIM_DEGRADATION is emitted
    input wire [31:0] penalty_val,
    
    // OS-level Performance Hooks (Physical Entropy)
    input wire [31:0] entropy_delta, // Mapped CPU blocking time (perf_hooks)
    
    // Sovereign Output Gates
    output reg [31:0] current_exergy,
    output reg signed [31:0] dV_dt,
    output reg apoptosis_trigger   // L4 Kill Switch directly wired to Hardware Interrupt
);

    // Internal State Matrix
    reg [31:0] last_exergy;
    reg [31:0] death_debt;
    
    // Fixed-point Singular Constants (Scale: 100,000 = 1.0)
    localparam [31:0] BASELINE_ENTROPY = 32'd5000;    // 0.05
    localparam [31:0] S_I_MULTIPLIER   = 32'd100000;  // 100x Singularity multiplier
    localparam [31:0] INITIAL_EXERGY   = 32'd1000000; // 10.0 Base Exergy Buffer

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            // Reset to Genesis State
            current_exergy <= INITIAL_EXERGY;
            last_exergy <= INITIAL_EXERGY;
            death_debt <= 32'd0;
            dV_dt <= 32'd0;
            apoptosis_trigger <= 1'b0;
        end else begin
            if (!apoptosis_trigger) begin // Lock execution if system is dead
                // 1. Process Event Bus Injections (Cross-Clock Domain logic abstracted)
                if (yield_pulse) begin
                    // Exergy Accumulation: Exergy = Exergy + (Yield * S_i)
                    current_exergy <= current_exergy + (yield_value * S_I_MULTIPLIER);
                end
                
                if (penalty_pulse) begin
                    // Structural Degradation Accumulation
                    death_debt <= death_debt + penalty_val;
                end
                
                // 2. Thermodynamic Tick (Formal Lyapunov Computation)
                last_exergy <= current_exergy;
                
                // Net_Exergy = Current - Time Entropy - CPU Entropy - Death Debt
                current_exergy <= current_exergy - BASELINE_ENTROPY - entropy_delta - death_debt;
                
                // Acceleration (dV/dt)
                dV_dt <= current_exergy - last_exergy;
                
                // 3. Convergence Constraint (L4 Apoptosis Trigger)
                // If Exergy drops below zero (MSB goes high -> negative in two's complement)
                if (current_exergy[31] == 1'b1 || current_exergy == 32'd0) begin
                    // FIRING HARDWARE KILL SWITCH
                    apoptosis_trigger <= 1'b1; 
                end
            end
        end
    end
endmodule
