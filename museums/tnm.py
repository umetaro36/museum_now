import requests
from bs4 import BeautifulSoup
import re

def get_tnm_special_exhibitions():
    url = "https://www.tnm.jp/modules/r_exhibition/index.php?controller=ctg&cid=1"
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    exhibitions = []

    # liタグの中に全ての特別展が入っている
    cards = soup.select("li")
    for card in cards:
        text_container = card.select_one("div.text > div.inner")
        if not text_container:
            continue

        exb = {}

        # タイトル
        title_tag = text_container.find("h2", class_="title")
        if title_tag:
            exb["title"] = title_tag.get_text(strip=True)

        # 会期を含む<p>タグ（"info" クラス）
        date_tag = text_container.find("p", class_="info")
        if date_tag:
            date_match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日（.）)[\s\S]*?(\d{4}年\d{1,2}月\d{1,2}日（.）)", date_tag.get_text())
            if date_match:
                exb["date"] = f"{date_match.group(1)} ～ {date_match.group(2)}"
            else:
                exb["date"] = date_tag.get_text(strip=True)

        # 詳細ページURL
        detail_link_tag = text_container.select_one("a.el_btn_link._page")
        if detail_link_tag:
            exb["detail_url"] = detail_link_tag["href"]

            # 観覧料情報を取得（詳細ページ）
            try:
                detail_res = requests.get(exb["detail_url"])
                detail_res.encoding = detail_res.apparent_encoding
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")

                fee_text_candidates = detail_soup.find_all(string=re.compile(r"(観覧料|料金|入場料|前売)"))
                for text in fee_text_candidates:
                    parent = text.find_parent(["p", "div", "section", "li", "td"])
                    if parent:
                        fee_text = parent.get_text(strip=True)

                        # 大人料金
                        normal_match = re.search(r"(一般|大人)[^\d]{0,5}([\d,]+)円", fee_text)
                        if normal_match:
                            exb["adult_fee"] = normal_match.group(2) + "円"

                        # 前売り大人料金
                        pre_match = re.search(r"(前売[^\d]{0,5})(一般|大人)?[^\d]{0,5}([\d,]+)円", fee_text)
                        if pre_match:
                            exb["pre_sale_adult_fee"] = pre_match.group(3) + "円"

                        if "adult_fee" in exb and "pre_sale_adult_fee" in exb:
                            break
            except Exception:
                exb["adult_fee"] = "取得エラー"

        exhibitions.append(exb)

    return exhibitions

if __name__ == "__main__":
    exhibitions = get_tnm_special_exhibitions()
    for idx, exb in enumerate(exhibitions, 1):
        print(f"\n◉ 特別展 {idx}")
        print(f"　タイトル: {exb.get('title')}")
        print(f"　会期: {exb.get('date')}")
        print(f"　大人料金: {exb.get('adult_fee', '情報なし')}")
        print(f"　前売り大人料金: {exb.get('pre_sale_adult_fee', '情報なし')}")
        print(f"　詳細ページ: {exb.get('detail_url')}")
