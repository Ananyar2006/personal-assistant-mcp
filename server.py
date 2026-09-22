import json
import os

from mcp.server import MCPServer


NOTES_FILE = "notes.json"

mcp = MCPServer("Personal Assistant Memory Server")


def load_notes():
    """Load all notes from notes.json."""

    if not os.path.exists(NOTES_FILE):
        return []

    try:
        with open(NOTES_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return []


def save_notes(notes):
    """Save all notes to notes.json."""

    with open(NOTES_FILE, "w", encoding="utf-8") as file:
        json.dump(notes, file, indent=4)


@mcp.tool()
def save_note(content: str, tags: str = "") -> str:
    """Save a new note with its content and tags."""

    notes = load_notes()

    if notes:
        new_id = max(note["id"] for note in notes) + 1
    else:
        new_id = 1

    tag_list = [
        tag.strip()
        for tag in tags.split(",")
        if tag.strip()
    ]

    new_note = {
        "id": new_id,
        "content": content,
        "tags": tag_list
    }

    notes.append(new_note)
    save_notes(notes)

    return (
        f"Note saved successfully.\n"
        f"ID: {new_id}\n"
        f"Content: {content}\n"
        f"Tags: {tag_list}"
    )


@mcp.tool()
def search_notes(query: str) -> str:
    """Search notes using a keyword or phrase."""

    notes = load_notes()
    query = query.lower().strip()

    if not query:
        return "Please enter a search query."

    matching_notes = []

    for note in notes:
        content = note["content"].lower()
        tags = " ".join(note["tags"]).lower()

        if query in content or query in tags:
            matching_notes.append(note)

    if not matching_notes:
        return f"No notes found for: {query}"

    result = "Matching Notes:\n\n"

    for note in matching_notes:
        result += (
            f"ID: {note['id']}\n"
            f"Content: {note['content']}\n"
            f"Tags: {', '.join(note['tags'])}\n\n"
        )

    return result


@mcp.tool()
def delete_note(note_id: int) -> str:
    """Delete a note using its ID."""

    notes = load_notes()

    updated_notes = [
        note for note in notes
        if note["id"] != note_id
    ]

    if len(updated_notes) == len(notes):
        return f"No note found with ID {note_id}."

    save_notes(updated_notes)

    return f"Note {note_id} deleted successfully."


if __name__ == "__main__":
    mcp.run(transport="stdio")