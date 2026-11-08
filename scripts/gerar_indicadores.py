#!/usr/bin/env python3
"""Atualiza o painel SVG usando arquivos públicos dos projetos do GitHub."""
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

OWNER = "JIsrael456"
PROJECTS = ["analise-chamados-sla", "sql-lab", "homelab-infra"]
OUTPUT = Path("projetos.svg")


def github(path):
    req = Request("https://api.github.com/" + path, headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": "portfolio-indicators",
        **({"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"]} if os.getenv("GITHUB_TOKEN") else {}),
    })
    with urlopen(req, timeout=25) as response:
        return json.load(response)


def files_in(repo):
    metadata = github("repos/" + OWNER + "/" + repo)
    branch = metadata["default_branch"]
    tree = github("repos/" + OWNER + "/" + repo + "/git/trees/" + branch + "?recursive=1")
    if tree.get("truncated"):
        raise RuntimeError("Árvore incompleta para " + repo)
    return [item["path"] for item in tree["tree"] if item["type"] == "blob"]


def generate():
    paths = {repo: files_in(repo) for repo in PROJECTS}
    sql_files = sum(p.lower().endswith(".sql") for paths_in_repo in paths.values() for p in paths_in_repo)
    pbix_files = sum(p.lower().endswith(".pbix") for paths_in_repo in paths.values() for p in paths_in_repo)
    # Fases planejadas, não concluídas: contagem de diretórios documentados no homelab.
    phases = len({p.split("/")[0] for p in paths["homelab-infra"] if p.startswith("fase-")})
    stats = [(str(len(PROJECTS)), "Projetos", "em destaque"),
             (str(sql_files), "Arquivos SQL", "versionados"),
             (str(pbix_files), "Dashboards", "arquivos PBIX"),
             (str(phases), "Fases", "planejadas")]
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="860" height="220" viewBox="0 0 860 220" role="img" aria-label="Projetos em números">',
           '<rect width="860" height="220" rx="8" fill="#1a1b27" stroke="#52576a"/>',
           '<text x="24" y="35" fill="#70a5fd" font-family="Arial,sans-serif" font-weight="bold" font-size="20">Projetos em números</text>']
    for i, (value, label, subtitle) in enumerate(stats):
        x = 24 + i * 209
        svg.extend([
            f'<rect x="{x}" y="60" width="188" height="130" rx="7" fill="#202438" stroke="#41475e"/>',
            f'<text x="{x + 94}" y="112" fill="#70a5fd" font-family="Arial,sans-serif" font-weight="bold" font-size="35" text-anchor="middle">{escape(value)}</text>',
            f'<text x="{x + 94}" y="143" fill="#38bdae" font-family="Arial,sans-serif" font-size="14" text-anchor="middle">{escape(label)}</text>',
            f'<text x="{x + 94}" y="161" fill="#b5bdd1" font-family="Arial,sans-serif" font-size="11" text-anchor="middle">{escape(subtitle)}</text>'
        ])
    svg.append('</svg>\n')
    result = "\n".join(svg)
    if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != result:
        OUTPUT.write_text(result, encoding="utf-8")
    print("Indicadores:", dict(zip([x[1] for x in stats], [x[0] for x in stats])))


if __name__ == "__main__":
    generate()
