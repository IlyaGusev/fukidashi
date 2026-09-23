# 質疑応答の準備（Team FUKIDASHI）

5分の本編に入らない材料をまとめた。元のスライド `slides.pdf`（小説中心の古い計画書）のうち、今も使える話を、新計画書 `refined_plan.md`（日本語→英語のマンガ）の数字とコードの事実に合わせて書き直した。

- 答えは英語。そのまま口に出せる長さにしてある
- 数字はすべて計画上の仮定。実績ではない
- 予備スライド（デッキの締めのあと）: 競合、12週間の計画、90日の予算、リスク

---

## 1. ビジネス

### Q. Why won't big publishers just do this themselves?
They could, and they hold the major series. We go after the titles they have not licensed: creator-owned work, small-publisher series and backlist with a named English audience. For those, a full traditional localization budget does not pay back; a cheaper, reviewed workflow might.
<!-- 出典: 新計画書 2.2、5.1。予備スライド「competition」 -->

### Q. How do you make money?
We license a volume, produce the English edition once and sell it direct to readers. In our plan a 200-page volume costs about €1,500 with human review and lettering. At €7.99, after a 50% royalty to the rights holder, payment fees, refunds and €1.50 of acquisition, about €1.90 is left per order, so a volume pays back after about 790 orders.
<!-- 出典: 新計画書 10.2〜10.3。元スライド p.15 の小説版をマンガ版に置き換えたもの -->

### Q. What moves the numbers most?
Acquisition cost, much more than price. At €0.50 of acquisition per order a volume pays back after 518 orders; at €3.00 it needs 3,748. Paid ads at €5 per new reader leave about €0.64 per reader even if they buy 1.7 volumes, so readers have to come through creators, communities and the next volume of a series.
<!-- 出典: 新計画書 10.4、10.5。元スライド p.16「Acquisition cost moves the answer more than price does」のマンガ版 -->

感度分析（新計画書 10.4。回収に必要な注文数、制作費 €1,500）:

| 条件 | 1件あたりの残り | 回収に必要な注文数 |
|---|---:|---:|
| €7.99、獲得コストなし | €3.40 | 442 |
| €7.99、獲得コスト €0.50 | €2.90 | 518 |
| €7.99、獲得コスト €1.50（基本） | €1.90 | 790 |
| €7.99、獲得コスト €3.00 | €0.40 | 3,748 |
| €5.99、獲得コストなし | €2.46 | 611 |
| €9.99、獲得コストなし | €4.35 | 346 |
| 権利者の取り分 60%、獲得コストなし | €2.67 | 562 |
| EU の読者（VAT 9%）、獲得コスト €1.50 | €1.58 | 950 |
| 手間のかかる巻（€3,000）、獲得コスト €1.50 | €1.90 | 1,579 |

### Q. How big is the market?
We have not sourced a size for the English digital manga market, so we don't quote one. What we know is that readers already pay for licensed manga sold direct: J-Novel Club sells most volumes at US$8.99. Sourcing that number is the first item on our plan.
<!-- 出典: 新計画書 2.3、18。数字をでっち上げない -->

### Q. What exactly does the reader buy?
One complete, authorized, stable volume, not an on-demand translation. They read a free sample in the browser, see the price, the credits and how AI and people were involved, buy, and read. No upload, no credits, no subscription. The next thing we offer is volume two.
<!-- 元スライド p.4「What we sell」、p.5「The reader journey」のマンガ版。新計画書 4.1〜4.5 -->

### Q. Why English first? What about other languages?
English is one market with one team and one set of rights to secure, and we can check quality ourselves. German, French, Spanish and others come later, each only when it has its own rights, editors, readers and economics.
<!-- 2-1 の 7 の決定。新計画書 14.3 -->

### Q. What will you do with funding? / What's next?
The first 90 days are planned at €49,000: two volumes, an end-to-end pilot with a real letterer, legal and tax advice including Japanese title advice, reader research, the storefront and acquisition tests. Volume two is only committed after volume one shows evidence.
<!-- 予備スライド「budget」。新計画書 11.2、11.3 -->

---

## 2. プロダクトと技術

### Q. Why GLM-5.3-Flash and not the best model?
Kimi-K3 draws the best boxes, but it costs about 20 times more. GLM-5.3-Flash is the cheapest model in our benchmark whose boxes are usable for overlays. The app can switch to Kimi-K3 for hard pages without a code change.
<!-- README「Vision model benchmark」 -->

### Q. Did you compare against GPT or Claude?
No. Our baseline is the other open vision models on Token Factory, including a smaller one. A closed-model comparison is a fair next step.
<!-- 正直に答える。閉じたモデルはテストしていない -->

### Q. How do you keep names and voices consistent across a volume?
Today each page gets the previous page's text as context. The plan is a source-linked story bible for the whole volume: characters, how they address each other, recurring jokes, terminology, with each choice approved by the editor. A later volume reuses it through an explicit import, and a change creates a list of affected lines instead of silently rewriting them.
<!-- 元スライド p.10「Whole-work and series memory」。新計画書 6.3。**今あるのは「前のページ」だけ**。巻全体の記憶は未実装なので「plan」と言う -->

### Q. What happens between a translated file and a sale?
A release gate. A volume is only sold when the rights cover it, every text region has an approved translation, the letterer has done a round trip, the reader works on real devices, and price, tax and delivery are checked. A successful model run authorizes nothing.
<!-- 元スライド p.13「A finished file is not a released product」、p.12。新計画書 8.2、7.6。**未実装の設計**なので「will」で話す -->

### Q. What is not built yet?
Speaker attribution, lettering into the bubbles, overflow checks, whole-volume memory, the reader and the store. What works today is detection, transcription and translation for pages and whole volumes, with a job queue that retries and resumes.
<!-- 言えないことを先に自分から言うと、信頼される -->

### Q. What if the model gets it wrong?
Everything it returns is shown on the page next to the Japanese, so an editor can spot a wrong box or line and re-run the page with another model. Nothing is published without a bilingual editor and a letterer signing off.

---

## 3. 権利と責任

### Q. Is the demo manga licensed?
The demo uses the OpenMantra research dataset, published under CC BY-NC 4.0 for non-commercial use with attribution. The product itself would only sell volumes licensed from their rights holders.
<!-- 2-1 の 6。表示: Hinami et al., AAAI 2021 -->

### Q. Who owns the translation?
The rights holder keeps the original. The license defines what we may publish. Protection for AI-assisted text depends on the human contribution, so we don't claim that "human edited" means "fully copyrighted".
<!-- 新計画書 12.6 -->

### Q. What data do you keep?
No accounts and no personal data today. Uploaded pages and results are cached on our server so we don't call the model twice. A store would add customer data, which needs its own privacy setup.
<!-- store.py。「保存しない」とは言わない -->

### Q. What about prompt injection from text in the page?
The model has no tools or write access; it can only return JSON, which we show on the page. The worst case is a wrong result that the editor sees.
<!-- 「対策している」とは言わない。index.html 238行目の kind のエスケープを直すまで「全部エスケープしている」とも言わない -->

---

## 4. 元のスライドから取り入れなかったもの

| 元のスライド | 理由 |
|---|---|
| p.3 ドイツの電子書籍市場（37.2M など） | マンガにも英語圏にも当てはまらない |
| p.7 最初のリリース（DOCX、12万語） | 小説用 |
| p.11 データモデル | 5分の発表には細かすぎる。未実装 |
| p.12 「Six rules the code enforces」 | コードにまだ無い。質疑では「リリースゲート」の答えに設計として入れた |
| p.14 小説の品質目標（編集工数 30〜50% 減） | 実測のベンチマークに置き換えた |
| p.15〜16 小説の収支 | マンガの収支に置き換えた（上の表） |
