import re
import requests
from bs4 import BeautifulSoup
from prompts import jd_extraction_prompt_template


def extract_jd_from_url_with_llm(client, url):
    try:
        print(f"🌐 Fetching job page content: {url}")
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        raw_text = soup.get_text(separator="\n")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        visible_text = "\n".join(lines[:200])  # 限制长度

        prompt = jd_extraction_prompt_template.format(
            url=url, visible_text=visible_text
        )
        print("🤖 Calling model to extract JD information")
        response = client.chat.completions.create(
            model="mistralai/devstral-2512:free",
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content

        jd, company, title = "", "Company", "Job"
        match_jd = re.search(r"### JD:\n(.*?)\n### Company:", content, re.DOTALL)
        match_co = re.search(r"### Company:\n(.*?)\n### Title:", content, re.DOTALL)
        match_tt = re.search(r"### Title:\n(.*)$", content, re.DOTALL)
        if match_jd:
            jd = match_jd.group(1).strip()
        if match_co:
            company = match_co.group(1).strip()
        if match_tt:
            title = match_tt.group(1).strip()

        if jd == "[FAILED]":
            raise Exception(
                "Failed to extract job description from URL. The page may not be accessible or may require manual review."
            )
        if company == "[UNKNOWN]":
            raise Exception(
                "Failed to extract company from URL. The page may not be accessible or may require manual review."
            )
        if title == "[UNKNOWN]":
            raise Exception(
                "Failed to extract title from URL. The page may not be accessible or may require manual review."
            )

        print(f"✅ Extraction completed → Company: {company}, Title: {title}")
        return jd, company, title

    except Exception as e:
        raise Exception(
            f"Failed to fetch job page: {str(e)}. Please verify the URL is accessible."
        )
