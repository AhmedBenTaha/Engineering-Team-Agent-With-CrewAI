from crewai.tools import tool
from pathlib import Path
import shutil
import subprocess


SANDBOX_DIR = Path(__file__).parents[3] / "sandbox"
SANDBOX_DIR.mkdir(parents=True, exist_ok=True)


def reset_sandbox() -> None:
    """Ensure the sandbox is a Gradio uv project without deleting its files."""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    pyproject = SANDBOX_DIR / "pyproject.toml"
    if not pyproject.exists():
        subprocess.run(
            ["uv", "init", "--bare", "--python", "3.13"],
            cwd=SANDBOX_DIR,
            check=True,
        )
    project_text = pyproject.read_text()
    if "gradio" not in project_text.lower():
        subprocess.run(["uv", "add", "gradio"], cwd=SANDBOX_DIR, check=True)

@tool("List Sandbox Files")
def list_sandbox_files() -> str:
    """
    List the filenames currently in the sandbox directory.

    Returns:
        A newline-separated list of filenames, or a message if the
        sandbox is empty.
    """
    names = sorted(p.name for p in SANDBOX_DIR.iterdir())
    return "\n".join(names) if names else "The sandbox is empty."


@tool("Read Sandbox File")
def read_sandbox_file(filename: str) -> str:
    """
    Read and return the text contents of a file in the sandbox directory.

    Args:
        filename: The name of the file to read (e.g. "solution.py").
    Returns:
        The file's contents, or a message if the file does not exist.
    """
    path = SANDBOX_DIR / filename
    if not path.is_file():
        return f"No such file in the sandbox: {filename}"
    return path.read_text()


@tool("Write Sandbox File")
def write_sandbox_file(filename: str, content: str) -> str:
    """
    Write text to a file in the sandbox directory, replacing any existing
    file with the same name.

    Args:
        filename: The name of the file to write (e.g. "solution.py").
        content: The text content to write.
    Returns:
        A confirmation message.
    """
    path = SANDBOX_DIR / filename
    path.write_text(content)
    return f"Wrote {len(content)} characters to {filename}."


@tool("Run Sandbox Python File")
def run_sandbox_python(filename: str) -> str:
    """
    Execute a Python file from the sandbox directory inside an ephemeral
    Docker container, with the sandbox mounted as the working directory,
    using `uv run` to run the code in the uv project.

    Returns the exit code, stdout, and stderr, clearly labeled. Note that
    Python's unittest module prints test results — including failures and
    tracebacks — to stderr by default, not stdout, so stderr is just as
    important as stdout for understanding what happened.

    Args:
        filename: The name of the Python file to run (e.g. "solution.py").
    Returns:
        A labeled block containing the exit code, stdout, and stderr.
    """
    docker = shutil.which("docker")
    if docker is None:
        return (
            "Exit code: 127\n\n"
            "--- stdout ---\n(empty)\n\n"
            "--- stderr ---\nDocker is required to run sandbox scripts safely, "
            "but the Docker CLI is not installed. The script was not run."
        )

    try:
        daemon = subprocess.run(
            [docker, "info"], capture_output=True, text=True, timeout=10
        )
    except subprocess.TimeoutExpired:
        return (
            "Exit code: 125\n\n"
            "--- stdout ---\n(empty)\n\n"
            "--- stderr ---\nDocker is required to run sandbox scripts safely, "
            "but checking the Docker daemon timed out. The script was not run."
        )
    if daemon.returncode != 0:
        details = daemon.stderr.strip() or daemon.stdout.strip()
        return (
            "Exit code: 125\n\n"
            "--- stdout ---\n(empty)\n\n"
            "--- stderr ---\nDocker is required to run sandbox scripts safely, "
            "but its daemon is unavailable. The script was not run. "
            f"{details}"
        )

    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "-v", f"{SANDBOX_DIR}:/workspace",
                "-w", "/workspace",
                "ghcr.io/astral-sh/uv:python3.13-bookworm-slim",
                "uv", "run", filename,
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return (
            f"Exit code: {result.returncode}\n\n"
            f"--- stdout ---\n{result.stdout or '(empty)'}\n\n"
            f"--- stderr ---\n{result.stderr or '(empty)'}"
        )
    except subprocess.TimeoutExpired as e:
        stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
        return (
            "The script timed out after 300 seconds.\n\n"
            f"--- stdout so far ---\n{stdout or '(empty)'}\n\n"
            f"--- stderr so far ---\n{stderr or '(empty)'}"
        )

sandbox_tools = [list_sandbox_files, read_sandbox_file, write_sandbox_file, run_sandbox_python]


def _never_cache(*_args, **_kwargs) -> bool:
    return False


# Sandbox state changes between calls (files appear/change/run), so caching tool
# results would feed agents stale data. Opt out of CrewAI's default tool caching.
for _t in sandbox_tools:
    _t.cache_function = _never_cache
