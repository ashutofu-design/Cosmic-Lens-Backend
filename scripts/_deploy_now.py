import subprocess
import pathlib

root = pathlib.Path(r"d:\Cosmic-Lens-Backend")
log = root / "deploy_automation.log"

def run(cmd: str) -> int:
    r = subprocess.run(cmd, shell=True, cwd=root, capture_output=True, text=True)
    with log.open("a", encoding="utf-8", errors="replace") as f:
        f.write(f"\n>>> {cmd}\n")
        if r.stdout:
            f.write(r.stdout)
        if r.stderr:
            f.write(r.stderr)
        f.write(f"\nexit={r.returncode}\n")
    return r.returncode

paths = " ".join([
    "artifacts/api-server/ask_education",
    "artifacts/api-server/openai_helper.py",
    "artifacts/api-server/ask_intent_llm.py",
    "artifacts/api-server/ask_career/classifier.py",
    "artifacts/api-server/ask_career/sector_registry.py",
    "artifacts/api-server/scripts/audit_education_full.py",
    "artifacts/api-server/tests/test_ask_education_engine.py",
])

run("git add " + paths)
c = run('git commit -m "Ask: education engine (15 archetypes) + 241-question audit fixes and routing"')
p = run("git push")
s = run(
    'ssh -o BatchMode=yes -o ConnectTimeout=60 root@187.127.174.55 '
    '"cd /root/Cosmic-Lens-Backend && find . -name \'*.pyc\' -delete && git pull '
    '&& cd artifacts/api-server && pm2 restart cosmic-api --update-env"'
)
h = subprocess.run("git rev-parse HEAD", shell=True, cwd=root, capture_output=True, text=True)
head = (h.stdout or "").strip()
with log.open("a", encoding="utf-8") as f:
    f.write(
        f"\nFINAL: commit={head} commit_exit={c} push_exit={p} ssh_exit={s}\n"
    )
