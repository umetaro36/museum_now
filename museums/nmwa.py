import requests
from bs4 import BeautifulSoup
import re

def get_all_nmwa_special_exhibitions():
    url = "https://www.nmwa.go.jp/jp/exhibitions/current.html"
    base_url = "https://www.nmwa.go.jp"
    res = requests.get(url)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")

    special_section = soup.find("section", id="exhibitions")
    if not special_section:
        return []

    exhibitions = []
    exb_infos = special_section.find_all("section", class_="exb_info")

    for exb_info in exb_infos:
        result = {}

        # タイトル
        title_tag = exb_info.find("h3")
        if title_tag:
            result["title"] = title_tag.get_text(strip=True)

        # 会期
        date_dt = exb_info.find("dt", class_="calendar")
        if date_dt:
            date_dd = date_dt.find_next_sibling("dd")
            if date_dd:
                result["date"] = date_dd.get_text(strip=True)

        # 詳細ページリンク
        detail_link_tag = exb_info.find("a", href=True)
        if detail_link_tag:
            detail_url = base_url + detail_link_tag["href"]
            result["detail_url"] = detail_url

            # 詳細ページにアクセスし料金を取得
            try:
                detail_res = requests.get(detail_url)
                detail_res.encoding = detail_res.apparent_encoding
                detail_soup = BeautifulSoup(detail_res.text, "html.parser")

                fee_candidates = detail_soup.find_all(stringre.compile(r"(観覧料|料金|入場料|前売)"))
                for candidate in fee_candidates:
                    parent = candidate.find_parent(["p", "div", "section", "li", "td"])
                    if parent:
                        fee_text_all = parent.get_text(strip=True)

                        # 通常料金（一般 or 大人）
                        normal_match = re.search(r"(一般|大人)[^\d]{0,5}([\d,]+)円", fee_text_all)
                        if normal_match:
                            result["adult_fee"] = normal_match.group(2).replace(",", "") + "円"

                        # 前売り料金（キーワードに前売を含む場合のみ）
                        pre_match = re.search(r"(前売[^\d]{0,5})(一般|大人)?[^\d]{0,5}([\d,]+)円", fee_text_all)
                        if pre_match:
                            result["pre_sale_adult_fee"] = pre_match.group(3).replace(",", "") + "円"

                        # 両方見つかったら打ち切り
                        if "adult_fee" in result and "pre_sale_adult_fee" in result:
                            break

            except Exception as e:
                result["adult_fee"] = "取得エラー"

        exhibitions.append(result)

    return exhibitions

if __name__ == "__main__":
    exhibitions = get_all_nmwa_special_exhibitions()
    if not exhibitions:
        print("現在会期中の展覧会はありません。")
    else:
        for idx, exb in enumerate(exhibitions, start=1):
            print(f"\n◉ 企画展 {idx}")
            print(f"　タイトル: {exb.get('title')}")
            print(f"　会期: {exb.get('date')}")
            print(f"　大人料金: {exb.get('adult_fee', '情報なし')}")
            print(f"　前売り大人料金: {exb.get('pre_sale_adult_fee', '情報なし')}")
            print(f"　詳細ページ: {exb.get('detail_url')}")
