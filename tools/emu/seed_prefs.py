import json, datetime, html, subprocess, sys
ADB = r"C:\Users\wnsdu\AppData\Local\Android\Sdk\platform-tools\adb.exe"
# 사용: python tools/emu/seed_prefs.py [self|coordinator] [proof:0|1]
# 에뮬레이터(emulator-5554) 의 FlutterSharedPreferences.xml 을 run-as 로 덮어써서 역할·이름·오늘 일정·완료사진 옵션을 시드한다.
# 기기 시계가 UTC 라 일정 시각은 UTC now 기준으로 생성.  (세션 7, 2026-09-06)
ROLE = sys.argv[1] if len(sys.argv) > 1 else "self"
PROOF = (sys.argv[2] if len(sys.argv) > 2 else "0") == "1"
# 에뮬레이터 시계는 UTC → 기기 기준 시각으로 일정 생성
now = datetime.datetime.utcnow()
today = now.strftime('%Y-%m-%d')
def t(h, m): return f"{h:02d}:{m:02d}"
base = now.hour * 60 + now.minute
def hm(mins):
    mins = max(0, min(23*60+59, mins)); return t(mins // 60, mins % 60)
items = [
    {"time": hm(base - 150), "type": "MORNING_BRIEFING", "task": "아침 인사", "guide_script": ["창문 열고 기지개", "물 한 잔"]},
    {"time": hm(base - 90), "type": "MEAL", "task": "아침 먹기", "guide_script": ["식탁 정리", "밥과 국 담기", "천천히 먹기"]},
    {"time": hm(base - 20), "type": "ROUTINE", "task": "이 닦고 세수", "guide_script": ["치약 콩알만큼", "2분 닦기", "물로 헹구기"]},
    {"time": hm(base + 25), "type": "WALK", "task": "동네 한 바퀴 산책", "guide_script": ["운동화 신기", "물병 챙기기", "20분 걷기"]},
    {"time": hm(base + 120), "type": "COOKING", "task": "점심 만들기", "guide_script": ["손 씻기", "재료 꺼내기"]},
    {"time": hm(base + 240), "type": "REST", "task": "쉬는 시간", "guide_script": ["좋아하는 음악"]},
]
sched = json.dumps({"date": today, "schedule": items}, ensure_ascii=False)
xml = f"""<?xml version='1.0' encoding='utf-8' standalone='yes' ?>
<map>
    <string name="flutter.harumate_segment">dd</string>
    <string name="flutter.harumate_city">Seoul</string>
    <string name="flutter.harumate_role">{ROLE}</string>
    <boolean name="flutter.harumate_proof_photo" value="{'true' if PROOF else 'false'}" />
    <string name="flutter.harumate_user_name">준영</string>
    <string name="flutter.harumate_font_size">large</string>
    <boolean name="flutter.harumate_onboarded_v1" value="true" />
    <string name="flutter.hibuddy_latest_date">{today}</string>
    <string name="flutter.hibuddy_schedule_{today}">{html.escape(sched, quote=True)}</string>
</map>
"""
DST = "/data/user/0/com.harumate.care/shared_prefs/FlutterSharedPreferences.xml"
# 단일 문자열로 넘겨야 리다이렉션이 run-as 안쪽(sh -c)에서 해석됨
p = subprocess.run([ADB, "-s", "emulator-5554", "shell",
                    f"run-as com.harumate.care sh -c 'cat > {DST}'"], input=xml.encode('utf-8'), capture_output=True)
print("push rc", p.returncode, p.stderr.decode(errors='ignore')[:200])
chk = subprocess.run([ADB, "-s", "emulator-5554", "shell",
                     f"run-as com.harumate.care wc -c {DST}"], capture_output=True)
print(chk.stdout.decode())
print("now", hm(base), "items", [i['time'] for i in items])
