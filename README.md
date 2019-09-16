# AdGraph
AdGraph is a novel graph-based machine learning approach for detecting advertising and tracking resources on the web. It differs from existing approaches by building a graph representation of the HTML structure, network requests, and JavaScript behavior of a webpage, and using this unique representation to train a classifier for identifying advertising and tracking resources. AdGraph's instruments Chromium web browser to capture fine grained details of a webpage rendering that involves interactions among and across all of the three layers of the web stack i.e. HTML, network, and JavaScript.

Since AdGraph captures fine grained details of a webpage rendering its application is not just limited to ad and tracker blocking and can be applied to a variety of other problems, we open source its instrumentation.

*AdGraph is tested on Ubuntu 16.04 (64-bit) and MacOS Mojave 10.14, but it should be compatible with other major Linux/MacOS distros and versions. Feel free to contact [Umar Iqbal](https://www.umariqbal.com) if you run into any problem running or building AdGraph.*

## Chromium Instrumentation
We instrument Chromium's rendering engine Blink and Chromium's JavaScript engine V8. To capture HTML and HTTP layers, we instrument Blink's core module. To capture JavaScript layer, we instrument V8 and Blink's bindings module.

### Instrumentation Details
To make our instrumentation portable to all Chromium based web browsers (e.g. Chrome, Edge, Brave) and to avoid disturbing the normal flow of execution, our design philosophy for Chromium instrumentation is to make minimal changes in the source code. We hook Chromium source code at points where we find all the necessary information to build connections among and across layers. To identify suitable hooks, we follow execution flows inside Chromium with debugging and Chromium's interactive repository. We then pass information from hooks to our own created data structures for further processing.

#### HTML Layer
To capture information at the HTML layer, we instrument Blink's core module. Specifically, we capture creation, insertion, modification, and removal of HTML nodes and their attributes in the DOM.

**Creation, Insertion, and Removal of Nodes** — We instrument constructors of `Blink::Element`, `Blink::Text`, and `Blink::DocumentFragment` in Blink to capture creation of nodes.Constructor of these objects are the earliest point to capture the node creation. Note that we are only able to capture node tag and node text at the time of node creation because its parent, siblings, and attributes are attached after its creation. We instrument `Blink::ContainerNode` to capture node insertion. We capture the insertion of all types of HTML nodes (e.g., Element, Text, Comment). We capture a node's parent, siblings, and attributes at time of node insertion. We similarly capture node removal in `Blink::ContainerNode`.

**Insertion, Modification, and Removal of Node Attributes** — We instrument `Blink::Element` to capture attribute manipulations by scripts. Parser inserted attributes are already captured in node insertion. We capture insertion, modification, and removal of node attributes by only scripts at this point. It is noteworthy that only Element node type have attributes.

**Insertion, Modification, and Removal of Inline Style Text** — Inline style text attribute manipulations follow a separate execution flow. We instrument `Blink::AbstractPropertySetCSSStyleDeclaration` to capture inline style text manipulations. We capture style text insertion, modification, and removal for nodes. It is noteworthy that only Element node type have inline style text.


#### JavaScript Layer
To capture information at the JavaScript layer, we instrument Blink's renderer bindings module and V8. We capture compilation of scripts, execution of scripts, execution of callbacks, and execution of dynamically created scripts with `Function()`, and `eval()`.

**Compilation and Execution of Scripts** — We instrument `Blink::ScriptController` to capture compilation and execution of scripts that happen sequentially. It is noteworthy that a script may compile and execute another script while it is being compiled and executed. Thus, we need to keep active scripts for each document in a stack. To this end, when we see a script's compilation, we push that script on top of the stack. We associate parsing events and HTTP requests with the script on the top of the stack. The mapping between a script element and its associated HTML element is needed for graph construction later. To get this mapping, we hook `Blink::PendingScript` which is executed right before the script is called. We register HTML element with the hash of script URL and script text in `Blink::PendingScript`. When we reach `Blink::ScriptController` and the script compiles, we link HTML element with the associated script.

**Execution of Script Callbacks (Macro & Micro Tasks)** — In addition to the execution of scripts, we also capture JavaScript callbacks. JavaScript has two type of callbacks: (1) macro tasks and (2) micro tasks. Micro tasks are a lightweight version of macro tasks and they are guaranteed to be executed before the execution of the next macro task. `setTimeout()` is an example of macro task and `promise.then()` is an example of micro task. We capture both macro and micro tasks in our instrumentation. While macro tasks can be captured in Blink's bindings module, capturing micro tasks is tricky as they are handled at a lower level in V8. Thus, we hook both Blink's bindings module and V8 to capture both macro and micro tasks. To this end, we register our hooks in `Blink::InitializeV8Common` to listen for callback execution. Our hooks are invoked whenever a callback is executed in `V8::ExternalCallbackScope`.

**Execution of eval() and Function()** — `eval()` and `Function()` provide a capability to generate script from a given string argument. We capture scripts created from these methods. `eval()` and `Function()` are called from other scripts, we keep this caller and callee association for graph construction. Similar to callbacks, we register listener hooks in `Blink::InitializeV8Common` to listen for creation of scripts with `eval()` and `Function()`. They are invoked whenever a script is created in `V8::Compiler`.
 

#### HTTP Layer
HTTP layer in AdGraph consists of HTTP nodes. We instrument Blink's renderer core module to capture HTTP layer. We capture HTTP requests to load scripts, `iframes`, style sheets, images, videos, and `XMLHTTP`. We capture HTTP requests before they are sent.

**HTTP requests for scripts, `Iframes`, and style sheets** — Requests for scripts, `Iframes`, and style sheets are sent when they are added to DOM. We insert our hooks at points, where these items are inserted. Specifically, we instrument `Blink::HTMLScriptElement`, `Blink::HTMLIFrameElement`, and `Blink::HTMLLinkElement` to capture requests to load scripts, `Iframes`, and style sheets, respectively. Each script, `Iframes`, and style sheets have an associated HTML element, we keep this mapping for graph construction. 

**HTTP requests for images and  videos** — Requests for images and videos are sent when the `src` attribute is assigned for these elements. We insert our hooks at the `src` assignment points. Specifically, to capture image request, we instrument `Blink::HTMLImageElement`. Whereas to capture video requests, we instrument `Blink::HTMLMediaElement` and `Blink::HTMLSourceElement`. It is important to note that the element is not attached to its parent when the `src` attribute is assigned. We hook `Blink::HTMLConstructionSite` to capture the parent information of an element. `Blink::HTMLConstructionSite` contains the information about the current element being parsed, we hook it to capture the parent of element.


**HTTP requests for `XMLHTTP`** — `XMLHTTP` requests are sent from JavaScript to interact with servers without refreshing the whole webpage. We capture these requests in our instrumentation when they are to be sent. Specifically, we instrument `Blink::XMLHttpRequest` to capture `XMLHTTP` requests.


### Rendering Stream Representation
We capture rendering events as they happen, they can be seen as a stream of events. We call the sequence of rendering events `rendering stream`. We keep an in-memory representation of `rendering stream` with our well defined data structures. Since we need to utilize `rendering stream` to build AdGraph, we record associations of events and link them together. We also record additional details about events that we later use for analysis on AdGraph. It is important to note that for low memory and performance footprint we optimize our representation and do not duplicate details.

For HTML layer nodes, we record their id, type, tag name, text, parents, siblings, and attributes. For JavaScript layers nodes, we record their id, associated HTML node id, URL, and text. For HTTP layer nodes, we record the request URL and associated HTML node id. For HTML and HTTP layer, we record active script id as well. We represent `rendering stream` for each Document separately. It allows us to build graph separately for each Document and do our analysis. We also provide a capability to export `rendering stream` in JSON format to enable offline analysis.

## Repository Structure

1. Binaries [`release`](https://github.com/uiowa-irl/AdGraph/releases)  
```
── AdGraph-Ubuntu-16.04.zip (built on Ubuntu 16.04)
── AdGraph-OSX-10.14.zip (built on MacOS Mojave 10.14)
```
2. Source Code  
```
├── LICENSE
├── README.md
├── patches
    ├── patch.diff
    └── v8_patch.diff
├── scripts
    └── example_crawler.py
```
We provide both the binaries (**download them from GitHub's [`release`](https://github.com/uiowa-irl/AdGraph/releases)**) and source code (as a patch to Chromium version 69.0.3441.0) to allow for reproducibility and future extensions from research community.

## Run Prebuilt Binary
Binaries are located in the **`release`** folder. Please follow the steps below to run them.

1. Unzip the folder `AdGraph-Ubuntu-16.04.zip/AdGraph-OSX-10.14.zip` and simply run `chrome` with `--no-sandbox` flag from command line  
```
# Ubuntu
./chrome --no-sandbox 
# MacOS 
./Chromium.app/Contents/MacOS/Chromium --no-sandbox
```
2. To extract fine grained rendering details, create a `CDATASection` element with text `NOTVERYUNIQUESTRING`. Execute the following script in Chromium's dev tools console. The resultant rendering stream will be stored in `{HOME_DIRECTORY}/rendering_stream` directory.
```
document.createCDATASection('NOTVERYUNIQUESTRING');
```
3. To extract/crawl a large number of websites, a sample Selenium based crawling script is added in the `scripts` folder

## Build From Scratch
We provide source code as a patch to Blink and V8 modules in Chromium. Please follow these steps to build AdGraph from scratch.
1. Check out Chromium source from [this repo](https://www.chromium.org/developers/how-tos/get-the-code) and follow all the steps before setting up the build [Copied from Chromium].

    Install depot_tools
    ```
    git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
    ```
    Add depot_tools to the end of your PATH (you will probably want to put this in your ~/.bashrc or ~/.zshrc). Assuming you cloned depot_tools to /path/to/depot_tools:
    ```
    export PATH="$PATH:/path/to/depot_tools"
    ```
    OR, when cloning depot_tools to your home directory do not use ~ on PATH, otherwise gclient runhooks will fail to run. Rather, you should use either $HOME or the absolute path:
    ```
    $ export PATH="$PATH:${HOME}/depot_tools"
    ```
    Get the code, create a chromium directory for the checkout and change to it (you can call this whatever you like and put it wherever you like, as long as the full path has no spaces): 
    ```
    mkdir ~/chromium && cd ~/chromium
    ```
    Run the fetch tool from depot_tools to check out the code and its dependencies.
    ```
    fetch --nohooks chromium
    ```
    The remaining instructions assume you have switched to the src directory:
    ```
    cd src
    ```
    Install additional build dependencies, once you have checked out the code, and assuming you're using Ubuntu, run build/install-build-deps.sh
    ```
    $ ./build/install-build-deps.sh
    ```  
    Run the hooks, once you've run install-build-deps at least once, you can now run the Chromium-specific hooks, which will download additional binaries and other things you might need:
    ```
    $ gclient runhooks
    ```

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

4. Setup the build with `gn` command    
```
# setup with is_debug and use_jumbo_build flags
gn gen out/AdGraph-[Ubuntu|MacOS] "--args=is_debug=false use_jumbo_build=true"
```

5. Build AdGraph with `ninja`, the resulting binary will be generated in `out/AdGraph-[Ubuntu|MacOS]`
```
autoninja -C out/AdGraph-[Ubuntu|MacOS]
```

6. Simply run the compiled AdGraph binary with `--no-sandbox` flag  
```
# Ubuntu
./chrome --no-sandbox
# MacOS
./Chromium.app/Contents/MacOS/Chromium --no-sandbox
```

## Reference

**AdGraph: A Graph-Based Approach to Ad and Tracker Blocking**  
Umar Iqbal, Peter Snyder, Shitong Zhu, Benjamin Livshits, Zhiyun Qian, and Zubair Shafiq  
*IEEE Symposium on Security & Privacy (S&P), 2020*

**Abstract** — User demand for blocking advertising and tracking online is large and growing. Existing tools, both deployed and described in research, have proven useful, but lack either the completeness or robustness needed for a general solution. Existing detection approaches generally focus on only one aspect of advertising or tracking (e.g. URL patterns, code structure), making existing approaches susceptible to evasion.

In this work we present AdGraph, a novel graph-based machine learning approach for detecting advertising and tracking resources on the web. AdGraph differs from existing approaches by building a graph representation of the HTML structure, network requests, and JavaScript behavior of a webpage, and using this unique representation to train a classifier for identifying advertising and tracking resources. Because AdGraph considers many aspects of the context a network request takes place in, it is less susceptible to the single-factor evasion techniques that flummox existing approaches.

We evaluate AdGraph on the Alexa top-10K websites, and find that it is highly accurate, able to replicate the labels of human-generated filter lists with 95.33% accuracy, and can even identify many mistakes in filter lists. We implement AdGraph as a modification to Chromium. AdGraph adds only minor overhead to page loading and execution, and is actually faster than stock Chromium on 42% of websites and AdBlock Plus on 78% of websites. Overall, we conclude that AdGraph is both accurate enough and performant enough for online use, breaking comparable or fewer websites than popular filter list based approaches.

**For more details please check our [full paper](https://umariqbal.com/papers/adgraph-sp2020.pdf)**
