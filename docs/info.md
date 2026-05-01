# Adaptive Traffic Light Controller with Emergency Override

## How it works

This project implements an adaptive finite-state-machine (FSM) traffic light
controller for a two-road intersection (North-South and East-West).

### States

| State     | NS Light | EW Light |
|-----------|----------|----------|
| NS_GREEN  | Green    | Red      |
| NS_YELLOW | Yellow   | Red      |
| EW_GREEN  | Red      | Green    |
| EW_YELLOW | Red      | Yellow   |

### Adaptive timing

When transitioning into a green phase the controller reads the vehicle sensor
for that road:

- **Sensor active** → timer is set to the **long** duration (8 clock cycles).
- **Sensor inactive** → timer is set to the **short** duration (4 clock cycles).

Yellow phases are always 2 clock cycles.

### Emergency override

When `emergency` (ui_in[2]) is asserted, the FSM is held in its reset state and
all green/yellow outputs are suppressed — both roads show **Red** and the
`emergency_led` output (uo_out[6]) is driven high. Releasing `emergency` returns
the controller to normal operation from the NS_GREEN state.

## How to test

1. Apply a clock to `clk` and hold `rst_n` low for at least one cycle to reset.
2. Release `rst_n`. The NS road will show Green and EW will show Red.
3. Toggle `ns_sensor` (ui_in[0]) and `ew_sensor` (ui_in[1]) to simulate traffic.
   Observe that phases with an active sensor last 8 cycles; phases without only 4.
4. Cycle through all four states by waiting for each phase timer to expire.
5. Assert `emergency` (ui_in[2]) at any point to verify that both roads go Red
   and the emergency LED (uo_out[6]) lights up. Release to resume normal operation.

## External hardware

- Three bi-colour (or six single-colour) LEDs connected to uo_out[5:0] to
  display the North-South and East-West traffic lights.
- One LED connected to uo_out[6] for the emergency indicator.
- Optional: PIR or IR break-beam sensors wired to ui_in[1:0] for real adaptive
  behaviour.

