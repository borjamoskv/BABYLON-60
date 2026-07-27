`timescale 1ns / 1ps

module moskv_core_top (
    input wire sys_clk,
    input wire sys_rst_n,
    
    // Bus Interface
    input wire nats_rx_valid,
    input wire [255:0] nats_rx_prev_hash,
    input wire [511:0] nats_rx_payload,
    input wire [31:0] nats_rx_entropy,
    
    // Output Interface
    output wire [255:0] cortex_current_hash,
    output wire graph_mutation_req,
    output wire [63:0] graph_cypher_ptr,
    output wire system_anergy_fault
);

    // Ledger Instantiation
    hash_ledger_unit #(
        .HASH_WIDTH(256),
        .PAYLOAD_WIDTH(512)
    ) u_hash_ledger (
        .clk(sys_clk),
        .rst_n(sys_rst_n),
        .valid_in(nats_rx_valid),
        .prev_hash_in(nats_rx_prev_hash),
        .payload_in(nats_rx_payload),
        .valid_out(), // Interconnect valid signal
        .current_hash_out(cortex_current_hash),
        .exergy_violation(system_anergy_fault)
    );
    
    // Autopoiesis Synthesis Instantiation
    auto_compile_kernel #(
        .ENTROPY_WIDTH(32),
        .ADDR_WIDTH(64)
    ) u_auto_compile (
        .clk(sys_clk),
        .rst_n(sys_rst_n),
        .event_valid(nats_rx_valid),
        .current_entropy(nats_rx_entropy),
        .mutation_req(graph_mutation_req),
        .cypher_instruction_ptr(graph_cypher_ptr)
    );

endmodule
