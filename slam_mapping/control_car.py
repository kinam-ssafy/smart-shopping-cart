import re
import subprocess
import serial
import signal
import sys
import time

SER_PORT = "/dev/ttyACM0"   # 필요하면 /dev/ttyTHS2
BAUD = 115200

CMD = ["sudo", "xboxdrv", "--detach-kernel-driver", "--no-uinput"]

RE_X1 = re.compile(r"\bX1:\s*(-?\d+)")
RE_LT = re.compile(r"\bLT:\s*(-?\d+)")
RE_RT = re.compile(r"\bRT:\s*(-?\d+)")

def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v

def scale_signed(raw, out_max):
    return int(round(raw / 32767.0 * out_max))

def scale_trigger(raw):
    # 트리거는 대개 0..255
    if raw < -1000 or raw > 1000:
        return clamp(scale_signed(raw, 100), -100, 100)
    raw = clamp(raw, 0, 255)
    return int(round((raw / 255.0) * 200 - 100))

def send(ser, axis, val):
    msg = f"{axis}={val}\r\n"
    ser.write(msg.encode())
    return msg.strip()

def main():
    print("=== xbox_uart_debug starting ===")
    print("UART:", SER_PORT, BAUD)
    print("CMD :", " ".join(CMD))
    print()

    # UART open
    try:
        ser = serial.Serial(SER_PORT, BAUD, timeout=0.1)
    except Exception as e:
        print("[ERR] Failed to open UART:", repr(e))
        sys.exit(1)

    # xboxdrv start
    p = subprocess.Popen(
        CMD,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    def shutdown(*_):
        print("\n=== shutting down ===")
        try:
            p.terminate()
        except Exception:
            pass
        try:
            ser.close()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    last_sent = {"x": None, "z": None, "r": None}
    last_hb = time.time()

    for line in p.stdout:
        now = time.time()
        if now - last_hb >= 1.0:
            print("[HB] alive... last:", last_sent)
            last_hb = now

        line = line.rstrip("\n")
        if not line:
            continue

        # xboxdrv가 뱉는 원본 라인도 보고 싶으면 주석 해제
        # print("[RAW]", line)

        mx = RE_X1.search(line)
        mlt = RE_LT.search(line)
        mrt = RE_RT.search(line)

        # 이벤트 라인이 아니면 그냥 패스
        if not (mx or mlt or mrt):
            continue

        raw_x1 = int(mx.group(1)) if mx else None
        raw_lt = int(mlt.group(1)) if mlt else None
        raw_rt = int(mrt.group(1)) if mrt else None

        # 스케일
        if raw_x1 is not None:
            x = clamp(scale_signed(raw_x1, 37), -37, 37)
        else:
            x = None

        if raw_lt is not None:
            z_raw = clamp(scale_trigger(raw_rt), -100, 100)
            z = int(round((z_raw + 100) / 2))   # -100~100 → 0~100
        else:
            z = None

        if raw_rt is not None:
            r_raw = clamp(scale_trigger(raw_lt), -100, 100)
            r = int(round((r_raw + 100) / 2))   # -100~100 → 0~100
        else:
            r = None


        print(f"[PARSE] X1={raw_x1} -> x={x} | LT={raw_lt} -> z={z} | RT={raw_rt} -> r={r}")

        # 변경된 것만 전송
        if x is not None and last_sent["x"] != x:
            last_sent["x"] = x
            sent = send(ser, "x", x)
            print("  [SEND]", sent)

        if z is not None and last_sent["z"] != z:
            last_sent["z"] = z
            sent = send(ser, "z", z)
            print("  [SEND]", sent)

        if r is not None and last_sent["r"] != r:
            last_sent["r"] = r
            sent = send(ser, "r", r)
            print("  [SEND]", sent)

if __name__ == "__main__":
    main()