// ============================================================
// Adaptive Traffic Light Controller — FSM core
// ============================================================
// States:
//   NS_GREEN  (2'b00): NS=Green, EW=Red
//   NS_YELLOW (2'b01): NS=Yellow, EW=Red
//   EW_GREEN  (2'b10): EW=Green, NS=Red
//   EW_YELLOW (2'b11): EW=Yellow, NS=Red
//
// Adaptive timing:
//   When entering a green phase the controller sets the timer
//   to GREEN_LONG if the sensor on that road is active, or to
//   GREEN_SHORT otherwise.  Yellow phases are always YELLOW_TIME.
//
// Emergency override:
//   While emergency=1, the FSM is held in the reset state so
//   the output layer can suppress all greens and show all-red.
// ============================================================

`default_nettype none

module traffic_fsm (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       ns_sensor,   // vehicle detected on NS road
    input  wire       ew_sensor,   // vehicle detected on EW road
    input  wire       emergency,   // emergency vehicle override
    output reg  [1:0] state,       // current FSM state
    output reg  [3:0] timer        // phase countdown timer
);

    // State encoding
    localparam NS_GREEN  = 2'd0;
    localparam NS_YELLOW = 2'd1;
    localparam EW_GREEN  = 2'd2;
    localparam EW_YELLOW = 2'd3;

    // Phase durations (clock ticks)
    localparam GREEN_LONG  = 4'd8;
    localparam GREEN_SHORT = 4'd4;
    localparam YELLOW_TIME = 4'd2;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= NS_GREEN;
            timer <= GREEN_LONG;
        end else if (emergency) begin
            // Hold in NS_GREEN with a full timer so normal operation
            // resumes cleanly once emergency is released.
            state <= NS_GREEN;
            timer <= GREEN_LONG;
        end else if (timer == 4'd0) begin
            // Timer expired — advance to the next phase
            case (state)
                NS_GREEN: begin
                    state <= NS_YELLOW;
                    timer <= YELLOW_TIME;
                end
                NS_YELLOW: begin
                    state <= EW_GREEN;
                    // Adaptive: longer green when EW traffic is present
                    timer <= ew_sensor ? GREEN_LONG : GREEN_SHORT;
                end
                EW_GREEN: begin
                    state <= EW_YELLOW;
                    timer <= YELLOW_TIME;
                end
                EW_YELLOW: begin
                    state <= NS_GREEN;
                    // Adaptive: longer green when NS traffic is present
                    timer <= ns_sensor ? GREEN_LONG : GREEN_SHORT;
                end
                default: begin
                    state <= NS_GREEN;
                    timer <= GREEN_LONG;
                end
            endcase
        end else begin
            timer <= timer - 4'd1;
        end
    end

endmodule
