"""
Core app cho AI Academic Advisor.

Chay baseline chatbot va ReAct agent tren bo test case offline. Neu khong co API
key, MockProvider van tao trace deterministic de demo duoc tu dau den cuoi.
"""

import ast
import json
import os
import re
import sys

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from prompts import CHATBOT_BASELINE_PROMPT, MAX_ITERATIONS, REACT_SYSTEM_PROMPT
from providers import get_llm_provider
from tools import AVAILABLE_TOOLS

load_dotenv()

ACTION_RE = re.compile(r"Action:\s*([a-zA-Z_][a-zA-Z0-9_]*)\[(.*)\]", re.DOTALL)
FINAL_RE = re.compile(r"Final Answer:\s*(.*)", re.DOTALL)


def load_test_cases():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(base_dir, "config", "test_cases.json"), encoding="utf-8") as f:
        return json.load(f)


def parse_action(response):
    match = ACTION_RE.search(response)
    if not match:
        return None, []

    raw_args = match.group(2).strip()
    if not raw_args:
        return match.group(1), []
    try:
        args = ast.literal_eval(f"[{raw_args}]")
    except (SyntaxError, ValueError):
        args = [part.strip().strip("'\"") for part in raw_args.split(",")]
    return match.group(1), [str(arg) for arg in args]


def run_tool(name, args):
    tool = AVAILABLE_TOOLS.get(name)
    if not tool:
        return json.dumps({"ok": False, "error": f"LOI: Tool {name} khong ton tai."}, ensure_ascii=False)
    try:
        return tool(*args)
    except TypeError as exc:
        return json.dumps({"ok": False, "error": f"LOI: Sai tham so cho {name}: {exc}"}, ensure_ascii=False)


def run_baseline_chatbot(user_query, provider):
    print(f"\n[BASELINE] {user_query}")
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(response)
    return response


def run_react_agent(user_query, provider):
    print(f"\n[REACT AGENT] {user_query}")
    scratchpad = ""

    for step in range(1, MAX_ITERATIONS + 1):
        prompt = (
            f"Câu hỏi người dùng: {user_query}\n\n"
            f"Trace hiện tại:\n{scratchpad or '(chưa có)'}\n\n"
            "Hãy trả về bước tiếp theo đúng format."
        )
        response = provider.generate(prompt, system_prompt=REACT_SYSTEM_PROMPT).strip()
        print(f"\n-- Step {step}/{MAX_ITERATIONS} --")
        print(response)

        final = FINAL_RE.search(response)
        if final:
            return final.group(1).strip()

        tool_name, args = parse_action(response)
        if not tool_name:
            print("Guardrail: Không tìm thấy Action hoặc Final Answer hợp lệ.")
            return response

        observation = run_tool(tool_name, args)
        print(f"Observation: {observation}")
        scratchpad += f"{response}\nObservation: {observation}\n\n"

    message = f"Guardrail: Đã đạt MAX_ITERATIONS={MAX_ITERATIONS}. Cần cố vấn kiểm tra thủ công."
    print(message)
    return message


def main():
    print("=" * 72)
    print("AI ACADEMIC ADVISOR - Chatbot Baseline vs ReAct Agent")
    print("=" * 72)

    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "offline-mock")
    print(f"Provider: {provider.__class__.__name__} ({model_name})")

    tests = load_test_cases()
    print(f"Loaded {len(tests)} test cases\n")

    for test in tests:
        print("\n" + "=" * 72)
        print(f"TEST #{test['id']} - {test['category']}")
        run_baseline_chatbot(test["question"], provider)
        run_react_agent(test["question"], provider)


if __name__ == "__main__":
    main()
