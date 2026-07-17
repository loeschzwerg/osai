#!/usr/bin/env python3
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "httpx>=0.28.1",
#     "ipython>=9.15.0",
#     "rich>=15.0.0",
#     "typer>=0.26.8",
# ]
# ///

import os
import sys
sys.path.append(os.getcwd())
# import foo


def main() -> None:
    print("Hello from hosts.py!")

import sys
import subprocess
import xml.etree.ElementTree as ET
from urllib.parse import urlencode

def ensure_httpx_installed():
    try:
        import httpx  # noqa: F401
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
        import httpx  # noqa: F401

def get_attr(elem, names, default=None):
    for n in names:
        if elem is None:
            return default
        if n in elem.attrib:
            return elem.attrib[n]
    return default

def parse_nmap_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Nmap XML typically uses namespaces sometimes; handle both with "endswith"
    def findall(parent, tag_endswith):
        return [e for e in parent.iter() if e.tag.endswith(tag_endswith)]

    hosts = []
    # Find all "host" elements regardless of namespace
    for host in [e for e in root.iter() if e.tag.endswith("host")]:
        addr = None
        addrtype = None
        for a in [e for e in host.iter() if e.tag.endswith("address")]:
            addrtype = a.attrib.get("addrtype")
            if addrtype in ("ipv4", "ipv6"):
                addr = a.attrib.get("addr")
                break
        if not addr:
            continue

        ports = []
        ports_parent = None
        for mp in [e for e in host.iter() if e.tag.endswith("ports")]:
            ports_parent = mp
            break
        if ports_parent is None:
            continue

        for p in [e for e in ports_parent.iter() if e.tag.endswith("port")]:
            portid = p.attrib.get("portid")
            proto = p.attrib.get("protocol", "tcp")
            if not portid:
                continue
            ports.append((addr, int(portid), proto))

        hosts.append((addr, ports))
    return hosts

def guess_schemes(port, service_name=None):
    """
    Heuristic:
    - 443/8443 => https
    - 80/8080/8000/8888/5000/3000 => http
    - If service_name hints, use it.
    """
    name = (service_name or "").lower()
    if name:
        if "https" in name or "ssl" in name:
            return ["https"]
        if "http" in name and "https" not in name:
            return ["http"]

    if port in (443, 8443, 9443):
        return ["https"]
    if port in (80, 8000, 8080, 8888, 5000, 3000, 8001):
        return ["http"]
    return ["http", "https"]  # fallback

def build_service_map(xml_path):
    """
    Build: (ip, port, proto) -> service_name
    so we can better guess http vs https.
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()

    service_map = {}
    for host in [e for e in root.iter() if e.tag.endswith("host")]:
        addr = None
        for a in [e for e in host.iter() if e.tag.endswith("address")]:
            if a.attrib.get("addrtype") in ("ipv4", "ipv6"):
                addr = a.attrib.get("addr")
                break
        if not addr:
            continue

        for p in host.iter():
            if not p.tag.endswith("port"):
                continue
            portid = p.attrib.get("portid")
            proto = p.attrib.get("protocol", "tcp")
            if not portid:
                continue
            service_name = None
            for s in [e for e in p.iter() if e.tag.endswith("service")]:
                service_name = s.attrib.get("name")
                break
            service_map[(addr, int(portid), proto)] = service_name
    return service_map

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} path/to/nmap.xml [--path /] [--timeout 10] [--concurrency 50]", file=sys.stderr)
        sys.exit(1)

    xml_path = sys.argv[1]
    target_path = "/"
    timeout = 10.0
    concurrency = 50

    # Very small arg parsing
    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == "--path" and i + 1 < len(args):
            target_path = args[i + 1]
            i += 2
        elif args[i] == "--timeout" and i + 1 < len(args):
            timeout = float(args[i + 1])
            i += 2
        elif args[i] == "--concurrency" and i + 1 < len(args):
            concurrency = int(args[i + 1])
            i += 2
        else:
            i += 1

    ensure_httpx_installed()
    import httpx
    import asyncio

    hosts = parse_nmap_xml(xml_path)
    service_map = build_service_map(xml_path)

    targets = []
    # Collect ports => potential HTTP endpoints
    for ip, portlist in hosts:
        for port, proto in [(pp, pr) for (_, pp, pr) in [(ip, p, proto) for (ip2, p, proto) in portlist] for pr in []]:
            pass  # (kept to avoid accidental edits)

    # Rebuild correctly:
    for ip, ports in hosts:
        for port, proto in [(p, pr) for (_, p, pr) in ports]:
            service_name = service_map.get((ip, port, proto))
            schemes = guess_schemes(port, service_name=service_name)
            for scheme in schemes:
                # Avoid default port in URL formatting
                if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
                    base = f"{scheme}://{ip}"
                else:
                    base = f"{scheme}://{ip}:{port}"
                url = base.rstrip("/") + "/" + target_path.lstrip("/")
                targets.append((url, ip, port, scheme))

    # Dedupe by URL
    seen = set()
    unique_targets = []
    for t in targets:
        url = t[0]
        if url not in seen:
            seen.add(url)
            unique_targets.append(t)

    async def fetch(client, url, ip, port, scheme):
        try:
            # Lightweight probe; follow redirects to discover working endpoints.
            r = await client.get(url, follow_redirects=True)
            return {
                "ip": ip,
                "port": port,
                "scheme": scheme,
                "url": url,
                "status_code": r.status_code,
                "content_type": r.headers.get("content-type"),
                "title": None,  # left empty; no parsing here to keep it fast/light
                "redirected_to": str(r.url) if r.url else None,
            }
        except Exception as e:
            return {
                "ip": ip,
                "port": port,
                "scheme": scheme,
                "url": url,
                "error": str(e),
            }

    async def run():
        timeout_cfg = httpx.Timeout(timeout)
        limits = httpx.Limits(max_connections=concurrency, max_keepalive_connections=concurrency)

        async with httpx.AsyncClient(
            timeout=timeout_cfg,
            limits=limits,
            headers={"User-Agent": "nmap-xml-to-httpx/1.0"},
            verify=False,  # common for scanners; remove if you want strict TLS verification
        ) as client:
            tasks = [fetch(client, url, ip, port, scheme) for (url, ip, port, scheme) in unique_targets]
            # Gather in chunks to keep memory sane
            results = []
            chunk = 500
            for j in range(0, len(tasks), chunk):
                results.extend(await asyncio.gather(*tasks[j:j+chunk]))
            return results

    results = asyncio.run(run())

    # Print results as simple lines (easy to redirect)
    for res in results:
        if "error" in res:
            print(f"[FAIL] {res['url']} ({res['ip']}:{res['port']} {res['scheme']}) error={res['error']}")
        else:
            print(f"[OK] {res['url']} ({res['ip']}:{res['port']} {res['scheme']}) status={res['status_code']} content-type={res['content_type']}")

if __name__ == "__main__":
    main()
