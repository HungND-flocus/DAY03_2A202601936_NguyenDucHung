"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
try:
    import requests
except ModuleNotFoundError:
    requests = None
try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv():
        return False

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        if requests is None:
            return "[OpenRouter Error]: Chưa cài thư viện requests!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()
        system = system_prompt.lower()
        if "chatbot tư vấn" in system:
            return (
                "Tôi có thể tư vấn nguyên tắc chung, nhưng để kết luận chính xác về "
                "môn học, tiên quyết, tín chỉ hoặc trạng thái duyệt thì cần Academic "
                "Advisor kiểm tra dữ liệu học vụ bằng tool/backend."
            )

        if "observation:" in text:
            return self._final_from_observation(prompt)

        if "magic999" in text:
            return 'Thought: Cần kiểm tra môn MAGIC999 có trong danh mục học vụ không.\nAction: search_courses["MAGIC999"]'
        if "cs201" in text and "đủ điều kiện" in text:
            return 'Thought: Cần kiểm tra tiên quyết của CS201 trên danh sách môn đã hoàn thành.\nAction: check_prerequisites["CS201", "CS101,MATH101"]'
        if "cs201, ds201" in text or "workload" in text or "quá nặng" in text:
            return 'Thought: Cần tính tổng tín chỉ của danh sách môn dự kiến.\nAction: estimate_workload["CS201,DS201,AI301"]'
        if "what-if" in text or "đổi số tín" in text or "12 tín" in text:
            return 'Thought: Cần mô phỏng kịch bản mới mà không ghi đè kế hoạch gốc.\nAction: simulate_what_if["S001", "12", "Data Science"]'
        if "nợ môn" in text or "bù học phần" in text or "rớt" in text:
            return 'Thought: Cần sinh kế hoạch bắt kịp tiến độ cho sinh viên đang nợ môn.\nAction: generate_study_plan["S002", "catch_up", "Software", "9"]'
        if "năm cuối" in text or "ra trường đúng hạn" in text:
            return 'Thought: Cần sinh kế hoạch ưu tiên tốt nghiệp đúng hạn cho sinh viên năm cuối.\nAction: generate_study_plan["S003", "graduate_on_time", "AI", "12"]'
        if "gửi kế hoạch" in text or "gửi cho cố vấn" in text:
            return 'Thought: Cần chuyển kế hoạch nháp sang trạng thái chờ cố vấn duyệt.\nAction: submit_plan["PLAN-S001-001", "S001"]'
        if "duyệt" in text or "advisor" in text or "cố vấn" in text:
            return 'Thought: Cần kiểm tra quyền cố vấn và duyệt kế hoạch đang chờ.\nAction: review_plan["PLAN-S001-001", "ADV01", "approve"]'
        if "tư vấn giúp em chọn môn" in text:
            return "Thought: Câu hỏi thiếu hồ sơ sinh viên, môn đã học, mục tiêu và giới hạn tín chỉ.\nFinal Answer: Em cho mình biết mã sinh viên, các môn đã hoàn thành, mục tiêu học kỳ tới và số tín chỉ tối đa nhé."
        if "gpa 3.2" in text or "data science" in text or "tối đa 9" in text:
            return 'Thought: Cần sinh kế hoạch bằng planner đã kiểm tra tiên quyết và giới hạn tín chỉ.\nAction: generate_study_plan["S001", "balanced", "Data Science", "9"]'

        return "Thought: Câu hỏi mang tính kiến thức chung, không cần tool.\nFinal Answer: Em nên bắt đầu từ lập trình, toán nền tảng, xác suất thống kê và kỹ năng đọc tài liệu học thuật."

    def _final_from_observation(self, prompt: str) -> str:
        observation = prompt.rsplit("Observation:", 1)[1].strip()
        try:
            data, _ = json.JSONDecoder().raw_decode(observation)
        except Exception:
            return "Thought: Observation không đọc được rõ ràng.\nFinal Answer: Mình cần cố vấn kiểm tra lại dữ liệu trước khi kết luận."

        if not data.get("ok"):
            return f"Thought: Tool trả về lỗi nên không được bịa kết quả.\nFinal Answer: {data.get('error', 'Không đủ dữ liệu để tư vấn.')} Mình không thể thêm môn/kế hoạch này khi dữ liệu học vụ chưa hợp lệ."

        if "terms" in data:
            term_lines = []
            for term in data["terms"]:
                courses = ", ".join(course["id"] for course in term["courses"]) or "chưa xếp môn"
                label = term.get("label") or term.get("term") or term.get("season", "Kỳ học")
                term_lines.append(f"{label}: {courses} ({term['credits']} tín chỉ)")
            alerts = " ".join(data.get("alerts") or ["Không có cảnh báo lớn."])
            return (
                "Thought: Planner đã trả về kế hoạch đã kiểm tra tiên quyết và tín chỉ.\n"
                "Final Answer: Kế hoạch đề xuất đang ở trạng thái "
                f"{data['status']} ({data['plan_id']}): " + "; ".join(term_lines) + f". Cảnh báo: {alerts}"
            )

        if "eligible" in data:
            if data["eligible"]:
                answer = f"Em đủ điều kiện đăng ký {data['course_id']} - {data['course_name']}."
            else:
                answer = f"Em chưa đủ điều kiện đăng ký {data['course_id']}; còn thiếu {', '.join(data['missing_prerequisites'])}."
            return f"Thought: Đã kiểm tra tiên quyết từ tool.\nFinal Answer: {answer}"

        if "total_credits" in data:
            warning = f" {data['warning']}" if data.get("warning") else ""
            return (
                "Thought: Đã tính workload từ danh sách môn.\n"
                f"Final Answer: Tổng cộng {data['total_credits']} tín chỉ, mức {data['workload_level']}.{warning}"
            )

        if "status" in data:
            return f"Thought: Đã cập nhật trạng thái kế hoạch qua tool.\nFinal Answer: {data.get('message', 'Trạng thái mới')}: {data['status']}."

        if "courses" in data:
            courses = ", ".join(f"{course['id']} - {course['name']}" for course in data["courses"])
            return f"Thought: Đã tìm được môn trong danh mục học vụ.\nFinal Answer: Các môn phù hợp: {courses}."

        return "Thought: Đã có dữ liệu tool.\nFinal Answer: Mình đã kiểm tra dữ liệu học vụ và có thể tư vấn dựa trên kết quả này."


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
