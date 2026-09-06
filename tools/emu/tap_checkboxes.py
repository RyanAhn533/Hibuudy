"""uiautomator dump 으로 체크박스 bounds 를 찾아 중앙을 탭 (스크롤 위치 무관)."""
import re, subprocess, sys, time
ADB = r"C:\Users\wnsdu\AppData\Local\Android\Sdk\platform-tools\adb.exe"
def sh(*a, **k):
    return subprocess.run([ADB, "-s", "emulator-5554", *a], capture_output=True, **k)
def dump():
    sh("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    xml = sh("exec-out", "cat", "/sdcard/ui.xml").stdout.decode("utf-8", "ignore")
    return xml
def boxes(xml):
    out = []
    for m in re.finditer(r'<node[^>]*checkable="true"[^>]*bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', xml):
        x1, y1, x2, y2 = map(int, m.groups())
        if y2 - y1 < 20: continue
        out.append(((x1 + x2) // 2, (y1 + y2) // 2))
    return out
xml = dump()
b = boxes(xml)
print("checkboxes:", b)
for i, (x, y) in enumerate(b[:3]):
    sh("shell", "input", "tap", str(x), str(y)); time.sleep(1.5)
    print("tapped", i + 1, (x, y))
