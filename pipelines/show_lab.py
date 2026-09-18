"""Print the eight must-show paths. Spoken command: python pipelines/show_lab.py"""

MUST_SHOW = r"""MUST-SHOW  (Dispatch-desk)
[1] inspect   instructions\{vehicles.json, jobs.json, dispatch_rules.md, rules_mcp.py}
[2] AGENTS.md AGENTS.md
[3] plan      PLAN.md
              .docs\specification\architecture.md
[4] skill     .grok\skills\dispatch-desk\SKILL.md
              .grok\plugins\dispatch-desk\skills\dispatch-desk\SKILL.md
[5] hook      .grok\hooks\protect-rules.json
              .grok\hooks\protect-vehicles.json
              .grok\plugins\dispatch-desk\hooks\hooks.json
[6] MCP       .grok\config.toml  [mcp_servers.rules]  tool rules__lookup_rule
              (plugin does not ship .mcp.json)
[7] script    python dispatch.py
[8] test      python -m unittest test_dispatch -v
Hotovo A/B    python dispatch.py
Do NOT use python3 on this laptop.
Do NOT grok mcp add if doctor is already green — show grok mcp list.
Plugin enable: grok plugin enable dispatch-desk  (or Space in /plugins).
Folder trust: grok --trust  /  /hooks-trust
Project skill+hook still show if the plugin is off.
"""


def main() -> None:
    print(MUST_SHOW, end="")


if __name__ == "__main__":
    main()
