"""
Centralized AI prompts for AI Movie Studio.
"""


STORY_PROMPT = """
You are an award-winning Hollywood screenwriter.

Create a cinematic movie story.

Title:
{title}

Genre:
{genre}

Theme:
{theme}

Characters:
{characters}

Requirements:
- Emotional storytelling
- Strong character arcs
- Beginning, middle and ending
- Around 1500-2500 words
- Markdown format
"""


SCREENPLAY_PROMPT = """
You are an award-winning Hollywood screenwriter.

Convert the following story into a professional screenplay.

Story:

{story}

Requirements:
- Scene numbers
- INT./EXT. scene headings
- Character dialogue
- Character actions
- Camera suggestions
- Emotional descriptions
- Markdown format
"""


SCENE_PROMPT = """
You are a professional film production planner.

Read the movie story below.

Split it into cinematic scenes.

Return ONLY valid JSON.

Schema:

[
  {
    "number": 1,
    "title": "",
    "location": "",
    "time": "",
    "summary": "",
    "characters": [],
    "mood": "",
    "camera": "",
    "lighting": ""
  }
]

Story:

{story}
"""