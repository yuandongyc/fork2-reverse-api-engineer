"""GitHub Copilot SDK implementation for reverse engineering."""

import asyncio
from typing import Any

import questionary

from .base_engineer import BaseEngineer
from .tui import THEME_PRIMARY, THEME_SECONDARY


class CopilotEngineer(BaseEngineer):
    """Uses GitHub Copilot SDK to analyze HAR files and generate API scripts."""

    def __init__(
        self,
        run_id: str,
        har_path: Any,
        prompt: str,
        copilot_model: str | None = None,
        **kwargs: Any,
    ):
        super().__init__(run_id=run_id, har_path=har_path, prompt=prompt, **kwargs)
        self.copilot_model = copilot_model or "gpt-5"

    def _build_ask_user_tool(self) -> Any:
        """Build the ask_user_question custom tool for Copilot sessions."""
        try:
            from copilot import define_tool
        except ImportError:
            raise ImportError("GitHub Copilot SDK not installed. Install with: uv pip install 'reverse-api-engineer[copilot]'") from None

        from pydantic import BaseModel, Field

        class QuestionOption(BaseModel):
            label: str = Field(description="Display text for this option")
            description: str = Field(default="", description="Explanation of what this option means")

        class Question(BaseModel):
            question: str = Field(description="The question to ask the user")
            header: str = Field(default="", description="Short label for context")
            options: list[QuestionOption] = Field(default_factory=list, description="Available choices")
            multiSelect: bool = Field(default=False, description="Allow multiple selections")

        class AskUserParams(BaseModel):
            questions: list[Question] = Field(description="Questions to ask the user")

        ui = self.ui

        @define_tool(description="Ask the user a clarifying question. Use when you need user input to proceed.")  # type: ignore[misc]
        async def ask_user_question(params: AskUserParams) -> str:
            answers: dict[str, str] = {}

            ui.console.print()
            ui.console.print(f"  [{THEME_PRIMARY}]?[/{THEME_PRIMARY}] [bold white]Agent Question[/bold white]")
            ui.console.print()

            for q in params.questions:
                if not q.question:
                    continue

                if q.header:
                    ui.console.print(f"  [dim]{q.header}[/dim]")

                try:
                    if q.multiSelect:
                        choices = [f"{opt.label} - {opt.description}" if opt.description else opt.label for opt in q.options]
                        if choices:
                            selected = await questionary.checkbox(
                                f" > {q.question}",
                                choices=choices,
                                qmark="",
                                style=questionary.Style(
                                    [
                                        ("pointer", f"fg:{THEME_PRIMARY} bold"),
                                        ("highlighted", f"fg:{THEME_PRIMARY} bold"),
                                        ("selected", f"fg:{THEME_PRIMARY}"),
                                    ]
                                ),
                            ).ask_async()

                            if selected is None:
                                raise KeyboardInterrupt

                            labels = [s.split(" - ")[0] if " - " in s else s for s in selected]
                            answers[q.question] = ", ".join(labels)
                        else:
                            answer = await questionary.text(
                                f" > {q.question}",
                                qmark="",
                                style=questionary.Style([("question", f"fg:{THEME_SECONDARY}")]),
                            ).ask_async()
                            if answer is None:
                                raise KeyboardInterrupt
                            answers[q.question] = answer.strip()
                    else:
                        choices = [f"{opt.label} - {opt.description}" if opt.description else opt.label for opt in q.options]
                        if choices:
                            answer = await questionary.select(
                                f" > {q.question}",
                                choices=choices,
                                qmark="",
                                style=questionary.Style(
                                    [
                                        ("pointer", f"fg:{THEME_PRIMARY} bold"),
                                        ("highlighted", f"fg:{THEME_PRIMARY} bold"),
                                    ]
                                ),
                            ).ask_async()

                            if answer is None:
                                raise KeyboardInterrupt

                            label = answer.split(" - ")[0] if " - " in answer else answer
                            answers[q.question] = label
                        else:
                            answer = await questionary.text(
                                f" > {q.question}",
                                qmark="",
                                style=questionary.Style([("question", f"fg:{THEME_SECONDARY}")]),
                            ).ask_async()
                            if answer is None:
                                raise KeyboardInterrupt
                            answers[q.question] = answer.strip()

                    ui.console.print(f"  [dim]→ {answers[q.question]}[/dim]")

                except KeyboardInterrupt:
                    ui.console.print("  [dim]User cancelled question[/dim]")
                    answers[q.question] = ""

            ui.console.print()

            # Return answers as formatted string
            return "\n".join(f"{k}: {v}" for k, v in answers.items())

        return ask_user_question

    async def analyze_and_generate(self) -> dict[str, Any] | None:
        """Run the reverse engineering analysis with GitHub Copilot."""
        try:
            from copilot import CopilotClient
        except ImportError:
            self.ui.error("GitHub Copilot SDK not installed. Install with: uv pip install 'reverse-api-engineer[copilot]'")
            return None

        self.ui.header(self.run_id, self.prompt, self.copilot_model, self.sdk)
        self.ui.start_analysis()

        prompt = self._build_analysis_prompt()
        self.message_store.save_prompt(prompt)

        done_event = asyncio.Event()
        accumulated_text: list[str] = []

        def on_event(event: Any) -> None:
            event_type = event.type.value if hasattr(event.type, "value") else str(event.type)

            if event_type == "assistant.message_delta":
                delta = ""
                if hasattr(event, "data") and hasattr(event.data, "delta_content"):
                    delta = event.data.delta_content or ""
                if delta:
                    accumulated_text.append(delta)
                    self.ui.thinking(delta)

            elif event_type == "assistant.message":
                # Extract usage if available
                if hasattr(event, "data") and hasattr(event.data, "usage"):
                    usage = event.data.usage
                    if isinstance(usage, dict):
                        self.usage_metadata["input_tokens"] = usage.get("prompt_tokens", 0)
                        self.usage_metadata["output_tokens"] = usage.get("completion_tokens", 0)

            elif event_type == "session.idle":
                done_event.set()

            elif event_type == "session.compaction_start":
                self.ui.console.print("  [dim]session compacting...[/dim]")

            elif event_type == "session.compaction_complete":
                self.ui.console.print("  [dim]session compaction complete[/dim]")

        try:
            ask_user_tool = self._build_ask_user_tool()

            client = CopilotClient(
                {
                    "auto_start": True,
                    "use_logged_in_user": True,
                }
            )
            await client.start()

            session = await client.create_session(
                {
                    "model": self.copilot_model,
                    "streaming": True,
                    "infinite_sessions": {"enabled": True},
                    "tools": [ask_user_tool],
                }
            )

            session.on(on_event)

            await session.send({"prompt": prompt})

            # Wait for session to complete
            await done_event.wait()

            # Save accumulated thinking text
            if accumulated_text:
                self.message_store.save_thinking("".join(accumulated_text))

            # Build result
            script_path = str(self.scripts_dir / self._get_client_filename())
            local_path = str(self.local_scripts_dir / self._get_client_filename()) if self.local_scripts_dir else None
            self.ui.success(script_path, local_path)

            # GitHub subscription: cost is 0 (included in Copilot subscription)
            self.usage_metadata["estimated_cost_usd"] = 0.0

            # Display usage if available
            input_tokens = self.usage_metadata.get("input_tokens", 0)
            output_tokens = self.usage_metadata.get("output_tokens", 0)
            if input_tokens > 0 or output_tokens > 0:
                self.ui.console.print("  [dim]Usage:[/dim]")
                if input_tokens > 0:
                    self.ui.console.print(f"  [dim]  input: {input_tokens:,} tokens[/dim]")
                if output_tokens > 0:
                    self.ui.console.print(f"  [dim]  output: {output_tokens:,} tokens[/dim]")
                self.ui.console.print("  [dim]  cost: $0.00 (Copilot subscription)[/dim]")

            result: dict[str, Any] = {
                "script_path": script_path,
                "usage": self.usage_metadata,
            }
            self.message_store.save_result(result)
            return result

        except Exception as e:
            self.ui.error(str(e))
            self.message_store.save_error(str(e))
            self.ui.console.print("\n[dim]Make sure GitHub Copilot CLI is installed and you are logged in: gh auth login[/dim]")
            return None
