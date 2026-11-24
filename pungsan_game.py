import random
import ipywidgets as widgets
from IPython.display import display

# ----- 1. 게임 설정 -------
STATS = ["지능", "체력", "사회성", "명성"]
DECAY = 3                     # 매 턴이 끝나면 모든 능력치가 3씩 줄어든다
DANGER = 25                   # 지능·체력·사회성이 25 미만으로 2턴 연속이면 전학
LAST_TURN = 15                # 15턴을 마치면 졸업
EXAM_TURNS = [3, 6, 9, 12, 15]    # 시험 보는 턴
ACTIVITIES = {# 활동 이름: 능력치 변화
    "자습": {"지능": 10, "체력": -3},
    "체단실": {"체력": 10, "지능": -2},
    "장기자랑": {"사회성": 8, "명성": 8},
    "무단외출": {"사회성": 15, "명성": 15},}
OUTING_SUCCESS = 85           # 무단외출 성공 확률(%)

# ------ 2. 게임 규칙 함수 ------
def new_game(focus):   # 새 게임 만들기 (집중 능력치 60, 나머지 50)
    stats = {"지능": 50, "체력": 50, "사회성": 50, "명성": 50}
    stats[focus] = 60
    return {"턴": 1, "능력치": stats, "위험": {"지능": 0, "체력": 0, "사회성": 0}, "시험": [], "결과": "진행중"}

def change(game, effects):   # 능력치 바꾸기 (0~100 유지)
    for stat in effects:
        game["능력치"][stat] = game["능력치"][stat] + effects[stat]
        if game["능력치"][stat] > 100:
            game["능력치"][stat] = 100
        if game["능력치"][stat] < 0:
            game["능력치"][stat] = 0

def do_activity(game, name):   # 활동하기 (무단외출은 15% 퇴학)
    if name == "무단외출" and random.randint(1, 100) > OUTING_SUCCESS:
        game["결과"] = "퇴학"
        return "🚨 무단외출이 사감 선생님께 걸렸다!"
    change(game, ACTIVITIES[name])
    return "✅ " + name + " 성공!"

def take_exam(game):   # 시험: 지능 + 운 → 1~5등급
    score = game["능력치"]["지능"] + random.randint(-10, 10)
    if score >= 80:
        grade = 1
    elif score >= 65:
        grade = 2
    elif score >= 50:
        grade = 3
    elif score >= 35:
        grade = 4
    else:
        grade = 5
    game["시험"].append(grade)
    return grade

def end_turn(game):   # 턴 끝: 감소 → 전학 판정 → 졸업/다음 턴
    for stat in STATS:
        change(game, {stat: -DECAY})
    for stat in game["위험"]:
        if game["능력치"][stat] < DANGER:
            game["위험"][stat] = game["위험"][stat] + 1
        else:
            game["위험"][stat] = 0
        if game["위험"][stat] >= 2:
            game["결과"] = "전학"
    if game["결과"] == "진행중":
        if game["턴"] == LAST_TURN:
            game["결과"] = "졸업"
        else:
            game["턴"] = game["턴"] + 1

def ending(game):   # 졸업 엔딩 정하기
    s = game["능력치"]
    average = sum(game["시험"]) / len(game["시험"])
    if s["지능"] >= 70 and average <= 2.5:
        return "📚 명문대 진학 엔딩: 뛰어난 성적으로 원하던 대학에 갔다!"
    elif s["체력"] >= 70:
        return "🏋️ 체육계 진출 엔딩: 체단실에서 다진 체력으로 운동선수가 되었다!"
    elif s["명성"] >= 70:
        return "⭐ 풍산고 스타 엔딩: 모두가 이름을 아는 유명한 졸업생이 되었다!"
    else:
        return "🎓 평범한 졸업 엔딩: 특별하진 않아도 무사히 3년을 마쳤다."

# ------- 3. 화면 (ipywidgets) -------
info = widgets.Label()        # 현재 턴
out = widgets.Output()        # 결과 글이 나오는 칸
box = widgets.VBox()          # 버튼이 들어가는 칸
bars = {}                     # 능력치 게이지 4개
for stat in STATS:
    bars[stat] = widgets.IntProgress(min=0, max=100, description=stat)
now = {"game": None}          # 지금 진행 중인 게임을 담아 두는 곳

def say(text):   # 결과 칸에 글 출력
    with out:
        print(text)

def show_buttons(names, handler):   # 버튼 만들기 (누르면 handler 실행)
    buttons = []
    for name in names:
        b = widgets.Button(description=name)
        b.on_click(handler)
        buttons.append(b)
    box.children = buttons

def is_valid(b):   # 지금 화면의 버튼인지 확인 (중복 클릭 방지)
    if b in box.children:
        box.children = []
        return True
    return False

def show_status():   # 턴과 능력치 게이지 갱신
    g = now["game"]
    info.value = f"{g['턴']}/15턴"
    for stat in STATS:
        bars[stat].value = g["능력치"][stat]
        bars[stat].description = stat + " " + str(g["능력치"][stat])

def show_title(b=None):   # 입학 화면 (집중 능력치 고르기)
    out.clear_output()
    say("🏫 풍산고에서 졸업하기! 15턴을 버티면 졸업한다.\n지능·체력·사회성이 25 미만으로 2턴 연속이면 전학.\n집중할 능력치를 골라 입학하자! (그 능력치는 60, 나머지는 50으로 시작)")
    show_buttons(STATS, on_start)

def on_start(b):   # 입학 버튼 → 새 게임 시작
    if is_valid(b):
        now["game"] = new_game(b.description)
        out.clear_output()
        start_turn()

def start_turn():   # 턴 시작 → 활동 버튼
    show_status()
    say(f"\n📅 {now['game']['턴']}턴 시작! 무엇을 할까?")
    say("자습: 지능+10 체력-3 / 체단실: 체력+10 지능-2 / 장기자랑: 사회성+8 명성+8\n무단외출: 사회성+15 명성+15, 하지만 15% 확률로 퇴학!")
    show_buttons(list(ACTIVITIES), on_activity)

def on_activity(b):   # 활동 → 시험 → 턴 끝
    if is_valid(b):
        g = now["game"]
        say(do_activity(g, b.description))
        if g["결과"] == "진행중":
            if g["턴"] in EXAM_TURNS:
                say(f"📋 시험 결과: {take_exam(g)}등급")
            end_turn(g)
        show_status()
        for stat in g["위험"]:
            if g["위험"][stat] == 1:
                say(f"⚠️ {stat}이(가) 25 미만! 다음 턴에도 낮으면 전학이다.")
        if g["결과"] == "진행중":
            show_buttons(["다음 턴"], on_next)
        else:
            show_buttons(["결과 보기"], on_result)

def on_next(b):   # 다음 턴 버튼
    if is_valid(b):
        start_turn()

def on_result(b):   # 졸업 엔딩 또는 게임 오버
    if is_valid(b):
        g = now["game"]
        out.clear_output()
        if g["결과"] == "졸업":
            say("🎓 졸업 성공! " + ending(g))
        else:
            say(f"💀 게임 오버: {g['결과']} ({g['턴']}턴)")
        for stat in STATS:
            say(f"  {stat}: {g['능력치'][stat]}")
        show_buttons(["다시 하기"], show_title)

display(widgets.VBox([info] + list(bars.values()) + [out, box]))
show_title()
