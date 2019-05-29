# AdGraph
**Abstract** — User demand for blocking advertising and tracking online is large and growing. Existing tools, both deployed and described in research, have proven useful, but lack either the completeness or robustness needed for a general solution. Existing detection approaches generally focus on only one aspect of advertising or tracking (e.g. URL patterns, code structure), making existing approaches susceptible to evasion.

In this work we present AdGraph, a novel graph-based machine learning approach for detecting advertising and tracking resources on the web. AdGraph differs from existing approaches by building a graph representation of the HTML structure, network requests, and JavaScript behavior of a webpage, and using this unique representation to train a classifier for identifying advertising and tracking resources. Because AdGraph considers many aspects of the context a network request takes place in, it is less susceptible to the single-factor evasion techniques that flummox existing approaches.

We evaluate AdGraph on the Alexa top-10K websites, and find that it is highly accurate, able to replicate the labels of human-generated filter lists with 95.33% accuracy, and can even identify many mistakes in filter lists. We implement AdGraph as a modification to Chromium. AdGraph adds only minor overhead to page loading and execution, and is actually faster than stock Chromium on 42% of websites and AdBlock Plus on 78% of websites. Overall, we conclude that AdGraph is both accurate enough and performant enough for online use, breaking comparable or fewer websites than popular filter list based approaches.

**Please check our full paper for more details**

## Instrumentation Details

## Repository Structure

1. Binaries (from [`release` tab](https://github.com/uiowa-irl/AdGraph/releases), currently versioned `AdGraph-v1.0`)
```
── AdGraph-Linux.tar.gz (modified Chromium binary for Linux)
```
2. Source Code
```
├── LICENSE
├── README.md
├── patches
│   ├── patch.diff
│   └── v8_patch.diff
├── scripts
    └── example_selenium_script.py
```
We provide both the binaries (**download them from GitHub's [`release` tab](https://github.com/uiowa-irl/AdGraph/releases)**) and source code (as Chromium patches) to allow for reproducibility and future extensions from research commiunity.

## Run Prebuilt Binary
Binaries are located in the **`release`** folder. Please follow the steps below to run them.

1. Unzip the folder `AdGraph-Linux.tar.gz` and simple run `chrome` with `--nosandbox` flag from command line 
```
.\chrome --nosandbox
```
2. To extract fine grained rendering details create a `CDATASection` element with text `NOTVERYUNIQUESTRING`
```
document.createCDATASection('NOTVERYUNIQUESTRING');
```
3. To extract/crawl a large number of webistes, a sample script is added in the `sacripts` folder

## Build From Scratch
Our source code is provided as Chromium patches. Follow these steps to apply and integrate them into stock Chromium.
1. Check out Chromium source from [this tutorial](https://www.chromium.org/developers/how-tos/get-the-code) and follow all the steps before setting up the build.
2. To apply patch for Blink checkout commit `c916c273b71b`  
```
git reset --hard c916c273b71b
git clean -fd
git apply /PATH/TO/patches/patch.diff
gclient sync
``` 
3. To apply patch for V8 checkout commit `44d7d7d6b1`
```
cd v8
git reset --hard 44d7d7d6b1
git clean -fd
git apply /PATH/TO/patches/v8_patch.diff
gclient sync
``` 
4. Set build parameters as below (by `gn args /PATH/TO/CHROMIUM/BUILD`):
```
# You may adjust this as needed, but 
# "use_jumbo_build = true" is required 
# as per our namespace usage
is_debug = false
```
5. `autoninja -C out/AdGraph-[Linux|OSX]` and you will get the resulting binary in `out/AdGraph-[Linux|OSX]`

## Reference
Check our IEEE S&P '20 paper for more architectural and technical details 

**AdGraph: A Graph-Based Approach to Ad and Tracker Blocking**
Umar Iqbal, Peter Snyder, Shitong Zhu, Benjamin Livshits, Zhiyun Qian, and Zubair Shafiq
*IEEE Symposium on Security & Privacy (S&P), 2020*
