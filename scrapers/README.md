
# lfwc_scraper
This subfolder archives all scrapers used to obtain the raw samples from all 10 vendors included in lfwc:

1.  [ASUS](https://www.asus.com)
2.  [AVM](https://avm.de)
3.  [D-Link](https://www.dlink.com/)
4.  [EDIMAX](https://www.edimax.com/edimax/global/)
5.  [ENGENIUS](https://www.engeniustech.com)
6.  [Linksys](https://www.linksys.com/)
7.  [NETGEAR](https://netgear.com)
8.  [TP-Link](https://www.tp-link.com/)
9.  [TRENDnet](https://www.trendnet.com)
10. [Ubiquiti](https://www.ui.com)

## Note

The scrapers in this directory are for archival purposes and their use is discouraged.
They are no appropriate tool to replicate LFWC because website layouts change and sample availability fluctuates over time.
Thus, it is likely that various scrapers in this project do not work anymore.

To replicate the corpus, please refer to the autodownloader tools that work in conjunction with the `.csv` metadata we distribute.
They use the official direct download links and fall back to archive.org when the original source longer exists. Thanks!

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

For more information about scrapy, [see here.](https://docs.scrapy.org/en/latest/intro/install.html#intro-install)

## Use

```bash
scrapy crawl <scraper_name> -o <output.json>
```

## Available Scrapers

```plain
archive_avm
archive_linksys
asus
avm
edimax
engenius
linksys
netgear
tplink
trendnet
ubiquiti
```
