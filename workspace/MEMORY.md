# MEMORY.md — Long-Term Persistent Memory
Last updated: 2026-06-12

***

## Architecture (Current — April 2026)
- Primary brain: groq/llama-3.3-70b-versatile (free, fast, reliable)
- Fallback: ollama/gpt-oss:20b-cloud
- Bot runs on Ubuntu laptop (i7, 16GB RAM, no GPU), executes locally
- Telegram = remote control interface
- Memory system: file-based (MEMORY.md = facts, memory/YYYY-MM-DD.md = daily log)
- Bot start command: ./run.sh

## About Praveen
- Location: Chennai, India (IST timezone)
- Pet: Pug named Baddu
- Hates long explanations — loves direct execution
- Builds AI automation tools (Final Form AI project)
- Ubuntu i7 16GB laptop, no GPU
- Groq API key configured and working

## Permanent Bans / Never Do
- Oracle Cloud: permanently banned (caused hallucinations — BOOTSTRAP.md deleted)
- Local Ollama CPU inference: retired (too slow on 16GB laptop)
- Never suggest these again

## Project State (April 2026)
- AutoGen Studio: installed at /home/ubuntu/.local/lib/python3.12/site-packages (v0.4.2.2)
- AutoGen command location: ~/.local/bin/autogenstudio
- Launch command: ~/.local/bin/autogenstudio ui --port 8080 --host 0.0.0.0
- Working on: Multi-agent orchestration (OpenClaw → Gemini CLI → AutoGen)
- Phase A (VSCode launcher): pending
- Phase B (Gemini delegation): pending

## Lessons Learned
- BOOTSTRAP.md must be deleted after first run
- USER.md must be filled immediately or bot has zero grounding
- Ubuntu blocks system pip — use --break-system-packages or ~/.local/bin/
- PATH must include ~/.local/bin for user-installed commands to work
- Bot used to hallucinate fake command outputs — anti-hallucination rules added

## VL / Vision Capabilities  
- Current model (llama-3.3-70b) has NO vision — text only
- VL support: switch to Groq VL model when needed (Praveen confirmed this is fine)

## Session Notes — 2026-04-27
- User prefers Python for automation scripts.
- User is using FastAPI for the backend of their project ClawHub.
- User wants the bot to match their energy and vibe.
- User wants the bot to create files and run commands on their computer.
- A file named test.md has been created on the user's computer at the location /home/ubuntu/test.md.

## Session Notes — 2026-04-28
- User's system has 15Gi of RAM and 4.0Gi of swap space.
- The system's available RAM is 11Gi.
- The user's disk space usage is at 1% for the tmpfs filesystem.
- The size of the tmpfs filesystem is 1.6G.
- User's laptop specifications include an i7 processor, 16GB RAM, and no GPU.
- User has implemented a new feature allowing the bot to reach out for help without waiting for the user's next message.
- User expects immediate reporting of any issues encountered during tasks.
- The bot is expected to follow instructions step-by-step, verifying the output of each step before proceeding.
- The bot has the capability to append messages to and read the contents of files on the user's computer.
- User has upgraded the system, implying potential changes to the architecture or dependencies.
- The .gemini directory is present in the user's home folder, suggesting Gemini CLI is installed and potentially in use.
- The user's home folder contains a .codex directory, which may be related to the Codex model or other AI tools.
- User's system is set to the IST (Indian Standard Time) timezone.
- The user's system has been up for more than a day, indicating continuous usage.
- The bot is capable of handling file operations and system commands, but may not always have access to the MEMORY.md file.
- The user expects the bot to handle errors and exceptions, such as file not found errors, in a robust manner.
- The bot's MEMORY.md file is not always accessible or up-to-date, as indicated by the "Error: File not found" message.
- The bot is currently unable to access the MEMORY.md file, receiving a "File not found" error.
- The user expects the bot to be able to access and scroll through the MEMORY.md file to find relevant information.
- The MEMORY.md file is located at the path `/home/ubuntu/MEMORY.md`.
- The user has section headers in their MEMORY.md file, including ones related to architecture, project state, and lessons learned.
- There are specific session note sections for the dates 2026-04-27 and 2026-04-28, in addition to the one already known for 2026-04-28.
- The user inquires about the bot's capability to read screenshots, indicating a potential need for image processing or text extraction from images.
- The bot lacks native vision capabilities, being a text-based AI, and cannot directly read or process images.
- The bot can suggest OCR tools for extracting text from images but cannot perform this task itself.

## Session Notes � 2026-05-09
- OpenClaw's personality files are located in multiple files, including IDENTITY.md, SOUL.md, MEMORY.md, and USER.md, which define its core vibe, tone, language, and overall personality.
- The IDENTITY.md and SOUL.md files are not found in the expected location, C:\home\ubuntu\, indicating a potential issue with file paths or locations.
- OpenClaw attempts to load its identity and soul files, but encounters "File not found" errors, suggesting a discrepancy between expected and actual file locations.
- User's favorite color is Neon Void Blue
- User is testing the new portable architecture
- The user's favorite color has been updated to Lime Green.

## Session Notes � 2026-05-12
- System RAM is currently at 11Gi.
- Disk space is clear.
- No new user preferences or personal details were shared.
- The system is currently operational and ready for use.
- The bot is prepared to execute commands or run Python code as needed.

## Session Notes � 2026-06-12
- The user has initiated a new conversation and is checking the bot's status.
- The bot is confirming its readiness to perform tasks and execute code.
