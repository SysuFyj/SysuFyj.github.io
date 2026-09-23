#!/usr/bin/env python3
"""Build the local review page for the current draft inside the site's NexT theme."""
from pathlib import Path
import json
import re
import subprocess
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "content/drafts/2026-09-23-LLM注意力机制及优化.md"
TEMPLATE = ROOT / "2025/02/21/Transformer-cuda学习/index.html"
OUTPUT = ROOT / "draft-preview/index.html"
TITLE = "LLM 注意力机制及优化：从单 token 解码到稀疏与线性注意力"
DESCRIPTION = "梳理单 token 解码中的注意力计算、逐层 KV cache、MHA/GQA/MQA，以及 Gated Attention、MLA、KDA、DSA、CSA、HCA 与 SWA 的优化思路。"
LOCAL_URL = "http://127.0.0.1:8765/draft-preview/"


def set_meta(soup: BeautifulSoup, selector: str, attr: str, value: str) -> None:
    node = soup.select_one(selector)
    if node:
        node[attr] = value


def main() -> None:
    markdown = DRAFT.read_text()
    # Pandoc's dollar math extension handles the display math used in the draft.
    markdown = markdown.replace(r"\[", "$$").replace(r"\]", "$$")
    rendered = subprocess.run(
        [
            "pandoc",
            "--from",
            "markdown+yaml_metadata_block+tex_math_dollars",
            "--to",
            "html5",
            "--mathml",
        ],
        input=markdown,
        text=True,
        capture_output=True,
        check=True,
    ).stdout

    soup = BeautifulSoup(TEMPLATE.read_text(), "html.parser")
    soup.title.string = f"{TITLE} | Ringo的博客"
    set_meta(soup, 'meta[name="description"]', "content", DESCRIPTION)
    set_meta(soup, 'meta[property="og:title"]', "content", TITLE)
    set_meta(soup, 'meta[property="og:url"]', "content", LOCAL_URL)
    set_meta(soup, 'meta[property="og:description"]', "content", DESCRIPTION)
    canonical = soup.select_one('link[rel="canonical"]')
    if canonical:
        canonical["href"] = LOCAL_URL

    # Update the structured data carried by the static article shell.
    main_entity = soup.select_one('[itemprop="mainEntityOfPage"]')
    if main_entity:
        main_entity["href"] = LOCAL_URL
    author_name = soup.select_one('[itemprop="author"] [itemprop="name"]')
    if author_name:
        author_name["content"] = "Ringo.fu"
    publisher_name = soup.select_one('[itemprop="publisher"] [itemprop="name"]')
    if publisher_name:
        publisher_name["content"] = "Ringo的博客"
    post_creative = soup.select_one('[itemprop="post"] [itemprop="name"]')
    if post_creative:
        post_creative["content"] = f"{TITLE} | Ringo的博客"
    set_meta(soup, 'meta[property="article:published_time"]', "content", "2026-09-23T13:00:00.000Z")
    set_meta(soup, 'meta[property="article:modified_time"]', "content", "2026-09-23T13:00:00.000Z")
    for node in soup.select('meta[property="og:image"], meta[name="twitter:image"]'):
        node.decompose()

    page_config = soup.select_one('script.next-config[data-name="page"]')
    if page_config:
        config = json.loads(page_config.string or "{}")
        config.update({"permalink": LOCAL_URL, "path": "draft-preview/", "title": TITLE})
        page_config.string = json.dumps(config, ensure_ascii=False, separators=(",", ":"))

    post_header = soup.select_one(".post-header")
    if post_header:
        heading = post_header.select_one(".post-title")
        if heading:
            heading.clear()
            heading.append(TITLE)
        meta = post_header.select_one(".post-meta-container")
        if meta:
            meta.clear()
            meta.append(BeautifulSoup(
                '<div class="post-meta"><span class="post-meta-item"><span class="post-meta-item-icon"><i class="far fa-calendar"></i></span><span class="post-meta-item-text">Posted on</span><time datetime="2026-09-23T21:00:00+08:00" itemprop="dateCreated datePublished">2026-09-23</time></span><span class="post-meta-item"><span class="post-meta-item-icon"><i class="far fa-folder"></i></span><span class="post-meta-item-text">In</span><span itemprop="about" itemscope="" itemtype="http://schema.org/Thing"><span itemprop="name">论文</span></span>，<span itemprop="about" itemscope="" itemtype="http://schema.org/Thing"><span itemprop="name">大模型</span></span></span></div>',
                "html.parser",
            ))

    body = soup.select_one(".post-body")
    if body:
        body.clear()
        fragment = BeautifulSoup(rendered, "html.parser")
        for child in list(fragment.contents):
            body.append(child)

    # Rebuild the sidebar TOC from the headings in the rendered article.
    toc = soup.select_one(".post-toc")
    if toc and body:
        toc.clear()
        nav = soup.new_tag("ol", attrs={"class": "nav"})
        for heading in body.find_all(["h2", "h3", "h4"]):
            level = int(heading.name[1])
            li = soup.new_tag("li", attrs={"class": f"nav-item nav-level-{level}"})
            link = soup.new_tag("a", attrs={"class": "nav-link", "href": "#" + (heading.get("id") or "")})
            span = soup.new_tag("span", attrs={"class": "nav-text"})
            span.string = heading.get_text(" ", strip=True)
            link.append(span)
            li.append(link)
            nav.append(li)
        toc.append(nav)

    # The cloned article's next/previous links point to an unrelated post.
    footer = soup.select_one(".post-footer")
    if footer:
        footer.decompose()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(str(soup))
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
