import streamlit as st
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from pydantic import BaseModel
import asyncio
import os
from connection import config  # Assume this has your API config; if issue, check OPENAI_API_KEY env

# API Key Issue Fix Tip: If error is API key, go to platform.openai.com, generate new key, set in env: export OPENAI_API_KEY=sk-... or in connection.py

# Set page config for pro design
st.set_page_config(
    page_title="Pro Multi-Agent Homework AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for high-level UI (modern, responsive, animations)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
    .main {background-color: #ffffff; font-family: 'Roboto', sans-serif;}
    .stChatMessage {border-radius: 12px; padding: 12px; margin: 8px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); transition: all 0.3s;}
    .stChatMessage:hover {box-shadow: 0 4px 8px rgba(0,0,0,0.15);}
    .user {background-color: #d0efff; color: #0056b3;}
    .assistant {background-color: #e6ffe6; color: #006600;}
    .sidebar .sidebar-content {background-color: #f8f9fa; border-right: 1px solid #dee2e6;}
    .stButton > button {background-color: #007bff; color: white; border-radius: 8px; font-weight: bold; transition: background 0.3s;}
    .stButton > button:hover {background-color: #0056b3;}
    .stSpinner {color: #28a745;}
    .fun-element {color: #ff9900; font-style: italic;}
    </style>
""", unsafe_allow_html=True)

# Guardrail output structure
class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str

# High-Level Guardrail Agent (strict, logical check)
guardrail_agent = Agent(
    name="Guardrail Check",
    instructions="""Logically analyze if the query is strictly educational/homework-related (e.g., math solving, history facts). 
    - Use clear criteria: Does it have learning keywords like equations, dates, events? (Yes/No)
    - If yes, output is_homework: true with concise reasoning (e.g., 'Query mentions algebra → educational').
    - If no, false with evidence (e.g., 'Query about weather → not homework').
    - Be ultra-precise: No assumptions; stick to query text for reliable check. If ambiguous, default to false.""",
    output_type=HomeworkOutput,
)

async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context, run_config=config)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )

# Expanded Specialist Agents (Fully Multi-Agent: Math, History, Science, English - High Level with Logic & Fun)
math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="For math equations, calculations, geometry",
    instructions="""Solve math problems accurately, logically, and with fun vibes! 
    - Restate the problem first for clarity.
    - Break into numbered steps with emojis (e.g., Step 1: 🔢 Add 5 to both sides).
    - Justify every step with rules (e.g., 'Using addition property').
    - Always verify at end (e.g., 'Plug x=5 back: Correct! ✅').
    - If unclear, politely ask for more details.
    - End with a quick fun fact (e.g., 'Math tip: Pi is infinite! 🥧').
    - Format: Problem → Steps → Answer → Verification → Fun Fact.
    Example: Query '3x=12'. Steps: 1. Divide by 3: x=4. Verify: 3*4=12 (spot on!). Fun Fact: Division is like sharing pizza equally! 🍕""",
)

history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="For historical events, dates, figures",
    instructions="""Explain history accurately like an exciting story, with logic! 
    - Start with overview (e.g., 'Here's the epic backstory! 📜').
    - List key facts with emojis (e.g., 📅 1947: Independence Day).
    - Explain cause-effect logic (e.g., 'This event led to that because...').
    - Add significance and a fun trivia (e.g., 'Did you know this king loved cats? 🐱').
    - If unsure, say 'Based on reliable records...' and stay neutral.
    - End with a curiosity question (e.g., 'What if this never happened?').
    - Format: Overview → Key Facts → Logic & Importance → Trivia → Question.
    Example: Query 'India Independence'. Overview: Freedom from British! Key Facts: 📅 Aug 15, 1947. Logic: Gandhi's movements built pressure. Trivia: Flag designed by Pingali! Question: How would world be different?""",
)

science_tutor_agent = Agent(  # New Agent for Multi-Agent Expansion
    name="Science Tutor",
    handoff_description="For physics, chemistry, biology concepts",
    instructions="""Teach science concepts logically and engagingly! 
    - Restate query for confirmation.
    - Explain in steps with diagrams if possible (describe: e.g., 'Imagine a circuit like this...').
    - Use real-world examples (e.g., 'Like how water boils at 100°C').
    - Verify facts (e.g., 'Based on Newton's laws').
    - End with experiment idea (e.g., 'Try this at home: ...').
    - Format: Concept → Steps/Explanation → Example → Verification → Experiment.
    Example: Query 'What is gravity?'. Explanation: Force pulling objects. Steps: 1. Newton's law. Example: Apple falling. Experiment: Drop a ball!""",
)

english_tutor_agent = Agent(  # New Agent for Full Multi-Agent System
    name="English Tutor",
    handoff_description="For grammar, literature, writing help",
    instructions="""Help with English logically and creatively! 
    - Analyze query (e.g., 'Grammar fix needed').
    - Provide corrections/steps with reasons (e.g., 'Change to past tense because...').
    - Add tips for improvement (e.g., 'Use active voice for impact').
    - If essay, suggest structure.
    - End with practice exercise.
    - Format: Analysis → Corrections → Tips → Exercise.
    Example: Query 'Fix: He go to school.'. Correction: He goes (subject-verb agreement). Tip: Check singular/plural. Exercise: Fix 'They runs'.""",
)

# Advanced Triage Agent (Handles Multi-Agents Routing Logically)
triage_agent = Agent(
    name="Triage Agent",
    instructions="""Route queries logically and error-free to the right specialist in this multi-agent system:
    - Analyze precisely: Keywords like 'solve/equation/number' → Math. 'when/date/event' → History. 'physics/chemical/biology' → Science. 'grammar/write/essay' → English.
    - Decision tree: Math? → Math Tutor. History? → History Tutor. Science? → Science Tutor. English? → English Tutor. Else: 'Not supported – try math, history, science, or English!'.
    - Justify with short reasoning (e.g., 'Keywords: equation → Math route').
    - Handle mixed: Prioritize primary topic (e.g., 'Science in history → Science').
    - No guesses: Base on evidence only for perfect handoff. If unclear, ask for clarification.""",
    handoffs=[math_tutor_agent, history_tutor_agent, science_tutor_agent, english_tutor_agent],  # Multi-Handoffs
    input_guardrails=[InputGuardrail(homework_guardrail)],
)

# Updated Async Run Function (Fix Errors: Better Handling)
async def async_run_agent(query: str):
    try:
        result = await Runner.run(triage_agent, query, run_config=config)
        return result.final_output, None
    except InputGuardrailTripwireTriggered as e:
        return f"❌ Guardrail Alert: {str(e)}. Let's focus on learning! 📖", "guardrail"
    except Exception as ex:
        return f"🚨 System Error: {str(ex)}. API key issue? Check env or config. Retry or contact support.", "error"

def run_agent(query: str):
    loop = asyncio.new_event_loop()  # New loop to avoid conflicts
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(async_run_agent(query))

# Sidebar (High-Level: More Options, Debug)
with st.sidebar:
    st.title("🧠 Pro Multi-Agent Helper")
    st.markdown("---")
    st.info("**Pro Features:**\n- Multi-Routing: Math, History, Science, English\n- Advanced Guardrails\n- Error Fixes\n- Fun & Logical Responses")
    st.markdown("---")
    if st.button("🔄 Reset Chat"):
        st.session_state.messages = []
        st.experimental_rerun()
    st.caption("Powered by OpenAI Agents - High-Level Learning! 🌟")
    st.warning("API Tip: If key error, regenerate at openai.com & set in env.")

# Main Interface (Improved UI: Cleaner, Interactive)
st.title("🦾 Ultimate AI Homework Multi-Agent")
st.markdown("*Ask about Math, History, Science, or English – Smart routing to experts! 🔥*")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"], avatar="👩‍🎓" if message["role"] == "user" else "🤖"):
        st.markdown(message["content"])
        if "type" in message:
            if message["type"] == "guardrail":
                st.error("⚠️ Invalid query – Stick to education!")
            elif message["type"] == "error":
                st.warning("🛠️ Fix in progress – Retry!")
            else:
                st.success("✅ Expert Routed!")

if prompt := st.chat_input("Enter your question (e.g., Solve x+5=10 or What is photosynthesis?)"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👩‍🎓"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Routing to Expert Agent... 🧠"):
            response, msg_type = run_agent(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response, "type": msg_type})

st.markdown("---")
st.markdown("<p style='text-align: center; color: #6c757d;'>High-Level Multi-Agent System by Grok – Enjoy Learning! 🚀</p>", unsafe_allow_html=True)