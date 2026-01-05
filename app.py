import streamlit as st
import json
import pandas as pd
import google.generativeai as genai
import os
import html  # ⬅️ لإصلاح عرض النص في سجل الحوار

# ========= 0. GEMINI CONFIG =========
# يفضل استخدام مفتاح في متغير بيئة، لكن للإسراع يمكنك وضعه هنا مباشرة
# تأكد من تحديث هذا المفتاح بمفتاحك الخاص
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBAroU6DPfzAUPYUwuwjKz9gH7RdpvfzSI")

# ========= 0.1 COMPANY PROCESS (سياسة SEOUDI للجودة) =========
# ملخص من E-Commerce Policies & Procedures Manual لكل القنوات
COMPANY_PROCESS = """
سياسات وإجراءات الجودة الخاصة بـ SEOUDI (ملخّص من E-Commerce Policies & Procedures Manual):

أولاً: SEOUDI Application | Live Chat
- Greeting (NC, 5%):
  * لازم الترحيب الموحد خلال الزمن المتفق عليه.
  * تعريف النفس واسم SEOUDI بوضوح.
- Interaction and Professionalism (NC, 5%):
  * التركيز الكامل، الرد على نفس طلب/شكوى العميل.
  * إظهار التعاطف فورًا بعد شكوى العميل.
  * تجنُّب الـ slang غير المهني، مع مراعاة Language Barrier (أخطاء بسيطة لا تؤثر على الفهم = NC).
  * تجنُّب مقاطعة العميل أو إظهار لا مبالاة.
- Hold & Controlling Transaction (NC, 5%):
  * طلب الإذن بالـ hold، توضيح السبب، تحديد المدة، وشكر العميل عند الرجوع.
  * تجنّب تكرار الـ hold مرات كثيرة بلا داعي.
- Control Chat Length (NC, 5%):
  * تجنُّب الصمت 30 ثانية – 1 دقيقة بدون سبب.
  * إنهاء الشات في الوقت الصحيح لو العميل صامت بعد الـ closure script.
- Closing (NC, 5%):
  * استخدام نص الإغلاق الموحد:
    "أي خدمة أو إستفسار أخر لحضرتك؟ شكرا لإختيارك سعودي سوبر ماركت"
- Company Policy (CTB, 10%):
  * عدم لوم الشركة أو السيستم أو الأقسام الأخرى.
  * عدم إعطاء انطباع سلبي عن SEOUDI أو التطبيق.
- Business Reporting / Documentation (CTB, 10%):
  * إنشاء الـ ticket الصحيح وعدم إهمال التسجيل.
- Internal Process / Control Chat Length – Process (CTB, 10%):
  * الالتزام بزمن إرسال الـ closure script وإغلاق الشات وفق العملية.
- Information (CTC, 25%):
  * تقديم معلومات/حلول كاملة وصحيحة طبقًا للـ KB.
  * عدم ترك أي استفسار بدون رد، وعدم تحويل العميل لقنوات أخرى لو ممكن خدمته بنفس المعاملة.
- Language Barrier or incorrect spelling – مؤثر (CTC, 25%):
  * خطأ لغوي يغيّر المعنى أو يتحوّل لشتيمة أو يسبب عدم فهم.
- Wrong Action (CTC, 25%):
  * تنفيذ إجراء خاطئ يؤثر سلبًا على العميل (غلط في Order ID, Mail, Contact Number, Case Status...).
- Missing Action (CTC, 25%):
  * عدم تنفيذ الإجراء الواجب طبقًا للبروسيس (عدم إنشاء case، عدم إرسال للـ team المختص…).
- Time Management (CTC, 25%):
  * تأخير الرد الأول، hold طويل جدًا، silence طويل بدون سبب.
- Handling Skills (CTC, 25%):
  * مقاطعة متكررة، لا مبالاة، عدم تحمل مسؤولية، مجادلة العميل، gender mistake، إلخ.
- Customer Mistreat (CTC, 25%):
  * غلق الشات/المكالمة بدون حل، لهجة/كلمات غير لائقة، سخرية، رفض تصعيد صحيح.
- Wrong Item / Missing Item / Lack of Follow up (CTC, 25%):
  * إضافة صنف خطأ، عدم إضافة الصنف المطلوب، عدم المتابعة أو تأخيرها بعد الوعد.

ثانيًا: Social Media Quality Manual
- Late Response (CTC, 25%):
  * الرد الأول خلال 30 دقيقة في أوقات العمل (9 ص – 1 ص).
- Information (CTC, 25%):
  * نفس مبدأ المعلومات الدقيقة والكاملة.
- Language Barrier or incorrect spelling (CTC, 25%):
  * لو أثّر على الفهم أو رضا العميل.
- Wrong Action / Missing Action (CTC, 25%):
  * تيكيت غلط، عدم إنشاء تيكيت، إلخ.
- Handling Skills (CTC, 25%):
  * مرونة، ملكشية، gender mistake، عدم إظهار رغبة للمساعدة.
- Lack of Follow up (CTC, 25%):
  * عدم الرد على posts/DMs أو عدم الاتصال بعد حل الشكوى.
- Business Reporting / Documentation (CTB, 10%):
  * توثيق ناقص أو خاطئ لا يضر العميل مباشرة.
- Company Policy (CTB, 10%):
  * نفس قواعد الصورة الإيجابية للشركة.

ثالثًا: Outbound Calls
- Outbound Greeting / Closing (NC, 5%):
  * نص محدد للافتتاح والإغلاق.
- Hold / Transfer / Control call length / Interaction (NC, 5% لكل بند):
  * ضبط وقت المكالمة، عدم طرح أسئلة لا تفيد، ترحيب واستخدام اسم العميل، إلخ.
- Company Policy, Business Reporting, Internal Process (CTB, 10%):
  * اتباع السياسة والعمليات وعدم الإضرار بصورة الشركة.
- Information, Wrong Item, Wrong Action, Missing Item, Missing Action, Lack of Follow up,
  Time Management, Handling Skills, Customer Mistreat (CTC, 25%):
  * نفس معايير التأثير المباشر على العميل وعلى طلبه.

رابعًا: Inbound Voice & WhatsApp
- Greeting, Hold, Transfer Call, Control call length, Interaction, Closing (NC).
- Company Policy, Business Reporting, Internal Process (CTB).
- Information، Wrong Item، Wrong Action، Missing Item، Missing Action،
  Lack of Follow up، Time Management، Handling Skills، Customer Mistreat،
  Slang Language، Tone Of Voice، Interaction With the Customer (CTC, 25%).

استخدم هذه السياسة لتصنيف كل خطأ في أداء الموظف حسب:
- item: البند (مثال: "Greeting", "Information", "Time Management", "Handling Skills", "Customer Mistreat"...)
- type: نوع الخطأ ("NC", "CTB", "CTC")
مع شرح عملي في الوصف.
"""

# ========= 1. CONFIGURATION AND STYLING =========
st.set_page_config(
    page_title="لوحة تحليل جودة المكالمات",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_custom_style():
    st.markdown(
        """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');

        div.stApp {
            direction: rtl;
            background: #f3f4f6;
        }
        html, body, [class*="st-"] {
            font-family: 'Inter', 'Tahoma', 'Arial', sans-serif;
        }
        h1, h2, h3 {
            color: #1e293b;
        }
        .stCard {
            border-radius: 14px;
            box-shadow: 0 4px 8px rgba(15, 23, 42, 0.06);
            border: 1px solid #e5e7eb;
            background: #ffffff;
        }
        .metric-card {
            transition: transform 0.15s ease, box-shadow 0.15s ease;
            cursor: default;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 18px rgba(15, 23, 42, 0.12);
        }
        .app-header {
            background: linear-gradient(120deg, #0ea5e9, #6366f1);
            color: white;
            padding: 18px 24px;
            border-radius: 18px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.25);
            margin-bottom: 1.5rem;
        }
        .app-header h1 {
            font-size: 30px;
            margin: 0;
        }
        .app-header p {
            margin: 4px 0 0 0;
            font-size: 13px;
            opacity: 0.9;
        }
        .transcript-wrapper {
            max-height: 520px;
            overflow-y: auto;
            padding: 12px 8px;
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            background: #f9fafb;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


apply_custom_style()

# ===== Header / Title =====
st.markdown(
    """
    <div class="app-header">
        <div style="display:flex; align-items:center; justify-content:space-between; gap:16px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="font-size:34px;">🤖📞</div>
                <div>
                    <h1>Call Quality AI Analytics</h1>
                    <p>لوحة ذكية لتحليل جودة مكالمات خدمة عملاء Seoudi</p>
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ========= 2. DEFAULT DATA (للاختبار) =========
DEFAULT_DATA = {
    "metadata": {
        "id": "#99283-DXB",
        "agent": "سارة م.",
        "duration": "04:12",
        "updatedBy": "Local System",
        "updatedAt": "10:30 ص",
    },
    "transcript": [
        {
            "time": "00:08",
            "speaker": "customer",
            "text": "لو سمحتي أنا طالب أوردر من ساعتين ولسه ماوصلش، والأبلكيشن مكتوب إنه تم التوصيل!",
        },
        {
            "time": "00:20",
            "speaker": "customer",
            "text": "أيوه يا أستاذة متأكد طبعاً! هو أنا هتبلى عليكم؟ أنا واقف قدام الباب ومفيش حاجة.",
        },
        {
            "time": "00:34",
            "speaker": "customer",
            "text": "يا بنتي اسمعيني! أنا مش بكلم السيستم أنا بكلم بني آدمة. شوفي حل للموضوع ده فوراً.",
        },
        {
            "time": "01:25",
            "speaker": "agent",
            "text": "يا فندم ما هو جي في الطريق خلاص، مفيش تعويض للتأخير البسيط ده.",
        },
        {
            "time": "02:05",
            "speaker": "agent",
            "text": "تمام يا فندم، هعمل request لـ Delivery Team يكلموك.",
        },
        {
            "time": "02:45",
            "speaker": "customer",
            "text": "طيب ماشي... سلام.",
        },
    ],
    "analysis": {
        "customer_sentiment": "Negative",
        "agent_attitude": "دفاعية ومش متعاونة كفاية، وبتقاطع العميل.",
        "churn_risk": "High",
        "main_issue_category": "تأخير توصيل / سلوك موظف",
        "summary": "العميل بيشتكي إن الأوردر اتأخر واتكتب له تم التوصيل. الموظفة قللت من المشكلة ورفضت التعويض بطريقة غير لائقة.",
    },
    "agent_issues": [
        {
            "time": "00:20",
            "item": "Interaction and Professionalism",
            "type": "NC",
            "description": "تشكيك في كلام العميل ونبرة دفاعية بدلاً من التعاطف.",
        },
        {
            "time": "00:34",
            "item": "Handling Skills",
            "type": "CTC",
            "description": "مقاطعة العميل أكثر من مرة وعدم إظهار أي صبر أو مرونة في الحوار.",
        },
        {
            "time": "01:25",
            "item": "Information",
            "type": "CTC",
            "description": "رفض أي تعويض أو حل مناسب رغم تأخير حقيقي في التوصيل، بالمخالفة لروح سياسة خدمة العملاء.",
        },
    ],
    "quality_scores": {
        "greeting": {"score": 9, "comment": "بداية ممتازة."},
        "empathy": {"score": 2, "comment": "ضعف شديد في التعاطف."},
        "listening": {"score": 3, "comment": "قاطعت العميل أكتر من مرة."},
        "problem_solving": {"score": 5, "comment": "فشلت في احتواء غضب العميل."},
        "closing": {"score": 4, "comment": "العميل قفل وهو متضايق جداً."},
        "overall_score": {"score": 45, "comment": "مكالمة سيئة."},
    },
    "corrective_actions": [
        "تدريب فوري على مهارات الامتصاص والتعاطف.",
        "مراجعة سياسة التعويضات وشرحها للموظفة.",
        "مراجعة إجراءات إنهاء المكالمات.",
    ],
}

# ========= 3. SESSION STATE =========
if "report_data" not in st.session_state:
    st.session_state.report_data = DEFAULT_DATA


# ========= 4. GEMINI AUDIO → REPORT =========
def analyze_audio_to_report(audio_bytes: bytes, mime_type: str):
    """
    يرسل ملف الصوت لـ Gemini ويرجع تقرير بنفس الـ structure المستخدم في الواجهة.
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("من فضلك حدّث المتغير GEMINI_API_KEY في الكود بمفتاح صحيح.")

    genai.configure(api_key=GEMINI_API_KEY)

    model = genai.GenerativeModel("gemini-2.5-flash")

    prompt = """
أنت خبير لغوي ومحلل جودة مكالمات (QA Analyst) في بيئة خدمة عملاء "سوبر ماركت سعودي".
مهمتك هي الاستماع للملف الصوتي وتفريغه بدقة عالية ثم تحليله.

### أولاً: تعليمات التفريغ النصي (Transcript Rules) - مهم جداً:
1. **تصحيح الإملاء مع الحفاظ على اللهجة:**
   - اكتب الكلام باللهجة التي قيل بها (مصرية، خليجية، شامي..)، لكن **بإملاء عربي صحيح**.
   - صحح الحروف التي تنطق خطأ في العامية لكن تكتب صحيحة.
     * أمثلة للتصحيح الواجب: 
       - (تانيه واحده) -> تكتب "ثانية واحدة"
       - (ظبط) -> تكتب "ضبط"
       - (دلوقتى) -> تكتب "دلوقتي"
       - (والنبى) -> تكتب "والنبي"
       - (مظبوط) -> تكتب "مضبوط"
       - (حضرتك) -> تكتب كما هي بالتاء المربوطة وليس الهاء.
   - لا تحول العامية إلى فصحى (لا تغير "عايز" إلى "أريد")، اتركها عامية لكن مكتوبة صح.

2. **التمييز بين المتحدثين:**
   - ميز بدقة بين الـ "agent" (الموظف) والـ "customer" (العميل) بناءً على سياق الكلام.

3. **الكلمات غير العربية:**
   - اكتب الكلمات الإنجليزية بحروف إنجليزية (Order, Refund, Delivery).
   - يجوز استخدام مصطلحات تقنية إنجليزية وسط الجملة، لكن باقي الشرح يكون بالعربية.

4. **عدم التخمين:**
   - لو في كلمة أو جزء غير واضح: استخدم "[غير واضح]" أو "[...]" بدلاً من اختراع كلمة جديدة.

### ثانياً: تعليمات التحليل (Analysis Rules):
1. اعتمد على دليل سياسات الجودة المرفق (COMPANY_PROCESS) في تصنيف الأخطاء بدقة:
   - حدد الـ Item (مثل Greeting, Information, Handling Skills).
   - حدد النوع (NC, CTB, CTC).
   - كن دقيقاً في وصف الخطأ كما حدث في المكالمة.

2. **لغة المخرجات التحليلية (مهم جداً):**
   - اكتب كل الشروحات والتحليلات النصية باللغة العربية فقط.
   - الحقول التالية يجب أن تكون بالعربية فقط:
     - `analysis.summary`
     - `analysis.agent_attitude`
     - `analysis.main_issue_category`
     - `agent_issues[*].description`
     - `corrective_actions` (جميع العناصر داخل القائمة)
   - لا تكتب جمل كاملة بالإنجليزية. إذا احتجت لمصطلح إنجليزي اكتبه داخل النص العربي مثل:
     "خطأ في رقم الـ Order ID" أو "تأخير في الـ Delivery".
   - أي وصف يظهر باللغة الإنجليزية يجب أن تعيده بصياغة عربية واضحة.

### المطلوب (Output Format):
أخرج النتيجة في صيغة JSON فقط (بدون أي نص أو علامات Markdown مثل ```json) وبنفس الهيكل التالي تماماً:

{
  "metadata": { ... },
  "transcript": [ ... ],
  "analysis": { ... },
  "agent_issues": [
    {
      "time": "MM:SS",
      "item": "Handling Skills",
      "type": "CTC",
      "description": "..."
    }
  ],
  "quality_scores": { ... },
  "corrective_actions": [ ... ]
}
"""

    parts = [
        prompt,
        COMPANY_PROCESS,
        {"mime_type": mime_type or "audio/mp3", "data": audio_bytes},
    ]

    response = model.generate_content(
        parts,
        generation_config={"response_mime_type": "application/json"},
    )

    text = response.text

    if text.startswith("```json"):
        text = text.lstrip("```json\n")
    if text.endswith("```"):
        text = text.rstrip("\n```")

    data = json.loads(text)
    return data


# ========= 5. LOAD DATA (JSON أو AUDIO) =========
def load_data(uploaded_file):
    """يتعامل مع JSON أو ملفات صوت."""
    if uploaded_file is None:
        return

    file_name = uploaded_file.name.lower()

    # 1) JSON جاهز
    if file_name.endswith(".json"):
        try:
            data = json.load(uploaded_file)
            if all(key in data for key in ["metadata", "quality_scores", "transcript"]):
                st.session_state.report_data = data
                st.success(f"تم تحميل وعرض تحليل المكالمة من الملف: {file_name}")
            else:
                st.error(
                    "صيغة ملف JSON غير صالحة. تأكد من احتواء الملف على metadata, quality_scores, transcript."
                )
        except Exception as e:
            st.error(f"حدث خطأ أثناء قراءة ملف JSON: {e}")
        return

    # 2) ملف صوت (MP3/WAV/...)
    audio_exts = (".mp3", ".wav", ".m4a", ".ogg", ".webm")
    if file_name.endswith(audio_exts):
        try:
            audio_bytes = uploaded_file.read()
            mime_type = uploaded_file.type or "audio/mp3"

            with st.spinner("جاري تحليل ملف الصوت وتحويله لتقرير جودة مكالمة..."):
                report = analyze_audio_to_report(audio_bytes, mime_type)

            st.session_state.report_data = report
            st.success("تم تحليل المكالمة الصوتية بنجاح باستخدام Gemini.")
        except Exception as e:
            st.error(f"حدث خطأ أثناء تحليل ملف الصوت: {e}")
        return

    st.warning(f"نوع الملف غير مدعوم: {file_name}")


# ========= 6. HELPER FUNCTIONS =========
def get_sentiment_style(sentiment):
    sentiment_lower = str(sentiment).lower()
    if sentiment_lower == "positive":
        return "#10b981", "Positive"
    elif sentiment_lower == "negative":
        return "#ef4444", "Negative"
    else:
        return "#9ca3af", "Neutral"


def get_churn_style(risk):
    risk_lower = str(risk).lower()
    if risk_lower == "low":
        return "#10b981", "Low"
    elif risk_lower == "medium":
        return "#f59e0b", "Medium"
    else:
        return "#ef4444", "High"


def normalize_metric(value):
    """يضمن أن كل معيار في quality_scores يكون ديكشنري فيه score/comment."""
    if isinstance(value, dict):
        score = value.get("score", 0)
        comment = value.get("comment", "")
    else:
        score = value
        comment = "Auto-normalized from primitive."

    try:
        score = float(score)
    except Exception:
        score = 0.0

    return {"score": score, "comment": comment}


def build_plain_transcript(transcript):
    """يبني نص بسيط يمكن تحميله كملف TXT."""
    lines = []
    for line in transcript:
        t = line.get("time", "")
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        lines.append(f"[{t}] {speaker}: {text}")
    return "\n".join(lines)


# ========= 7. DASHBOARD UI =========

uploaded_file = st.sidebar.file_uploader(
    "تحميل المكالمة (صوت أو تقرير JSON)",
    type=["json", "mp3", "wav", "m4a", "ogg", "webm"],
    help="ارفع ملف MP3/WAV للمكالمة أو ملف JSON يحتوي على تحليل جاهز.",
)

load_data(uploaded_file)

data = st.session_state.report_data
metadata = data.get("metadata", {})
analysis = data.get("analysis", {})
scores = data.get("quality_scores", {}) or {}
agent_issues = data.get("agent_issues", []) or []
transcript = data.get("transcript", []) or []

# ---- تطبيع درجات الجودة ----
criteria_keys = ["greeting", "empathy", "listening", "problem_solving", "closing"]
for k in criteria_keys:
    if k in scores:
        scores[k] = normalize_metric(scores[k])

overall_raw = scores.get("overall_score", None)
if overall_raw is None:
    values = []
    for k in criteria_keys:
        if k in scores and isinstance(scores[k], dict):
            try:
                values.append(float(scores[k]["score"]))
            except Exception:
                pass
    if values:
        avg = sum(values) / len(values)
        overall_value = round(avg * 10)
    else:
        overall_value = 0
    scores["overall_score"] = {
        "score": overall_value,
        "comment": "Overall score تم حسابه تلقائيًا من متوسط المعايير التفصيلية.",
    }
else:
    scores["overall_score"] = normalize_metric(overall_raw)

customer_sentiment_raw = analysis.get("customer_sentiment", "Neutral")
churn_risk_raw = analysis.get("churn_risk", "Medium")
main_issue_category = analysis.get("main_issue_category", "Not specified")

# --- Action Buttons ---
action_col1, action_col2, action_col3 = st.columns([2, 2, 2])
with action_col1:
    if st.button("🔁 Rerun Analysis"):
        st.info("لإعادة التحليل، من فضلك ارفع ملف مكالمة جديد من الشريط الجانبي.")

with action_col2:
    transcript_plain = build_plain_transcript(transcript)
    st.download_button(
        "⬇️ Download Transcript",
        data=transcript_plain,
        file_name=f"{metadata.get('id','call')}_transcript.txt",
        mime="text/plain",
    )

with action_col3:
    st.button(
        "📄 Export PDF (Soon)",
        help="سيتم تفعيل تصدير التقرير إلى PDF في تحديث لاحق.",
    )

st.markdown("---")

# --- Executive Summary ---
st.markdown(
    """
    <h2 style="text-align:center; margin-top: 0.5rem;">
        Executive Call Performance Summary
    </h2>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f"**Current data file:** `{uploaded_file.name if uploaded_file else 'Default sample data'}`"
)

col1, col2, col3, col4 = st.columns(4)

overall_score_for_color = scores["overall_score"]["score"]
try:
    overall_score_for_color = float(overall_score_for_color)
except Exception:
    overall_score_for_color = 0.0

score_color = (
    "#10b981"
    if overall_score_for_color >= 85
    else ("#f59e0b" if overall_score_for_color >= 70 else "#ef4444")
)

if overall_score_for_color >= 85:
    overall_bg = "linear-gradient(135deg, #dcfce7, #bbf7d0)"
elif overall_score_for_color >= 70:
    overall_bg = "linear-gradient(135deg, #fef9c3, #fde68a)"
else:
    overall_bg = "linear-gradient(135deg, #fee2e2, #fecaca)"

with col1:
    st.markdown(
        f"""
    <div class="stCard metric-card" style="padding:16px; text-align:center; border-right:5px solid {score_color}; background:{overall_bg};"
         title="التقييم العام لجودة المكالمة بناءً على جميع المعايير.">
        <div style="font-size:22px; margin-bottom:4px;">📊</div>
        <p style="font-size:13px; color:#374151; margin:0 0 4px 0;">Overall Score</p>
        <h2 style="font-size:34px; font-weight:800; margin:0; color:{score_color};">
            {int(overall_score_for_color)}
        </h2>
        <p style="font-size:11px; color:#4b5563; margin:4px 0 0 0;">out of 100</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

sentiment_color, sentiment_text = get_sentiment_style(customer_sentiment_raw)
if sentiment_text == "Positive":
    sentiment_bg = "linear-gradient(135deg, #dcfce7, #bbf7d0)"
elif sentiment_text == "Neutral":
    sentiment_bg = "linear-gradient(135deg, #f9fafb, #e5e7eb)"
else:
    sentiment_bg = "linear-gradient(135deg, #fee2e2, #fecaca)"

with col2:
    st.markdown(
        f"""
    <div class="stCard metric-card" style="padding:16px; text-align:center; background:{sentiment_bg};"
         title="تحليل شعور العميل أثناء المكالمة.">
        <div style="font-size:22px; margin-bottom:4px;">😊</div>
        <p style="font-size:13px; color:#374151; margin:0 0 4px 0;">Customer Sentiment</p>
        <p style="font-size:22px; font-weight:700; margin:0; color:{sentiment_color};">
            {sentiment_text}
        </p>
        <p style="font-size:11px; color:#4b5563; margin:4px 0 0 0;">
            {customer_sentiment_raw}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

churn_color, churn_text = get_churn_style(churn_risk_raw)
if churn_text == "Low":
    churn_bg = "linear-gradient(135deg, #dcfce7, #bbf7d0)"
elif churn_text == "Medium":
    churn_bg = "linear-gradient(135deg, #fef9c3, #fde68a)"
else:
    churn_bg = "linear-gradient(135deg, #fee2e2, #fecaca)"

with col3:
    st.markdown(
        f"""
    <div class="stCard metric-card" style="padding:16px; text-align:center; border-bottom:5px solid {churn_color}; background:{churn_bg};"
         title="احتمالية فقدان العميل (churn) بناءً على التجربة.">
        <div style="font-size:22px; margin-bottom:4px;">📈</div>
        <p style="font-size:13px; color:#374151; margin:0 0 4px 0;">Customer Churn Risk</p>
        <p style="font-size:22px; font-weight:700; margin:0; color:{churn_color};">
            {churn_text}
        </p>
        <p style="font-size:11px; color:#4b5563; margin:4px 0 0 0;">
            {churn_risk_raw}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        f"""
    <div class="stCard metric-card" style="padding:16px; text-align:center; background:linear-gradient(135deg,#e0f2fe,#bfdbfe);"
         title="أهم فئة مشكلة ظهرت في المكالمة (خدمة، تأخير، منتج، سلوك... إلخ).">
        <div style="font-size:22px; margin-bottom:4px;">🎯</div>
        <p style="font-size:13px; color:#374151; margin:0 0 4px 0;">Main Issue Category</p>
        <p style="font-size:18px; font-weight:700; margin:0; color:#111827;">
            {main_issue_category}
        </p>
        <p style="font-size:11px; color:#4b5563; margin:4px 0 0 0;">Was the issue resolved successfully?</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# --- تقسيم الشاشة: Alerts / Transcript ---
col_analysis, col_transcript = st.columns([5, 7])

with col_analysis:
    st.markdown("#### Agent Behavior Alerts")
    if agent_issues:
        for issue in agent_issues:
            issue_color = "#f59e0b"
            time_label = issue.get("time", "")
            item_label = issue.get("item", "")
            type_label = issue.get("type", "")
            type_badge = (
                f'<span style="font-size:10px; margin-left:6px; padding:2px 8px; border-radius:999px; background:#f97316; color:white;">{type_label}</span>'
                if type_label
                else ""
            )
            item_badge = (
                f'<span style="font-size:10px; margin-left:6px; padding:2px 8px; border-radius:999px; background:#fee2e2; color:#b91c1c;">{item_label}</span>'
                if item_label
                else ""
            )
            st.markdown(
                f"""
            <div class="stCard" style="padding:10px 12px; margin-top:8px; border-right:4px solid {issue_color}; background:#fff7e6;">
                <p style="margin:0; font-size:12px; font-weight:700; color:{issue_color};">
                    ⚠️ {time_label}
                    {type_badge}
                    {item_badge}
                </p>
                <p style="margin:4px 0 0 0; font-size:13px; color:#111827; direction:rtl; text-align:right;">
                    {issue.get('description','')}
                </p>
            </div>
            """,
                unsafe_allow_html=True,
            )
    else:
        st.info("لا توجد مشاكل سلوكية ملحوظة في هذه المكالمة.")

with col_transcript:
    tab_transcript, tab_summary = st.tabs(
        ["Call Transcript", "Summary & Analysis"]
    )

    # ===== Tab: Transcript =====
    with tab_transcript:
        st.markdown("#### Conversation Log")

        blocks_html = []
        for line in transcript:
            is_agent = str(line.get("speaker", "")).lower() == "agent"
            speaker_label = "الموظف" if is_agent else "العميل"
            bg_color = "#dbeafe" if not is_agent else "#dcfce7"
            label_color = "#1d4ed8" if not is_agent else "#15803d"
            highlight = any(
                issue.get("time") == line.get("time") for issue in agent_issues
            )
            border_style = "border-right:4px solid #f59e0b;" if highlight else ""

            time_str = html.escape(str(line.get("time", "")))
            raw_text = str(line.get("text", ""))

            safe_text = html.escape(raw_text)
            keywords = ["شكوى", "طلب إلغاء"]
            for kw in keywords:
                safe_text = safe_text.replace(
                    kw, f"<mark style='background:#facc15; padding:0 2px;'>{kw}</mark>"
                )

            block_html = f"""
<div style="background:{bg_color}; border-radius:12px; padding:10px 14px; margin-bottom:10px; box-shadow:0 1px 3px rgba(15,23,42,0.08); {border_style}">
  <div style="display:flex; gap:12px; align-items:flex-start;">
    <span style="font-size:11px; font-family:monospace; color:#6b7280; background:#f3f4f6; padding:2px 8px; border-radius:999px; white-space:nowrap;">
      {time_str}
    </span>
    <div style="flex:1; text-align:right; direction:rtl;">
      <p style="margin:0; font-size:13px; font-weight:700; color:{label_color}; text-align:right; direction:rtl;">{speaker_label}</p>
      <p style="margin:4px 0 0 0; font-size:13px; color:#111827; line-height:1.7; text-align:right; direction:rtl;">{safe_text}</p>
    </div>
  </div>
</div>
"""
            blocks_html.append(block_html)

        transcript_html = (
            '<div class="transcript-wrapper">'
            + "".join(blocks_html)
            + "</div>"
        )
        st.markdown(transcript_html, unsafe_allow_html=True)

    # ===== Tab: Summary & Analysis =====
    with tab_summary:
        st.markdown("#### Call Summary")
        summary_text = analysis.get("summary", "لا يوجد ملخص متاح لهذه المكالمة.")
        st.markdown(
            f"<div style='direction:rtl; text-align:right;'>{summary_text}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("---")

        st.markdown("#### Agent Attitude")
        attitude_text = analysis.get("agent_attitude", "لا يوجد وصف لسلوك الموظف.")
        st.markdown(
            f"<div style='direction:rtl; text-align:right;'>{attitude_text}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### Main Issue Category")
        st.write(main_issue_category)

        st.markdown("#### Quality Criteria Scores")
        scores_df = pd.DataFrame(
            [
                {
                    "Criterion": "Greeting",
                    "Score (out of 10)": scores.get("greeting", {}).get("score", 0),
                    "Note": scores.get("greeting", {}).get("comment", ""),
                },
                {
                    "Criterion": "Empathy",
                    "Score (out of 10)": scores.get("empathy", {}).get("score", 0),
                    "Note": scores.get("empathy", {}).get("comment", ""),
                },
                {
                    "Criterion": "Listening",
                    "Score (out of 10)": scores.get("listening", {}).get("score", 0),
                    "Note": scores.get("listening", {}).get("comment", ""),
                },
                {
                    "Criterion": "Problem solving",
                    "Score (out of 10)": scores.get("problem_solving", {}).get(
                        "score", 0
                    ),
                    "Note": scores.get("problem_solving", {}).get("comment", ""),
                },
                {
                    "Criterion": "Closing",
                    "Score (out of 10)": scores.get("closing", {}).get("score", 0),
                    "Note": scores.get("closing", {}).get("comment", ""),
                },
            ]
        )
        st.dataframe(scores_df, hide_index=True, use_container_width=True)

        # --- Expanders لتحليل نقاط القوة والضعف ---
        strengths = []
        weaknesses = []
        for k, label in [
            ("greeting", "Greeting"),
            ("empathy", "Empathy"),
            ("listening", "Listening"),
            ("problem_solving", "Problem solving"),
            ("closing", "Closing"),
        ]:
            s_val = scores.get(k, {}).get("score", 0)
            note = scores.get(k, {}).get("comment", "")
            try:
                s_val = float(s_val)
            except Exception:
                s_val = 0.0
            if s_val >= 7:
                strengths.append((label, s_val, note))
            elif s_val <= 4:
                weaknesses.append((label, s_val, note))

        st.markdown("#### Quality Insights")

        with st.expander("✅ Strengths", expanded=True):
            if strengths:
                for label, s_val, note in strengths:
                    st.markdown(
                        f"- **{label}** → {s_val}/10 – {note or 'No extra notes.'}"
                    )
            else:
                st.write("No clear strengths based on current scores.")

        with st.expander("⚠️ Weaknesses", expanded=True):
            if weaknesses:
                for label, s_val, note in weaknesses:
                    st.markdown(
                        f"- **{label}** → {s_val}/10 – {note or 'Needs improvement.'}"
                    )
            else:
                st.write("No severe weaknesses (≤ 4/10).")

        with st.expander("📝 Additional Notes / Accuracy", expanded=False):
            notes_text = analysis.get("notes", "") or analysis.get(
                "agent_attitude", ""
            )
            if notes_text:
                st.markdown(
                    f"<div style='direction:rtl; text-align:right;'>{notes_text}</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.write("No additional notes for this call.")
