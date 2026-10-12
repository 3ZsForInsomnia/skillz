"""Long help for `skillz -h` and `skillz <command> -h`: what each command does, touches, and asks."""

EXAMPLES_HEADING = "examples:"

OVERVIEW = """\
Download, track, and organize agent skills in a namespaced local library.

A skill is a folder containing SKILL.md. Namespaces are the folders above it:
downloaded skills default to vendor/<owner>/<skill>. Skill names are unique
across the whole library, so commands take bare names.

Files:
  $XDG_CONFIG_HOME/skillz/skillz.toml   your settings: library location, namespace options
  <library>/skillz.lock.json            written by skillz: sources, commits, hashes

Defaults: library at $XDG_DATA_HOME/skillz/skills (~/.local/share/skillz/skills)."""

OVERVIEW_EPILOG = "Run `skillz <command> -h` for details and examples."

LIST = """\
List every skill skillz can see, with its namespace, status, and description:
skills in the library, tracked or not, plus skills in pulled folders.

Statuses (computed on every run, never stored; no network):
  unchanged   matches what was installed
  edited      files changed since install
  untracked   not installed by skillz (your own, or copied in)
  missing     in the lock, but its folder is gone
  misplaced   tracked, but not in the namespace the lock records
  external    read in place from a pull_from folder; skillz never writes there

examples:
  skillz list
  skillz list -j        # JSON array of {name, namespace, status, description, path, source}"""

ADD = """\
Download skills from a GitHub repo into the library and record them in the lock.

The source is one of:
  owner/repo                                  the repo's default branch
  https://github.com/owner/repo               same as owner/repo
  https://github.com/owner/repo/tree/REF/PATH exactly that skill folder, at REF

With owner/repo, name the skills to install, or omit names to install every
skill currently in the repo. Skills land in vendor/<owner> unless -n is given;
a namespace that doesn't exist yet prompts before it's created (vendor/<owner>
is created without asking).

Refuses before writing anything if a name already exists anywhere in the
library, isn't in the repo, or has differing copies in the repo. Identical
copies (such as committed build output) resolve to the one highest in the repo.
Clones over SSH into a temporary folder that's deleted afterwards.

examples:
  skillz add anthropics/skills pdf docx
  skillz add softaworks/agent-toolkit humanizer -n core
  skillz add https://github.com/supabase/agent-skills/tree/main/skills/supabase-postgres-best-practices"""

REMOVE = """\
Delete tracked skills from disk and drop them from the lock. A source with no
skills left is dropped too.

Always asks first, and the question names any skills with local edits that
would be lost. Only works on skills skillz installed; delete untracked or
external skills by hand.

examples:
  skillz remove pdf
  skillz remove pdf docx"""

MOVE = """\
Move a skill's folder to another namespace and update the lock to match.

Works for any skill in the library, tracked or untracked, so your own skills
can move too. Asks before creating a namespace that doesn't exist yet. Refuses
external skills, pulled namespaces, and a destination that already exists.
Use this rather than mv for tracked skills, or they show as misplaced.

examples:
  skillz move lbm core
  skillz move pdf vendor/anthropics"""

STATUS = """\
Check tracked skills against their sources and show only the ones that need
attention: local edits, an available update, a missing folder, or a skill
removed upstream. Fetches each source once (network). Changes nothing.

With -d, adds a plain git diff for each change:
  local edits     the locked version against your folder (locked/ -> local/)
  updates         your folder against upstream (local/ -> upstream/), exactly
                  what `skillz update` would change on disk

examples:
  skillz status
  skillz status pdf -d"""

UPDATE = """\
Replace tracked skills that changed upstream, then record the new commit and
hashes in the lock.

Skills with local edits are skipped with a message unless -f is given, and -f
requires skill names, so one command can't overwrite every edited skill at
once. A skill removed upstream is left as it is. Run `skillz status -d` first
to see what would change.

examples:
  skillz update -c          # report what has updates, change nothing
  skillz update             # update everything that isn't edited
  skillz update pdf -f      # overwrite pdf's local edits with upstream"""

RESET = """\
Restore skills to exactly the commit the lock records, discarding local edits
and files added since install. A missing skill is restored into its locked
namespace. Doesn't ask: naming the skills is the confirmation.

Fetches the locked commit, so it fails clearly if upstream rewrote history and
that commit no longer exists.

examples:
  skillz reset pdf
  skillz reset pdf docx"""

COMPLETIONS = """\
Print the zsh completion script. Save it as _skillz in a folder on $fpath;
regenerate it after skillz's commands change.

examples:
  skillz completions > ~/.zsh/completions/_skillz"""

DESCRIPTIONS = {
    "list": LIST,
    "add": ADD,
    "remove": REMOVE,
    "move": MOVE,
    "status": STATUS,
    "update": UPDATE,
    "reset": RESET,
    "completions": COMPLETIONS,
}
