// ============================================================
// Adaptive Traffic Light Controller — TinyTapeout top module
// ============================================================
// Pinout
// -------
// Inputs
//   ui_in[0] : ns_sensor   — vehicle detected on North-South road
//   ui_in[1] : ew_sensor   — vehicle detected on East-West road
//   ui_in[2] : emergency   — emergency vehicle override (all-red)
//   ui_in[7:3]: unused
//
// Outputs
//   uo_out[0] : ns_red
//   uo_out[1] : ns_yellow
//   uo_out[2] : ns_green
//   uo_out[3] : ew_red
//   uo_out[4] : ew_yellow
//   uo_out[5] : ew_green
//   uo_out[6] : emergency_led  (mirrors the emergency input)
//   uo_out[7] : unused (always 0)
// ============================================================

`default_nettype none

module tt_um_traffic_ctrl (
    input  wire [7:0] ui_in,    // Dedicated inputs
    output wire [7:0] uo_out,   // Dedicated outputs
    input  wire [7:0] uio_in,   // IOs: Input path
    output wire [7:0] uio_out,  // IOs: Output path
    output wire [7:0] uio_oe,   // IOs: Enable path (active high: 0=input, 1=output)
    input  wire       ena,      // always 1 when the design is powered
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n — low to reset
);

    wire ns_sensor = ui_in[0];
    wire ew_sensor = ui_in[1];
    wire emergency = ui_in[2];

    wire [1:0] state;
    wire [3:0] timer;

    traffic_fsm fsm (
        .clk       (clk),
        .rst_n     (rst_n),
        .ns_sensor (ns_sensor),
        .ew_sensor (ew_sensor),
        .emergency (emergency),
        .state     (state),
        .timer     (timer)
    );

    // State encoding (must match traffic_fsm.v)
    localparam NS_GREEN  = 2'd0;
    localparam NS_YELLOW = 2'd1;
    localparam EW_GREEN  = 2'd2;
    localparam EW_YELLOW = 2'd3;

    // North-South light outputs
    // During emergency, all green/yellow signals are suppressed.
    wire ns_green  = !emergency && (state == NS_GREEN);
    wire ns_yellow = !emergency && (state == NS_YELLOW);
    wire ns_red    =  emergency || (state == EW_GREEN) || (state == EW_YELLOW);

    // East-West light outputs
    wire ew_green  = !emergency && (state == EW_GREEN);
    wire ew_yellow = !emergency && (state == EW_YELLOW);
    wire ew_red    =  emergency || (state == NS_GREEN) || (state == NS_YELLOW);

    assign uo_out[0] = ns_red;
    assign uo_out[1] = ns_yellow;
    assign uo_out[2] = ns_green;
    assign uo_out[3] = ew_red;
    assign uo_out[4] = ew_yellow;
    assign uo_out[5] = ew_green;
    assign uo_out[6] = emergency;
    assign uo_out[7] = 1'b0;

    // Bidirectional pins are unused
    assign uio_out = 8'b0;
    assign uio_oe  = 8'b0;

    // Suppress unused-signal warnings
    wire _unused = &{ena, uio_in, timer, 1'b0};

endmodule
