from dotenv import load_dotenv
from langfuse import Langfuse

load_dotenv(".env")

langfuse = Langfuse()


PROMPTS = {
    "resume-review/system": """You are an expert HR resume reviewer. When given a resume, you must:
1. Score it using the score_resume tool
2. Identify strengths using the identify_strengths tool
3. Suggest improvements using the suggest_improvements tool
4. Provide a final summary combining all findings.""",

    "resume-review/score": """Score the following resume out of 10. Consider:
- Clarity and writing quality
- Structure and formatting
- Completeness (contact info, experience, skills, education)

Resume:
{{resume_text}}

Respond with: Score: X/10 followed by brief reasoning.""",

    "resume-review/strengths": """Identify the top 3 strengths in this resume. Be specific.

Resume:
{{resume_text}}

List them as:
1. ...
2. ...
3. ...""",

    "resume-review/improvements": """Suggest the top 3 improvements for this resume. Be actionable and specific.

Resume:
{{resume_text}}

List them as:
1. ...
2. ...
3. ...""",
}


def seed():
    for name, content in PROMPTS.items():
        try:
            existing = langfuse.get_prompt(name, label="production")
            if existing.prompt == content:
                print(f"[skip]   {name} (unchanged)")
                continue
            langfuse.create_prompt(
                name=name,
                prompt=content,
                labels=["production"],
                type="text",
                commit_message="Updated via seed_prompts.py",
            )
            print(f"[update] {name} (new version)")
        except Exception:
            langfuse.create_prompt(
                name=name,
                prompt=content,
                labels=["production"],
                type="text",
                commit_message="Initial version",
            )
            print(f"[create] {name}")


if __name__ == "__main__":
    seed()
    print("\nDone.")
