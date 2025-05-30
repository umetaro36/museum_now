import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://www.momat.go.jp/exhibitions"

def get_momat_exhibitions():
    url = BASE_URL
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    exhibitions = []

    # 開催中の展覧会セクションを取得
    current_exhibitions = soup.select("section.item")
    
    for exb_item in current_exhibitions:
        # 開催中かどうかを確認
        status_tag = exb_item.find("span", class_="status")
        if not status_tag or "開催中" not in status_tag.get_text(strip=True):
            continue

        # 企画展かどうかを確認
        type_tag = exb_item.find("span", class_="type")
        if not type_tag or "企画展" not in type_tag.get_text(strip=True):
            continue

        exb = {}

        # タイトル
        title_tag = exb_item.find("h3", class_="title")
        if title_tag:
            exb["title"] = title_tag.get_text(strip=True)

        # 会期
        date_tag = exb_item.find("time", class_="date")
        if date_tag:
            exb["date"] = date_tag.get_text(strip=True)

        # 展覧会タイプ
        if type_tag:
            exb["type"] = type_tag.get_text(strip=True)

        # 詳細ページURL
        a_tag = exb_item.find("a")
        if a_tag and "href" in a_tag.attrs:
            detail_url = a_tag["href"]
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
    exhibitions = get_momat_exhibitions()
    if not exhibitions:
        print("現在会期中の企画展はありません。")
    else:
        for idx, exb in enumerate(exhibitions, 1):
            print(f"\n◉ 企画展 {idx}")
            print(f"　タイトル: {exb.get('title')}")
            print(f"　会期: {exb.get('date')}")
            print(f"　種類: {exb.get('type', '情報なし')}")
            print(f"　大人料金: {exb.get('adult_fee', '情報なし')}")
            print(f"　前売り大人料金: {exb.get('pre_sale_adult_fee', '情報なし')}")
            print(f"　詳細ページ: {exb.get('detail_url')}")
