# NHentai API
A python script that collects data from NHentai.net. 

**Goals**
```
>Collect data from NHentai
>Automatically save the metadata(tags)
>Download pages concurrently
>API Template (For possible other websites to support)
```

**Libraries used**
```
>bs4 
>Httpx
>Anyio (Trio Backend)
>Trio
>pyyaml
>undetected-chromedriver 
```
**Repositories:**


>[Ungoogled chromedriver](https://github.com/ultrafunkamsterdam/undetected-chromedriver)


**Supported Sites at the moment**
```
• NHentai [Mirror sites: .to])
```

**Note:**
Mirror download is enabled by default incase the official site is not available, if you prefer
to disable this. Please set "mirror_available" to `false` in config.json