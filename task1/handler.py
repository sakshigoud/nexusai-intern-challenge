"""
Task 1 — AI Message Handler
Async function that takes a customer message and returns a structured AI response.
"""

import asyncio
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI, APITimeoutError, RateLimitError

load_dotenv()  # Load .env file from project root


@dataclass
class MessageResponse:
    """Structured response from the AI message handler."""
    response_text: str
    confidence: float
    suggested_action: str
    channel_formatted_response: str
    error: Optional[str] = None


def get_system_prompt(channel: str) -> str:
    """Return a system prompt tailored for a telecom support agent."""
    base = (
        "You are a senior telecom customer support agent for NexusAI Telecom. "
        "You handle billing disputes, service outages, plan upgrades, SIM issues, "
        "and account inquiries. Be empathetic but efficient. "
        "Always acknowledge the customer's frustration before offering a solution. "
        "If you cannot resolve the issue, clearly state you will escalate to a specialist. "
        "Never make promises about credits or refunds without confirming eligibility. "
        "End every response with a clear next step for the customer."
    )
    if channel == "voice":
        base += (
            "\n\nIMPORTANT: This is a voice call. Keep your response under 2 sentences. "
            "Be concise and natural — avoid bullet points or long lists."
        )
    elif channel == "whatsapp":
        base += (
            "\n\nThis is a WhatsApp message. Use short paragraphs. "
            "You may use emojis sparingly to seem friendly. Keep it under 3-4 sentences."
        )
    else:  # chat
        base += (
            "\n\nThis is a live chat. You can provide detailed responses with step-by-step "
            "instructions if needed. Use clear formatting."
        )

    base += (
        "\n\nAfter your response, on a NEW LINE, output exactly:\n"
        "CONFIDENCE: <a float between 0 and 1>\n"
        "ACTION: <one of: resolve, escalate, follow_up, inform>\n"
        "Do NOT include any other text on those lines."
    )
    return base


def parse_ai_output(raw: str) -> tuple:
    """Parse confidence and action from the AI output."""
    lines = raw.strip().split("\n")
    confidence = 0.5
    action = "inform"
    response_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.upper().startswith("CONFIDENCE:"):
            try:
                confidence = float(stripped.split(":", 1)[1].strip())
                confidence = max(0.0, min(1.0, confidence))
            except ValueError:
                confidence = 0.5
        elif stripped.upper().startswith("ACTION:"):
            action = stripped.split(":", 1)[1].strip().lower()
        else:
            response_lines.append(line)

    return "\n".join(response_lines).strip(), confidence, action


def format_for_channel(text: str, channel: str) -> str:
    """Format the response text based on the channel."""
    if channel == "voice":
        # Keep only the first two sentences for voice
        sentences = text.replace("!", "!|").replace(".", ".|").replace("?", "?|").split("|")
        sentences = [s.strip() for s in sentences if s.strip()]
        return " ".join(sentences[:2])
    elif channel == "whatsapp":
        return text.replace("**", "*")  # WhatsApp uses single asterisks for bold
    return text  # chat — return as is


async def handle_message(
    customer_message: str,
    customer_id: str,
    channel: str,
) -> MessageResponse:
    """
    Process a customer message and return a structured AI response.

    Args:
        customer_message: The message from the customer.
        customer_id: Unique customer identifier.
        channel: One of "voice", "whatsapp", or "chat".

    Returns:
        MessageResponse with the AI-generated response and metadata.
    """
    # --- Error case (c): empty or whitespace-only input ---
    if not customer_message or not customer_message.strip():
        return MessageResponse(
            response_text="",
            confidence=0.0,
            suggested_action="error",
            channel_formatted_response="",
            error="Empty or whitespace-only input received.",
        )

    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    system_prompt = get_system_prompt(channel)

    try:
        # --- Call the API with a 10-second timeout ---
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"[Customer {customer_id}]: {customer_message}"},
                ],
                temperature=0.4,
                max_tokens=300,
            ),
            timeout=10,
        )

        raw_text = response.choices[0].message.content
        response_text, confidence, action = parse_ai_output(raw_text)
        formatted = format_for_channel(response_text, channel)

        return MessageResponse(
            response_text=response_text,
            confidence=confidence,
            suggested_action=action,
            channel_formatted_response=formatted,
            error=None,
        )

    except (asyncio.TimeoutError, APITimeoutError):
        # --- Error case (a): API timeout after 10 seconds ---
        return MessageResponse(
            response_text="",
            confidence=0.0,
            suggested_action="escalate",
            channel_formatted_response="",
            error="API request timed out after 10 seconds.",
        )

    except RateLimitError:
        # --- Error case (b): rate limit — retry once after 2 seconds ---
        await asyncio.sleep(2)
        try:
            response = await asyncio.wait_for(
                client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"[Customer {customer_id}]: {customer_message}"},
                    ],
                    temperature=0.4,
                    max_tokens=300,
                ),
                timeout=10,
            )

            raw_text = response.choices[0].message.content
            response_text, confidence, action = parse_ai_output(raw_text)
            formatted = format_for_channel(response_text, channel)

            return MessageResponse(
                response_text=response_text,
                confidence=confidence,
                suggested_action=action,
                channel_formatted_response=formatted,
                error=None,
            )
        except Exception as e:
            return MessageResponse(
                response_text="",
                confidence=0.0,
                suggested_action="escalate",
                channel_formatted_response="",
                error=f"Retry after rate limit also failed: {str(e)}",
            )


# --- Quick demo ---
if __name__ == "__main__":
    async def main():
        # Test with empty input
        # result = await handle_message("", "C001", "chat")
        # print("Empty input test:", result)

        # Test with a real message (requires OPENAI_API_KEY env var)
        result = await handle_message(
            "My internet has been down for 2 days, this is unacceptable!",
            "C002",
            "voice",
        )
        print("Voice test:", result)

    asyncio.run(main())
