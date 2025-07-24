const parser = require('@babel/parser');
const traverse = require('@babel/traverse').default;
const axios = require('axios');
const jsdom = require("jsdom");
const { JSDOM } = jsdom;
const fs = require("node:fs");
const wasm_hook = require("./dch-hook");

async function fetchHsw(version) {
    try {
        const inst = axios.create({
            timeout: 1000,
        });
        const resp = await inst.get("https://newassets.hcaptcha.com/c/" + version + "/hsw.js");
        return resp.data;
    } catch (error) {
        console.error('Error fetching hsw:', error);
        throw error;
    }
}

function findWasm(ast) {
    let wasm = "";
    traverse(ast, {
        StringLiteral(path) {
            if (path.node.value.length > 100000) {
                wasm = path.node.value;
            }
        }
    });
    return wasm;
}

async function hook(hswVersion) {
    const hswScript = await fetchHsw(hswVersion);
    const AST = parser.parse(hswScript, {});
    const wasm = findWasm(AST);
    const hookedWasm = wasm_hook.hookWasm(wasm);
    return {
        script: hswScript,
        wasm: hookedWasm,
    };
}

async function parse(scriptData) {
    const dom = new JSDOM(`<!DOCTYPE html><html lang="en"><body></body></html>`, { runScripts: "dangerously" });

    let output = fs.readFileSync("key_fetcher/hook.js").toString();
    output = output.replaceAll("{HCAPTCHA_HSW_WASM}", scriptData.wasm);
    output += scriptData.script + ";";
    output += "callHsw().then(x => x)";

    return dom.window.eval(output);
}

async function fetchKeys(hswVersion) {
    try {
        const scriptData = await hook(hswVersion);
        const array = await parse(scriptData);

        const keys = array[0];
        const fingerprintKey = Buffer.from(keys[0]).toString("base64");
        const payloadKey = Buffer.from(keys[keys.length - 2]).toString("base64");
        const responseKey = Buffer.from(keys[2]).toString("base64");

        return {
            keys: [fingerprintKey, payloadKey, responseKey]
        };
    } catch (error) {
        console.error("Error fetching keys:", error);
        throw error;
    }
}

const args = process.argv.slice(2);
const hswVersion = args[0];

fetchKeys(hswVersion).then(result => {
    console.log(JSON.stringify(result));
}).catch(err => {
    console.error("Error:", err);
});
