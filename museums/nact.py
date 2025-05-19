import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.nact.jp/"

def get_nact_exhibitions():
    url = BASE_URL
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    exhibitions = []

    # 「展覧会」セクション内のスライドを取得
    slides = soup.select("li.splide__slide")
    for slide in slides:
        # ステータスカテゴリを取得（例：開催中、企画展、公募展など）
        status_tags = slide.select("ul.ex_cate li")
        statuses = [tag.get_text(strip=True) for tag in status_tags]

        # 公募展などの除外と、開催中かつ展覧会（企画展など）のみを対象
        if "開催中" not in statuses:
            continue
        if not any(s in statuses for s in ["企画展", "展覧会"]):
            continue

        exb = {}

        # タイトル
        title_tag = slide.find("h2")
        if title_tag:
            exb["title"] = title_tag.get_text(strip=True)

        # 会期
        date_tag = slide.find("p", class_="ex_date")
        if date_tag:
            exb["date"] = date_tag.get_text(strip=True)

        # 詳細ページURL
        a_tag = slide.find("a")
        if a_tag and "href" in a_tag.attrs:
            detail_url = BASE_URL.rstrip("/") + "/" + a_tag["href"].lstrip("/")
            exb["detail_url"] = detail_url

            # 詳細ページから料金取得
            try:
                detail_res = requests.get(detail_url)
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
    exhibitions = get_nact_exhibitions()
    if not exhibitions:
        print("現在会期中の展覧会はありません。")
    else:
        for idx, exb in enumerate(exhibitions, 1):
            print(f"\n◉ 展覧会 {idx}")
            print(f"　タイトル: {exb.get('title')}")
            print(f"　会期: {exb.get('date')}")
            print(f"　大人料金: {exb.get('adult_fee', '情報なし')}")
            print(f"　前売り大人料金: {exb.get('pre_sale_adult_fee', '情報なし')}")
            print(f"　詳細ページ: {exb.get('detail_url')}")
