# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


# ── helpers ────────────────────────────────────────────────────────────────────

def decode_lights(uo_out):
    """Return (ns_red, ns_yellow, ns_green, ew_red, ew_yellow, ew_green, emerg)."""
    v = int(uo_out)
    return (
        bool(v & (1 << 0)),  # ns_red
        bool(v & (1 << 1)),  # ns_yellow
        bool(v & (1 << 2)),  # ns_green
        bool(v & (1 << 3)),  # ew_red
        bool(v & (1 << 4)),  # ew_yellow
        bool(v & (1 << 5)),  # ew_green
        bool(v & (1 << 6)),  # emergency_led
    )


# ── tests ──────────────────────────────────────────────────────────────────────

@cocotb.test()
async def test_reset_state(dut):
    """After reset the controller must be in NS_GREEN: NS=Green, EW=Red."""
    dut._log.info("test_reset_state")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.ui_in.value  = 0   # no sensors, no emergency
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 1)

    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, emerg = decode_lights(dut.uo_out)
    assert ns_g,       "NS should be Green after reset"
    assert ew_r,       "EW should be Red after reset"
    assert not ns_r,   "NS Red should be off"
    assert not ns_y,   "NS Yellow should be off"
    assert not ew_y,   "EW Yellow should be off"
    assert not ew_g,   "EW Green should be off"
    assert not emerg,  "Emergency LED should be off"


@cocotb.test()
async def test_emergency_override(dut):
    """Asserting emergency must force both roads Red and light the emergency LED."""
    dut._log.info("test_emergency_override")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 2)

    # Assert emergency (bit 2)
    dut.ui_in.value = 0b00000100
    await ClockCycles(dut.clk, 3)

    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, emerg = decode_lights(dut.uo_out)
    assert emerg,     "Emergency LED must be ON"
    assert ns_r,      "NS must be Red during emergency"
    assert ew_r,      "EW must be Red during emergency"
    assert not ns_g,  "NS Green must be OFF during emergency"
    assert not ew_g,  "EW Green must be OFF during emergency"


@cocotb.test()
async def test_phase_sequence(dut):
    """Verify the full NS_GREEN → NS_YELLOW → EW_GREEN → EW_YELLOW cycle."""
    dut._log.info("test_phase_sequence")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.uio_in.value = 0
    dut.ui_in.value  = 0   # no traffic sensors active
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1
    await ClockCycles(dut.clk, 1)

    # ── NS_GREEN phase (timer starts at GREEN_LONG=8) ─────────────────────────
    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ns_g and ew_r, "Expected NS_GREEN phase after reset"

    # Timer counts 7→0 in 8 cycles; transition to NS_YELLOW on the 9th cycle.
    await ClockCycles(dut.clk, 8)

    # ── NS_YELLOW phase (timer=2) ─────────────────────────────────────────────
    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ns_y and ew_r, "Expected NS_YELLOW phase"

    # Timer counts 1→0 in 2 cycles; transition to EW_GREEN on the 3rd cycle.
    await ClockCycles(dut.clk, 3)

    # ── EW_GREEN phase (timer=GREEN_SHORT=4, ew_sensor=0) ────────────────────
    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ew_g and ns_r, "Expected EW_GREEN phase"

    # Timer counts 3→0 in 4 cycles; transition to EW_YELLOW on the 5th cycle.
    await ClockCycles(dut.clk, 5)

    # ── EW_YELLOW phase (timer=2) ─────────────────────────────────────────────
    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ew_y and ns_r, "Expected EW_YELLOW phase"


@cocotb.test()
async def test_adaptive_long_green(dut):
    """EW traffic sensor causes long EW green (8 cycles) instead of short (4)."""
    dut._log.info("test_adaptive_long_green")

    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    dut.ena.value    = 1
    dut.uio_in.value = 0
    dut.rst_n.value  = 0
    await ClockCycles(dut.clk, 5)
    dut.rst_n.value  = 1

    # Keep ew_sensor=1 so when we enter EW_GREEN the timer is GREEN_LONG=8
    dut.ui_in.value = 0b00000010   # ew_sensor=1

    await ClockCycles(dut.clk, 1)   # +1: NS_GREEN, timer=7

    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ns_g, "Should start in NS_GREEN"

    # Skip through NS_GREEN (8 cycles remaining) + NS_YELLOW (3 cycles including
    # transition) = 11 more cycles to land on the first cycle of EW_GREEN.
    await ClockCycles(dut.clk, 11)  # +12 total: EW_GREEN, timer=8

    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ew_g, "Should be in EW_GREEN"

    # With GREEN_LONG=8, the timer counts 7→0 over 8 more cycles.
    # EW_GREEN must still be active at the end of those 8 cycles
    # (transition to EW_YELLOW only happens on the following cycle).
    await ClockCycles(dut.clk, 8)   # timer now=0, still EW_GREEN

    ns_r, ns_y, ns_g, ew_r, ew_y, ew_g, _ = decode_lights(dut.uo_out)
    assert ew_g, "EW_GREEN should still be active (long timer due to ew_sensor=1)"
