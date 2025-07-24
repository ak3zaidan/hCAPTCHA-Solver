let __wasmMemory = null;
let __likelyDecryptMemFunctions = [];
let __hCaptcha_keys = [];

function readUInt32LE(buffer) {
    return new DataView(buffer.buffer).getUint32(0, true);
}

function memSlice(from, to) {
    if (to - from <= 0) {
        throw "Slice length is lower or equal than 0";
    }

    const buffer = new Uint8Array(to - from);
    for (let i = 0; i < buffer.length; i++) {
        buffer[i] = __likelyDecryptMemFunctions[0](from + i);
    }

    return buffer;
}

function fetchKeys(pos) {
    const key = memSlice(pos, pos+32);
    __hCaptcha_keys.push(Array.from(key));
}

function hookWebAssembly() {
    const origWasmCompile = WebAssembly.compile;
    WebAssembly.compile = function(source) {
        // Hook WASM buffer here
        // console.log(uint8ArrayToBase64(source))

        const base64String = "{HCAPTCHA_HSW_WASM}";
        const binaryString = atob(base64String);
        const buffer = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
            buffer[i] = binaryString.charCodeAt(i);
        }

        return origWasmCompile(buffer);
    }

    const origWasmInstantiate = WebAssembly.instantiate;
    WebAssembly.instantiate = function(source, imports) {
        imports["hook"] = {
            __keyScheduleCallback: fetchKeys,
        };

        const instancePromise = origWasmInstantiate(source, imports);

        instancePromise.then(module => {
            const values = Object.values(module.exports);

            for (let i = 0; i < values.length; i++) {
                const value = values[i];

                if (value.toString() === "[object WebAssembly.Memory]") {
                    __wasmMemory = value;
                    break;
                }
            }

            for (let i = 0; i < values.length; i++) {
                const value = values[i];
                if (!value.toString().startsWith("function ")) {
                    continue;
                }

                const argsLength = value.length;
                if (argsLength !== 2) {
                    continue
                }

                try {
                    // no comment on this
                    let res = value(1048576);
                    if (res === 65) {
                        __likelyDecryptMemFunctions.push(value);
                    }
                } catch(exception) {}
            }
        })

        return instancePromise
    }
}

async function callHsw() {
    try {
        await hsw("eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmIjowLCJzIjoyLCJ0IjoidyIsImQiOiJ6M2M4SUNkczZQMjE2bmw5RVJXWndvTHQyWE5RdWdVN2hZUVRYNW9yeDYvTjlrMHhvaXZGeHdyQkV5RW45UTVnMHRyYWhMbVZad2VScVRSR09nblMzRXdoVlc1VnpjT0o5WW5MT3RMRGFwSksxV0NldnV5Mm9LdjUwV2lmc0ErZlpQN3lpaWhmVHl2MFgyYmRiQlFuRWRkdmxFRHU5WDQyMndmOEhsaWFpc3NWYytFRGZ0SWZKODRJM1RrRExkTUg5eCtmb3ZKRVpvUTBTdFRoQU0weDQwakI4aExVcmFLUElPa2JJUUNSK2JZTnMyNkRGSFhJNVJBL3NJbXlqL3c9ZUEzemZaTlZCYkpXdzdSZSIsImwiOiIvYy83YjZlMTdjMDRjNmQ3OTdiZmFjNWRjNTM4MjY4ODk3MGUzNzU5ZGEzNjI5YTUyZjlhNDMxN2JmNzFhZjExZTNhIiwiaSI6InNoYTI1Ni1kQlE5SjRpMTMxVnVvZUo0OTYwWjZqRERyV3MrRU85YWZ2YW0vdTAvYjdJPSIsImUiOjE3MzQxMjA3MjcsIm4iOiJoc3ciLCJjIjoxMDAwfQ.QdL13LZrlxUdSIev5LADKRREIzrLnwCrF78EhZNO9-Y")
    } catch {}
    try {
        await hsw(0, new Uint8Array(1024));
    } catch {}
    try{
        await hsw(1, new Uint8Array(1024));
    } catch {}

    return [__hCaptcha_keys]
}

hookWebAssembly();
