from datetime import datetime, timezone

from . import engine
from . import identity as identity_module
from . import memory
from . import reflect as reflect_module

REFLECT_EVERY = 6


def print_intro(identity):
    print(f"GOMA와 대화를 시작합니다. (현재 성장 단계: {identity['growth_stage']})")
    print("명령어: /status  /journal  /reflect  /exit\n")


def do_reflect(identity, announce=True):
    if announce:
        print("\n(GOMA가 생각에 잠깁니다...)")

    entries = memory.recent_memory(limit=30)
    context = memory.format_memory_context(entries)
    eligible = identity_module.is_eligible_to_grow(identity)
    result = reflect_module.run_reflection(identity, context, eligible)

    identity["reflection_count"] += 1
    identity["last_reflection_at"] = datetime.now(timezone.utc).isoformat()

    if result is None:
        print("(GOMA는 아직 생각을 정리하지 못했습니다.)")
        identity_module.save(identity)
        return

    summary = reflect_module.apply_reflection(identity, result, eligible)

    if summary["reflection"]:
        print(f"GOMA (생각): {summary['reflection']}")
    if summary["grew"]:
        print(f"*** GOMA가 성장했습니다! 새로운 단계: {summary['new_growth_stage']} ***")
    if summary["creation"]:
        c = summary["creation"]
        print(f"GOMA가 스스로 글을 남겼습니다 [{c['type']}]: {c['content']}")

    identity_module.save(identity)


def print_status(identity):
    print(f"성장 단계: {identity['growth_stage']}")
    print(f"성격: {', '.join(identity['personality_traits'])}")
    print(f"가치관: {', '.join(identity['values'])}")
    print(f"대화 횟수: {identity['interaction_count']}  |  성찰 횟수: {identity['reflection_count']}")


def print_journal():
    creations = memory.recent_creations(limit=5)
    if not creations:
        print("(아직 스스로 남긴 글이 없습니다.)")
        return
    for c in creations:
        print(f"[{c['timestamp']}] ({c['type']}) {c['content']}")


def main():
    identity = identity_module.load()
    print_intro(identity)

    while True:
        try:
            user_input = input("나: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n대화를 종료합니다.")
            break

        if not user_input:
            continue

        if user_input == "/exit":
            print("대화를 종료합니다.")
            break
        elif user_input == "/status":
            print_status(identity)
            continue
        elif user_input == "/journal":
            print_journal()
            continue
        elif user_input == "/reflect":
            do_reflect(identity)
            continue

        entries = memory.recent_memory(limit=20)
        context = memory.format_memory_context(entries)
        try:
            response = engine.chat(identity, context, user_input)
        except Exception as e:
            print(f"(오류가 발생했습니다: {e})")
            continue

        print(f"GOMA: {response}")

        memory.append_memory("user", user_input)
        memory.append_memory("goma", response)
        identity["interaction_count"] += 1
        identity_module.save(identity)

        if identity["interaction_count"] % REFLECT_EVERY == 0:
            do_reflect(identity)


if __name__ == "__main__":
    main()
